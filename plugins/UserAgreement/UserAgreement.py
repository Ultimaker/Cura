# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os

from PyQt5.QtCore import QObject, pyqtSlot

from UM.Extension import Extension
from UM.Logger import Logger


class UserAgreement(QObject, Extension):
    def __init__(self, application):
        super(UserAgreement, self).__init__()
        self._application = application
        self._user_agreement_window = None
        self._user_agreement_context = None
        self._application.engineCreatedSignal.connect(self._onEngineCreated)

        self._application.getPreferences().addPreference("general/accepted_user_agreement", False)

    def _onEngineCreated(self):
        if not self._application.getPreferences().getValue("general/accepted_user_agreement"):
            self.showUserAgreement()

    def showUserAgreement(self):
        if not self._user_agreement_window:
            self.createUserAgreementWindow()

        self._user_agreement_window.show()

    @pyqtSlot(bool)
    def didAgree(self, user_choice):
        if user_choice:
            Logger.log("i", "User agreed to the user agreement")
            self._application.getPreferences().setValue("general/accepted_user_agreement", True)
            self._user_agreement_window.hide()
        else:
            Logger.log("i", "User did NOT agree to the user agreement")
            self._application.getPreferences().setValue("general/accepted_user_agreement", False)
            self._application.quit()
        self._application.setNeedToShowUserAgreement(False)

    def createUserAgreementWindow(self):
        path = os.path.join(self._application.getPluginRegistry().getPluginPath(self.getPluginId()), "UserAgreement.qml")
        self._user_agreement_window = self._application.createQmlComponent(path, {"manager": self})
