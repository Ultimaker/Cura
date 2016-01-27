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

        Preferences.getInstance().preferenceChanged.connect(self._onPreferenceChanged)

        machine_manager = Application.getInstance().getMachineManager()

        self._profile = None
        machine_manager.activeProfileChanged.connect(self._onActiveProfileChanged)
        machine_manager.profileNameChanged.connect(self._onProfileNameChanged)
        machine_manager.profilesChanged.connect(self._onProfilesChanged)
        machine_manager.machineInstanceNameChanged.connect(self._onInstanceNameChanged)
        machine_manager.machineInstancesChanged.connect(self._onInstancesChanged)
        Application
        self._onActiveProfileChanged()

        self._change_timer = QTimer()
        self._change_timer.setInterval(1000 * 60)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self._onTimeout)

        self._save_preferences = False
        self._save_profiles = False
        self._save_instances = False

    def _onPreferenceChanged(self, preference):
        self._save_preferences = True
        self._change_timer.start()

    def _onSettingValueChanged(self, setting):
        self._save_profiles = True
        self._change_timer.start()

    def _onActiveProfileChanged(self):
        if self._profile:
            self._profile.settingValueChanged.disconnect(self._onSettingValueChanged)

        self._profile = Application.getInstance().getMachineManager().getActiveProfile()

        if self._profile:
            self._profile.settingValueChanged.connect(self._onSettingValueChanged)

    def _onProfileNameChanged(self, name):
        self._onProfilesChanged()

    def _onProfilesChanged(self):
        self._save_profiles = True
        self._change_timer.start()

    def _onInstanceNameChanged(self, name):
        self._onInstancesChanged()

    def _onInstancesChanged(self):
        self._save_instances = True
        self._change_timer.start()

    def _onTimeout(self):
        Logger.log("d", "Autosaving preferences, instances and profiles")

        if self._save_preferences:
            Preferences.getInstance().writeToFile(Resources.getStoragePath(Resources.Preferences, Application.getInstance().getApplicationName() + ".cfg"))

        if self._save_instances:
            Application.getInstance().getMachineManager().saveMachineInstances()

        if self._save_profiles:
            Application.getInstance().getMachineManager().saveProfiles()

        self._save_preferences = False
        self._save_instances = False
        self._save_profiles = False
