# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING, Callable, List

from UM.Logger import Logger

if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication


#
# This class manages a all registered upon-exit checks that need to be perform when the application tries to exit.
# For example, to show a confirmation dialog when there is USB printing in progress, etc. All callbacks will be called
# in the order of when they got registered. If all callbacks "passes", that is, for example, if the user clicks "yes"
# on the exit confirmation dialog or nothing that's blocking the exit, then the application will quit after that.
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

    # Trigger the next callback if available. If not, it means that all callbacks have "passed", which means we should
    # not block the application to quit, and it will call the application to actually quit.
    def triggerNextCallback(self) -> None:
        # Get the next callback and schedule that if
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

    # This is the callback function which an on-exit callback should call when it finishes, it should provide the
    # "should_proceed" flag indicating whether this check has "passed", or in other words, whether quitting the
    # application should be blocked. If the last on-exit callback doesn't block the quitting, it will call the next
    # registered on-exit callback if available.
    def onCurrentCallbackFinished(self, should_proceed: bool = True) -> None:
        if not should_proceed:
            Logger.log("d", "on-app-exit callback finished and we should not proceed.")
            # Reset the state
            self.resetCurrentState()
            return

        self.triggerNextCallback()
