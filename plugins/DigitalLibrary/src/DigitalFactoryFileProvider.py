# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os

from UM.FileProvider import FileProvider
from UM.Logger import Logger
from cura.API import Account
from cura.CuraApplication import CuraApplication
from .DigitalFactoryController import DigitalFactoryController


class DigitalFactoryFileProvider(FileProvider):

    def __init__(self, df_controller: DigitalFactoryController) -> None:
        super().__init__()
        self._controller = df_controller

        self.menu_item_display_text = "From Digital Library"
        self.shortcut = "Ctrl+Shift+O"
        plugin_path = os.path.dirname(os.path.dirname(__file__))
        self._dialog_path = os.path.join(plugin_path, "resources", "qml", "DigitalFactoryOpenDialog.qml")

        self._account = CuraApplication.getInstance().getCuraAPI().account  # type: Account
        self._controller.userAccessStateChanged.connect(self._onUserAccessStateChanged)
        self.enabled = self._account.isLoggedIn and self._controller.userAccountHasLibraryAccess()
        self.priority = 10

    def run(self) -> None:
        """
        Function called every time the 'From Digital Factory' option of the 'Open File(s)' submenu is triggered
        """
        if self._account.isLoggedIn and self._controller.userAccountHasLibraryAccess():
            self._controller.initialize()
            self.loadWindow()

    def loadWindow(self) -> None:
        """
        Create the GUI window for the Digital Library Open dialog and shows it.
        """

        dialog = CuraApplication.getInstance().createQmlSubWindow(self._dialog_path, {"manager": self._controller})

        if dialog:
            dialog.show()
        else:
            Logger.log("e", "Unable to create the Digital Library Open dialog.")

    def _onUserAccessStateChanged(self, logged_in: bool) -> None:
        """
        Sets the enabled status of the DigitalFactoryFileProvider according to the account's login status
        :param logged_in: The new login status
        """
        self.enabled = logged_in and self._controller.userAccountHasLibraryAccess()
        self.enabledChanged.emit()
