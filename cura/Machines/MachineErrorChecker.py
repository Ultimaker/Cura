# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import time

from collections import deque

from PyQt6.QtCore import QObject, QTimer, pyqtSignal, pyqtProperty
from typing import Optional, Any, Set

from UM.Logger import Logger
from UM.Settings.SettingDefinition import SettingDefinition
from UM.Settings.Validator import ValidatorState

import cura.CuraApplication


class MachineErrorChecker(QObject):
    """This class performs setting error checks for the currently active machine.

    The whole error checking process is pretty heavy which can take ~0.5 secs, so it can cause GUI to lag. The idea
    here is to split the whole error check into small tasks, each of which only checks a single setting key in a
    stack. According to my profiling results, the maximal runtime for such a sub-task is <0.03 secs, which should be
    good enough. Moreover, if any changes happened to the machine, we can cancel the check in progress without wait
    for it to finish the complete work.
    """

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self._global_stack = None

        self._has_errors = True  # Result of the error check, indicating whether there are errors in the stack
        self._error_keys = set()  # type: Set[str] # A set of settings keys that have errors
        self._error_keys_in_progress = set()  # type: Set[str]  # The variable that stores the results of the currently in progress check

        self._stacks_and_keys_to_check = None  # type: Optional[deque]  # a FIFO queue of tuples (stack, key) to check for errors

        self._need_to_check = False  # Whether we need to schedule a new check or not. This flag is set when a new
                                     # error check needs to take place while there is already one running at the moment.
        self._check_in_progress = False  # Whether there is an error check running in progress at the moment.

        self._application = cura.CuraApplication.CuraApplication.getInstance()
        self._machine_manager = self._application.getMachineManager()

        self._check_start_time = time.time()

        self._setCheckTimer()

        self._keys_to_check = set()  # type: Set[str]

        self._num_keys_to_check_per_update = 1

    def initialize(self) -> None:
        self._error_check_timer.timeout.connect(self._rescheduleCheck)

        # Reconnect all signals when the active machine gets changed.
        self._machine_manager.globalContainerChanged.connect(self._onMachineChanged)

        # Whenever the machine settings get changed, we schedule an error check.
        self._machine_manager.globalContainerChanged.connect(self.startErrorCheck)

        self._onMachineChanged()
        self.startErrorCheck()

    def _setCheckTimer(self) -> None:
        """A QTimer to regulate error check frequency

        This timer delays the starting of error check
        so we can react less frequently if the user is frequently
        changing settings.
        """

        self._error_check_timer = QTimer(self)
        self._error_check_timer.setInterval(100)
        self._error_check_timer.setSingleShot(True)

    def _onMachineChanged(self) -> None:
        if self._global_stack:
            self._global_stack.propertyChanged.disconnect(self.startErrorCheckPropertyChanged)
            self._global_stack.containersChanged.disconnect(self.startErrorCheck)

            for extruder in self._global_stack.extruderList:
                extruder.propertyChanged.disconnect(self.startErrorCheckPropertyChanged)
                extruder.containersChanged.disconnect(self.startErrorCheck)

        self._global_stack = self._machine_manager.activeMachine

        if self._global_stack:
            self._global_stack.propertyChanged.connect(self.startErrorCheckPropertyChanged)
            self._global_stack.containersChanged.connect(self.startErrorCheck)

            for extruder in self._global_stack.extruderList:
                extruder.propertyChanged.connect(self.startErrorCheckPropertyChanged)
                extruder.containersChanged.connect(self.startErrorCheck)

    hasErrorUpdated = pyqtSignal()
    needToWaitForResultChanged = pyqtSignal()
    errorCheckFinished = pyqtSignal()

    @pyqtProperty(bool, notify = hasErrorUpdated)
    def hasError(self) -> bool:
        return self._has_errors

    @pyqtProperty(bool, notify = needToWaitForResultChanged)
    def needToWaitForResult(self) -> bool:
        return self._need_to_check or self._check_in_progress

    def startErrorCheckPropertyChanged(self, key: str, property_name: str) -> None:
        """Start the error check for property changed
        this is separate from the startErrorCheck because it ignores a number property types

        :param key:
        :param property_name:
        """

        if property_name != "value":
            return
        self._keys_to_check.add(key)
        self.startErrorCheck()

    def startErrorCheck(self, *args: Any) -> None:
        """Starts the error check timer to schedule a new error check.

        :param args:
        """

        if not self._check_in_progress:
            self._need_to_check = True
            self.needToWaitForResultChanged.emit()
        self._error_check_timer.start()

    def _rescheduleCheck(self) -> None:
        """This function is called by the timer to reschedule a new error check.

        If there is no check in progress, it will start a new one. If there is any, it sets the "_need_to_check" flag
        to notify the current check to stop and start a new one.
        """

        if self._check_in_progress and not self._need_to_check:
            self._need_to_check = True
            self.needToWaitForResultChanged.emit()
            return

        self._error_keys_in_progress = set()
        self._need_to_check = False
        self.needToWaitForResultChanged.emit()

        global_stack = self._machine_manager.activeMachine
        if global_stack is None:
            Logger.log("i", "No active machine, nothing to check.")
            return

        # Populate the (stack, key) tuples to check
        self._stacks_and_keys_to_check = deque()
        for stack in global_stack.extruderList:
            if not self._keys_to_check:
                self._keys_to_check = stack.getAllKeys()

            for key in self._keys_to_check:
                self._stacks_and_keys_to_check.append((stack, key))

        self._application.callLater(self._checkStack)
        self._check_start_time = time.time()
        Logger.log("d", "New error check scheduled.")

    def _checkStack(self) -> None:
        if self._need_to_check:
            Logger.log("d", "Need to check for errors again. Discard the current progress and reschedule a check.")
            self._check_in_progress = False
            self._application.callLater(self.startErrorCheck)
            return

        self._check_in_progress = True

        for i in range(self._num_keys_to_check_per_update):
            # If there is nothing to check any more, it means there is no error.
            if not self._stacks_and_keys_to_check:
                # Finish
                self._setResult(False)
                return

            # Get the next stack and key to check
            stack, key = self._stacks_and_keys_to_check.popleft()

            enabled = stack.getProperty(key, "enabled")
            if not enabled:
                continue

            validation_state = stack.getProperty(key, "validationState")
            if validation_state is None:
                # Setting is not validated. This can happen if there is only a setting definition.
                # We do need to validate it, because a setting definitions value can be set by a function, which could
                # be an invalid setting.
                definition = stack.getSettingDefinition(key)
                validator_type = SettingDefinition.getValidatorForType(definition.type)
                if validator_type:
                    validator = validator_type(key)
                    validation_state = validator(stack)
            if validation_state in (ValidatorState.Exception, ValidatorState.MaximumError, ValidatorState.MinimumError, ValidatorState.Invalid):
                # Since we don't know if any of the settings we didn't check is has an error value, store the list for the
                # next check.
                keys_to_recheck = {setting_key for stack, setting_key in self._stacks_and_keys_to_check}
                keys_to_recheck.add(key)
                self._setResult(True, keys_to_recheck = keys_to_recheck)
                return

        # Schedule the check for the next key
        self._application.callLater(self._checkStack)

    def _setResult(self, result: bool, keys_to_recheck = None) -> None:
        if result != self._has_errors:
            self._has_errors = result
            self.hasErrorUpdated.emit()
            self._machine_manager.stacksValidationChanged.emit()
        self._keys_to_check = keys_to_recheck if keys_to_recheck else set()
        self._need_to_check = False
        self._check_in_progress = False
        self.needToWaitForResultChanged.emit()
        self.errorCheckFinished.emit()
        execution_time = time.time() - self._check_start_time
        Logger.info(f"Error check finished, result = {result}, time = {execution_time:.2f}s")
