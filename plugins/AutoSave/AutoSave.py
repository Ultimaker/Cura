# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QTimer

from UM.Extension import Extension
from UM.Preferences import Preferences
from UM.Application import Application
from UM.Resources import Resources
from UM.Logger import Logger

class AutoSave(Extension):
    def __init__(self):
        super().__init__()

        Preferences.getInstance().preferenceChanged.connect(self._triggerTimer)

        self._global_stack = None
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalStackChanged)
        self._onGlobalStackChanged()

        Preferences.getInstance().addPreference("cura/autosave_delay", 1000 * 10)

        self._change_timer = QTimer()
        self._change_timer.setInterval(Preferences.getInstance().getValue("cura/autosave_delay"))
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self._onTimeout)

        self._saving = False

    def _triggerTimer(self, *args):
        if not self._saving:
            self._change_timer.start()

    def _onGlobalStackChanged(self):
        if self._global_stack:
            self._global_stack.propertyChanged.disconnect(self._triggerTimer)
            self._global_stack.containersChanged.disconnect(self._triggerTimer)

        self._global_stack = Application.getInstance().getGlobalContainerStack()

        if self._global_stack:
            self._global_stack.propertyChanged.connect(self._triggerTimer)
            self._global_stack.containersChanged.connect(self._triggerTimer)

    def _onTimeout(self):
        self._saving = True # To prevent the save process from triggering another autosave.
        Logger.log("d", "Autosaving preferences, instances and profiles")

        Application.getInstance().saveSettings()

        Preferences.getInstance().writeToFile(Resources.getStoragePath(Resources.Preferences, Application.getInstance().getApplicationName() + ".cfg"))

        self._saving = False
