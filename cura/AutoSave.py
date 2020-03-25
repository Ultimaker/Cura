# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QTimer
from typing import Any, TYPE_CHECKING

from UM.Logger import Logger

if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication


class AutoSave:
    def __init__(self, application: "CuraApplication") -> None:
        self._application = application
        self._application.getPreferences().preferenceChanged.connect(self._triggerTimer)

        self._global_stack = None

        self._application.getPreferences().addPreference("cura/autosave_delay", 1000 * 10)

        self._change_timer = QTimer()
        self._change_timer.setInterval(int(self._application.getPreferences().getValue("cura/autosave_delay")))
        self._change_timer.setSingleShot(True)

        self._enabled = True
        self._saving = False

    def initialize(self) -> None:
        # only initialise if the application is created and has started
        self._change_timer.timeout.connect(self._onTimeout)
        self._application.globalContainerStackChanged.connect(self._onGlobalStackChanged)
        self._onGlobalStackChanged()
        self._triggerTimer()

    def _triggerTimer(self, *args: Any) -> None:
        if not self._saving:
            self._change_timer.start()

    def setEnabled(self, enabled: bool) -> None:
        self._enabled = enabled
        if self._enabled:
            self._change_timer.start()
        else:
            self._change_timer.stop()

    def _onGlobalStackChanged(self) -> None:
        if self._global_stack:
            self._global_stack.propertyChanged.disconnect(self._triggerTimer)
            self._global_stack.containersChanged.disconnect(self._triggerTimer)

        self._global_stack = self._application.getGlobalContainerStack()

        if self._global_stack:
            self._global_stack.propertyChanged.connect(self._triggerTimer)
            self._global_stack.containersChanged.connect(self._triggerTimer)

    def _onTimeout(self) -> None:
        self._saving = True # To prevent the save process from triggering another autosave.
        Logger.log("d", "Autosaving preferences, instances and profiles")

        self._application.saveSettings()

        self._saving = False
