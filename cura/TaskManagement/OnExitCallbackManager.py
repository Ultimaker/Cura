# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING, Callable, List

from UM.Logger import Logger

if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication


#
# This class manages all registered upon-exit checks
# that need to be performed when the application tries to exit.
# For example, show a confirmation dialog when there is USB printing in progress.
# All callbacks will be called in the order of when they were registered.
# If all callbacks "pass", for example:
# if the user clicks "yes" on the exit confirmation dialog
# and nothing else is blocking the exit, then the application will quit.
#
class OnExitCallbackManager:

    def __init__(self, application: "CuraApplication") -> None:
        self._application = application
        self._on_exit_callback_list = list()  # type: List[Callable]
        self._current_callback_idx = 0
        self._is_all_checks_passed = False

    def addCallback(self, callback: Callable) -> None:
        self._on_exit_callback_list.append(callback)
        Logger.log("d", "on-app-exit callback [%s] added.", callback)

    # Reset the current state so the next time it will call all the callbacks again.
    def resetCurrentState(self) -> None:
        self._current_callback_idx = 0
        self._is_all_checks_passed = False

    def getIsAllChecksPassed(self) -> bool:
        return self._is_all_checks_passed

    # Trigger the next callback if there is one.
    # If not, all callbacks have "passed",
    # which means we should not prevent the application from quitting,
    # and we call the application to actually quit.
    def triggerNextCallback(self) -> None:
        # Get the next callback and schedule it
        this_callback = None
        if self._current_callback_idx < len(self._on_exit_callback_list):
            this_callback = self._on_exit_callback_list[self._current_callback_idx]
            self._current_callback_idx += 1

        if this_callback is not None:
            Logger.log("d", "Scheduled the next on-app-exit callback [%s]", this_callback)
            self._application.callLater(this_callback)
        else:
            Logger.log("d", "No more on-app-exit callbacks to process. Tell the app to exit.")

            self._is_all_checks_passed = True

            # Tell the application to exit
            self._application.callLater(self._application.closeApplication)

    # Callback function which an on-exit callback calls when it finishes.
    # It provides a "should_proceed" flag indicating whether the check has "passed",
    # or whether quitting the application should be blocked.
    # If the last on-exit callback doesn't block quitting, it will call the next
    # registered on-exit callback if one is available.
    def onCurrentCallbackFinished(self, should_proceed: bool = True) -> None:
        if not should_proceed:
            Logger.log("d", "on-app-exit callback finished and we should not proceed.")
            # Reset the state
            self.resetCurrentState()
            return

        self.triggerNextCallback()
