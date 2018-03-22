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

        Preferences.getInstance().addPreference("cura/autosave_delay", 1000 * 10)

        self._change_timer = QTimer()
        self._change_timer.setInterval(Preferences.getInstance().getValue("cura/autosave_delay"))
        self._change_timer.setSingleShot(True)

        self._saving = False

        # At this point, the Application instance has not finished its constructor call yet, so directly using something
        # like Application.getInstance() is not correct. The initialisation now will only gets triggered after the
        # application finishes its start up successfully.
        self._init_timer = QTimer()
        self._init_timer.setInterval(1000)
        self._init_timer.setSingleShot(True)
        self._init_timer.timeout.connect(self.initialize)
        self._init_timer.start()

    def initialize(self):
        # only initialise if the application is created and has started
        from cura.CuraApplication import CuraApplication
        if not CuraApplication.Created:
            self._init_timer.start()
            return
        if not CuraApplication.getInstance().started:
            self._init_timer.start()
            return

        self._change_timer.timeout.connect(self._onTimeout)
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalStackChanged)
        self._onGlobalStackChanged()

        self._triggerTimer()

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
