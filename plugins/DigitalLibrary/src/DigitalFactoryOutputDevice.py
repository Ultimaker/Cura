# Copyright (c) 2021 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.
import os
from typing import Optional, List

from UM.FileHandler.FileHandler import FileHandler
from UM.Logger import Logger
from UM.OutputDevice import OutputDeviceError
from UM.OutputDevice.ProjectOutputDevice import ProjectOutputDevice
from UM.Scene.SceneNode import SceneNode
from UM.Version import Version
from cura import ApplicationMetadata
from cura.API import Account
from cura.CuraApplication import CuraApplication
from .DigitalFactoryController import DigitalFactoryController


class DigitalFactoryOutputDevice(ProjectOutputDevice):
    """Implements an OutputDevice that supports saving to the digital factory library."""

    def __init__(self, plugin_id, df_controller: DigitalFactoryController, add_to_output_devices: bool = False, parent = None) -> None:
        super().__init__(device_id = "digital_factory", add_to_output_devices = add_to_output_devices, parent = parent)

        self.setName("Digital Library")  # Doesn't need to be translated
        self.setShortDescription("Save to Library")
        self.setDescription("Save to Library")
        self.setIconName("save")
        self.menu_entry_text = "To Digital Library"
        self.shortcut = "Ctrl+Shift+S"
        self._plugin_id = plugin_id
        self._controller = df_controller

        plugin_path = os.path.dirname(os.path.dirname(__file__))
        self._dialog_path = os.path.join(plugin_path, "resources", "qml", "DigitalFactorySaveDialog.qml")
        self._dialog = None

        # Connect the write signals
        self._controller.uploadStarted.connect(self._onWriteStarted)
        self._controller.uploadFileProgress.connect(self.writeProgress.emit)
        self._controller.uploadFileError.connect(self._onWriteError)
        self._controller.uploadFileSuccess.connect(self.writeSuccess.emit)
        self._controller.uploadFileFinished.connect(self._onWriteFinished)

        self._priority = -1  # Negative value to ensure that it will have less priority than the LocalFileOutputDevice (which has 0)
        self._application = CuraApplication.getInstance()

        self._writing = False

        self._account = CuraApplication.getInstance().getCuraAPI().account  # type: Account
        self._controller.userAccessStateChanged.connect(self._onUserAccessStateChanged)
        self.enabled = self._account.isLoggedIn and self._controller.userAccountHasLibraryAccess()

        self._current_workspace_information = CuraApplication.getInstance().getCurrentWorkspaceInformation()

    def requestWrite(self, nodes: List[SceneNode], file_name: Optional[str] = None, limit_mimetypes: bool = False, file_handler: Optional[FileHandler] = None, **kwargs) -> None:
        """Request the specified nodes to be written.

        Function called every time the 'To Digital Factory' option of the 'Save Project' submenu is triggered or when the
        "Save to Library" action button is pressed (upon slicing).

        :param nodes: A collection of scene nodes that should be written to the file.
        :param file_name: A suggestion for the file name to write to.
        :param limit_mimetypes: Limit the possible mimetypes to use for writing to these types.
        :param file_handler: The handler responsible for reading and writing mesh files.
        :param kwargs: Keyword arguments.
        """

        if self._writing:
            raise OutputDeviceError.DeviceBusyError()
        self.loadWindow()

        if self._account.isLoggedIn and self._controller.userAccountHasLibraryAccess():
            self._controller.nodes = nodes

            df_workspace_information = self._current_workspace_information.getPluginMetadata("digital_factory")
            self._controller.initialize(preselected_project_id = df_workspace_information.get("library_project_id"))

            if not self._dialog:
                Logger.log("e", "Unable to create the Digital Library Save dialog.")
                return
            self._dialog.show()

    def loadWindow(self) -> None:
        """
        Create the GUI window for the Digital Library Save dialog. If the window is already open, bring the focus on it.
        """

        if self._dialog:  # Dialogue is already open.
            self._dialog.requestActivate()  # Bring the focus on the dialogue.
            return

        if not self._controller.file_handlers:
            self._controller.file_handlers = {
                "3mf": CuraApplication.getInstance().getWorkspaceFileHandler(),
                "ufp": CuraApplication.getInstance().getMeshFileHandler(),
                "makerbot": CuraApplication.getInstance().getMeshFileHandler()
            }

        self._dialog = CuraApplication.getInstance().createQmlComponent(self._dialog_path, {"manager": self._controller})
        if not self._dialog:
            Logger.log("e", "Unable to create the Digital Library Save dialog.")

    def _onUserAccessStateChanged(self, logged_in: bool) -> None:
        """
        Sets the enabled status of the DigitalFactoryOutputDevice according to the account's login status
        :param logged_in: The new login status
        """
        self.enabled = logged_in and self._controller.userAccountHasLibraryAccess()
        self.enabledChanged.emit()

    def _onWriteStarted(self, new_name: Optional[str] = None) -> None:
        self._writing = True
        if new_name and Version(ApplicationMetadata.CuraSDKVersion) >= Version("7.8.0"):
            # setLastOutputName is only supported in sdk version 7.8.0 and up
            self.setLastOutputName(new_name) # On saving, the user can change the name, this should propagate.
        self.writeStarted.emit(self)

    def _onWriteFinished(self) -> None:
        self._writing = False
        self.writeFinished.emit(self)

    def _onWriteError(self) -> None:
        self._writing = False
        self.writeError.emit(self)
