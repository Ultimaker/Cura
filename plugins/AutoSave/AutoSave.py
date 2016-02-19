# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

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

        machine_manager = Application.getInstance().getMachineManager()

        self._profile = None
        machine_manager.activeProfileChanged.connect(self._onActiveProfileChanged)
        machine_manager.profileNameChanged.connect(self._triggerTimer)
        machine_manager.profilesChanged.connect(self._triggerTimer)
        machine_manager.machineInstanceNameChanged.connect(self._triggerTimer)
        machine_manager.machineInstancesChanged.connect(self._triggerTimer)
        self._onActiveProfileChanged()

        Preferences.getInstance().addPreference("cura/autosave_delay", 1000 * 10)

        self._change_timer = QTimer()
        self._change_timer.setInterval(Preferences.getInstance().getValue("cura/autosave_delay"))
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self._onTimeout)

        self._saving = False

    def _triggerTimer(self, *args):
        if not self._saving:
            self._change_timer.start()

    def _onActiveProfileChanged(self):
        if self._profile:
            self._profile.settingValueChanged.disconnect(self._triggerTimer)

        self._profile = Application.getInstance().getMachineManager().getWorkingProfile()

        if self._profile:
            self._profile.settingValueChanged.connect(self._triggerTimer)

    def _onTimeout(self):
        self._saving = True # To prevent the save process from triggering another autosave.
        Logger.log("d", "Autosaving preferences, instances and profiles")

        machine_manager = Application.getInstance().getMachineManager()

        machine_manager.saveVisibility()
        machine_manager.saveMachineInstances()
        machine_manager.saveProfiles()
        Preferences.getInstance().writeToFile(Resources.getStoragePath(Resources.Preferences, Application.getInstance().getApplicationName() + ".cfg"))

        self._saving = False
