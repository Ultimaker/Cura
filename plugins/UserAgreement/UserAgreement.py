# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Extension import Extension
from UM.Preferences import Preferences
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry
from UM.Logger import Logger

from cura.CuraApplication import CuraApplication

from PyQt5.QtCore import QObject, pyqtSlot

import os.path

class UserAgreement(QObject, Extension):
    def __init__(self):
        super(UserAgreement, self).__init__()
        self._user_agreement_window = None
        self._user_agreement_context = None
        Application.getInstance().engineCreatedSignal.connect(self._onEngineCreated)
        Preferences.getInstance().addPreference("general/accepted_user_agreement", False)

    def _onEngineCreated(self):
        if not Preferences.getInstance().getValue("general/accepted_user_agreement"):
            self.showUserAgreement()

    def showUserAgreement(self):
        if not self._user_agreement_window:
            self.createUserAgreementWindow()

        self._user_agreement_window.show()

    @pyqtSlot(bool)
    def didAgree(self, user_choice):
        if user_choice:
            Logger.log("i", "User agreed to the user agreement")
            Preferences.getInstance().setValue("general/accepted_user_agreement", True)
            self._user_agreement_window.hide()
        else:
            Logger.log("i", "User did NOT agree to the user agreement")
            Preferences.getInstance().setValue("general/accepted_user_agreement", False)
            CuraApplication.getInstance().quit()
        CuraApplication.getInstance().setNeedToShowUserAgreement(False)

    def createUserAgreementWindow(self):
        path = os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), "UserAgreement.qml")
        self._user_agreement_window = Application.getInstance().createQmlComponent(path, {"manager": self})
