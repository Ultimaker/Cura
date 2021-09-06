# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import json
import math
import os
import tempfile
import threading
from enum import IntEnum
from pathlib import Path
from typing import Optional, List, Dict, Any, cast

from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, pyqtProperty, Q_ENUMS, QTimer, QUrl
from PyQt5.QtNetwork import QNetworkReply
from PyQt5.QtQml import qmlRegisterType, qmlRegisterUncreatableType

from UM.FileHandler.FileHandler import FileHandler
from UM.Logger import Logger
from UM.Message import Message
from UM.Scene.SceneNode import SceneNode
from UM.Signal import Signal
from UM.TaskManagement.HttpRequestManager import HttpRequestManager
from cura.API import Account
from cura.CuraApplication import CuraApplication
from cura.UltimakerCloud.UltimakerCloudScope import UltimakerCloudScope
from .BackwardsCompatibleMessage import getBackwardsCompatibleMessage
from .DFFileExportAndUploadManager import DFFileExportAndUploadManager
from .DigitalFactoryApiClient import DigitalFactoryApiClient
from .DigitalFactoryFileModel import DigitalFactoryFileModel
from .DigitalFactoryFileResponse import DigitalFactoryFileResponse
from .DigitalFactoryProjectModel import DigitalFactoryProjectModel
from .DigitalFactoryProjectResponse import DigitalFactoryProjectResponse


class RetrievalStatus(IntEnum):
    """
    The status of an http get request.

    This is not an enum, because we want to use it in QML and QML doesn't recognize Python enums.
    """
    Idle = 0
    InProgress = 1
    Success = 2
    Failed = 3


class DFRetrievalStatus(QObject):
    """
    Used as an intermediate QObject that registers the RetrievalStatus as a recognizable enum in QML, so that it can
    be used within QML objects as DigitalFactory.RetrievalStatus.<status>
    """

    Q_ENUMS(RetrievalStatus)


class DigitalFactoryController(QObject):

    DISK_WRITE_BUFFER_SIZE = 256 * 1024  # 256 KB

    selectedProjectIndexChanged = pyqtSignal(int, arguments = ["newProjectIndex"])
    """Signal emitted whenever the selected project is changed in the projects dropdown menu"""

    selectedFileIndicesChanged = pyqtSignal("QList<int>", arguments = ["newFileIndices"])
    """Signal emitted whenever the selected file is changed in the files table"""

    retrievingProjectsStatusChanged = pyqtSignal(int, arguments = ["status"])
    """Signal emitted whenever the status of the 'retrieving projects' http get request is changed"""

    retrievingFilesStatusChanged = pyqtSignal(int, arguments = ["status"])
    """Signal emitted whenever the status of the 'retrieving files in project' http get request is changed"""

    creatingNewProjectStatusChanged = pyqtSignal(int, arguments = ["status"])
    """Signal emitted whenever the status of the 'create new library project' http get request is changed"""

    hasMoreProjectsToLoadChanged = pyqtSignal()
    """Signal emitted whenever the variable hasMoreProjectsToLoad is changed. This variable is used to determine if 
    the paginated list of projects has more pages to show"""

    preselectedProjectChanged = pyqtSignal()
    """Signal emitted whenever a preselected project is set. Whenever there is a preselected project, it means that it is
    the only project in the ProjectModel. When the preselected project is invalidated, the ProjectsModel needs to be
    retrieved again."""

    projectCreationErrorTextChanged = pyqtSignal()
    """Signal emitted whenever the creation of a new project fails and a specific error message is returned from the
    server."""

    """Signals to inform about the process of the file upload"""
    uploadStarted = Signal()
    uploadFileProgress = Signal()
    uploadFileSuccess = Signal()
    uploadFileError = Signal()
    uploadFileFinished = Signal()

    """Signal to inform about the state of user access."""
    userAccessStateChanged = pyqtSignal(bool)

    """Signal to inform whether the user is allowed to create more Library projects."""
    userCanCreateNewLibraryProjectChanged = pyqtSignal(bool)

    def __init__(self, application: CuraApplication) -> None:
        super().__init__(parent = None)

        self._application = application
        self._dialog = None  # type: Optional["QObject"]

        self.file_handlers = {}  # type: Dict[str, FileHandler]
        self.nodes = None  # type: Optional[List[SceneNode]]
        self.file_upload_manager = None  # type: Optional[DFFileExportAndUploadManager]
        self._has_preselected_project = False  # type: bool

        self._api = DigitalFactoryApiClient(self._application, on_error = lambda error: Logger.log("e", str(error)), projects_limit_per_page = 20)

        # Indicates whether there are more pages of projects that can be loaded from the API
        self._has_more_projects_to_load = False

        self._account = self._application.getInstance().getCuraAPI().account  # type: Account
        self._account.loginStateChanged.connect(self._onLoginStateChanged)
        self._current_workspace_information = CuraApplication.getInstance().getCurrentWorkspaceInformation()

        # Initialize the project model
        self._project_model = DigitalFactoryProjectModel()
        self._selected_project_idx = -1
        self._project_creation_error_text = "Something went wrong while creating a new project. Please try again."
        self._project_filter = ""
        self._project_filter_change_timer = QTimer()
        self._project_filter_change_timer.setInterval(200)
        self._project_filter_change_timer.setSingleShot(True)
        self._project_filter_change_timer.timeout.connect(self._applyProjectFilter)

        # Initialize the file model
        self._file_model = DigitalFactoryFileModel()
        self._selected_file_indices = []  # type: List[int]

        # Filled after the application has been initialized
        self._supported_file_types = {}  # type: Dict[str, str]

        # For cleaning up the files afterwards:
        self._erase_temp_files_lock = threading.Lock()

        # The statuses which indicate whether Cura is waiting for a response from the DigitalFactory API
        self.retrieving_files_status = RetrievalStatus.Idle
        self.retrieving_projects_status = RetrievalStatus.Idle
        self.creating_new_project_status = RetrievalStatus.Idle

        self._application.engineCreatedSignal.connect(self._onEngineCreated)
        self._application.initializationFinished.connect(self._applicationInitializationFinished)

        self._user_has_access = False
        self._user_account_can_create_new_project = False

    def clear(self) -> None:
        self._project_model.clearProjects()
        self._api.clear()
        self._has_preselected_project = False
        self.preselectedProjectChanged.emit()

        self.setRetrievingFilesStatus(RetrievalStatus.Idle)
        self.setRetrievingProjectsStatus(RetrievalStatus.Idle)
        self.setCreatingNewProjectStatus(RetrievalStatus.Idle)

        self.setSelectedProjectIndex(-1)

    def _onLoginStateChanged(self, logged_in: bool) -> None:
        def callback(has_access, **kwargs):
            self._user_has_access = has_access
            self.userAccessStateChanged.emit(logged_in)

        self._api.checkUserHasAccess(callback)

    def userAccountHasLibraryAccess(self) -> bool:
        """
        Checks whether the currently logged in user account has access to the Digital Library

        :return: True if the user account has Digital Library access, else False
        """
        if self._user_has_access:
            self._api.checkUserCanCreateNewLibraryProject(callback = self.setCanCreateNewLibraryProject)
        return self._user_has_access

    def initialize(self, preselected_project_id: Optional[str] = None) -> None:
        self.clear()

        if self._account.isLoggedIn and self.userAccountHasLibraryAccess():
            self.setRetrievingProjectsStatus(RetrievalStatus.InProgress)
            if preselected_project_id:
                self._api.getProject(preselected_project_id, on_finished = self.setProjectAsPreselected, failed = self._onGetProjectFailed)
            else:
                self._api.getProjectsFirstPage(search_filter = self._project_filter, on_finished = self._onGetProjectsFirstPageFinished, failed = self._onGetProjectsFailed)

    def setProjectAsPreselected(self, df_project: DigitalFactoryProjectResponse) -> None:
        """
        Sets the received df_project as the preselected one. When a project is preselected, it should be the only
        project inside the model, so this function first makes sure to clear the projects model.

        :param df_project: The library project intended to be set as preselected
        """
        self._project_model.clearProjects()
        self._project_model.setProjects([df_project])
        self.setSelectedProjectIndex(0)
        self.setHasPreselectedProject(True)
        self.setRetrievingProjectsStatus(RetrievalStatus.Success)
        self.setCreatingNewProjectStatus(RetrievalStatus.Success)

    def _onGetProjectFailed(self, reply: QNetworkReply, error: QNetworkReply.NetworkError) -> None:
        reply_string = bytes(reply.readAll()).decode()
        self.setHasPreselectedProject(False)
        Logger.log("w", "Something went wrong while trying to retrieve a the preselected Digital Library project. Error: {}".format(reply_string))

    def _onGetProjectsFirstPageFinished(self, df_projects: List[DigitalFactoryProjectResponse]) -> None:
        """
        Set the first page of projects received from the digital factory library in the project model. Called whenever
        the retrieval of the first page of projects is successful.

        :param df_projects: A list of all the Digital Factory Library projects linked to the user's account
        """
        self.setHasMoreProjectsToLoad(self._api.hasMoreProjectsToLoad())
        self._project_model.setProjects(df_projects)
        self.setRetrievingProjectsStatus(RetrievalStatus.Success)

    @pyqtSlot()
    def loadMoreProjects(self) -> None:
        """
        Initiates the process of retrieving the next page of the projects list from the API.
        """
        self._api.getMoreProjects(on_finished = self.loadMoreProjectsFinished, failed = self._onGetProjectsFailed)
        self.setRetrievingProjectsStatus(RetrievalStatus.InProgress)

    def loadMoreProjectsFinished(self, df_projects: List[DigitalFactoryProjectResponse]) -> None:
        """
        Set the projects received from the digital factory library in the project model. Called whenever the retrieval
        of the projects is successful.

        :param df_projects: A list of all the Digital Factory Library projects linked to the user's account
        """
        self.setHasMoreProjectsToLoad(self._api.hasMoreProjectsToLoad())
        self._project_model.extendProjects(df_projects)
        self.setRetrievingProjectsStatus(RetrievalStatus.Success)

    def _onGetProjectsFailed(self, reply: QNetworkReply, error: QNetworkReply.NetworkError) -> None:
        """
        Error function, called whenever the retrieval of projects fails.
        """
        self.setRetrievingProjectsStatus(RetrievalStatus.Failed)
        Logger.log("w", "Failed to retrieve the list of projects from the Digital Library. Error encountered: {}".format(error))

    def getProjectFilesFinished(self, df_files_in_project: List[DigitalFactoryFileResponse]) -> None:
        """
        Set the files received from the digital factory library in the file model. The files are filtered to only
        contain the files which can be opened by Cura.
        Called whenever the retrieval of the files is successful.

        :param df_files_in_project: A list of all the Digital Factory Library files that exist in a library project
        """
        # Filter to show only the files that can be opened in Cura
        self._file_model.setFilters({"file_name": lambda x: Path(x).suffix[1:].lower() in self._supported_file_types})  # the suffix is in format '.xyz', so omit the dot at the start
        self._file_model.setFiles(df_files_in_project)
        self.setRetrievingFilesStatus(RetrievalStatus.Success)

    def getProjectFilesFailed(self, reply: QNetworkReply, error: QNetworkReply.NetworkError) -> None:
        """
        Error function, called whenever the retrieval of the files in a library project fails.
        """
        Logger.log("w", "Failed to retrieve the list of files in project '{}' from the Digital Library".format(self._project_model._projects[self._selected_project_idx]))
        self.setRetrievingFilesStatus(RetrievalStatus.Failed)

    @pyqtSlot()
    def clearProjectSelection(self) -> None:
        """
        Clear the selected project.
        """
        if self._has_preselected_project:
            self.setHasPreselectedProject(False)
        else:
            self.setSelectedProjectIndex(-1)

    @pyqtSlot(int)
    def setSelectedProjectIndex(self, project_idx: int) -> None:
        """
        Sets the index of the project which is currently selected in the dropdown menu. Then, it uses the project_id of
        that project to retrieve the list of files included in that project and display it in the interface.

        :param project_idx: The index of the currently selected project
        """
        if project_idx < -1 or project_idx >= len(self._project_model.items):
            Logger.log("w", "The selected project index is invalid.")
            project_idx = -1  # -1 is a valid index for the combobox and it is handled as "nothing is selected"
        self._selected_project_idx = project_idx
        self.selectedProjectIndexChanged.emit(project_idx)

        # Clear the files from the previously-selected project and refresh the files model with the newly-selected-
        # project's files
        self._file_model.clearFiles()
        self.selectedFileIndicesChanged.emit([])
        if 0 <= project_idx < len(self._project_model.items):
            library_project_id = self._project_model.items[project_idx]["libraryProjectId"]
            self.setRetrievingFilesStatus(RetrievalStatus.InProgress)
            self._api.getListOfFilesInProject(library_project_id, on_finished = self.getProjectFilesFinished, failed = self.getProjectFilesFailed)

    @pyqtProperty(int, fset = setSelectedProjectIndex, notify = selectedProjectIndexChanged)
    def selectedProjectIndex(self) -> int:
        return self._selected_project_idx

    @pyqtSlot("QList<int>")
    def setSelectedFileIndices(self, file_indices: List[int]) -> None:
        """
        Sets the index of the file which is currently selected in the list of files.

        :param file_indices: The index of the currently selected file
        """
        if file_indices != self._selected_file_indices:
            self._selected_file_indices = file_indices
            self.selectedFileIndicesChanged.emit(file_indices)

    def setProjectFilter(self, new_filter: str) -> None:
        """
        Called when the user wants to change the search filter for projects.

        The filter is not immediately applied. There is some delay to allow the user to finish typing.
        :param new_filter: The new filter that the user wants to apply.
        """
        self._project_filter = new_filter
        self._project_filter_change_timer.start()

    """
    Signal to notify Qt that the applied filter has changed.
    """
    projectFilterChanged = pyqtSignal()

    @pyqtProperty(str, notify = projectFilterChanged, fset = setProjectFilter)
    def projectFilter(self) -> str:
        """
        The current search filter being applied to the project list.
        :return: The current search filter being applied to the project list.
        """
        return self._project_filter

    def _applyProjectFilter(self) -> None:
        """
        Actually apply the current filter to search for projects with the user-defined search string.
        :return:
        """
        self.clear()
        self.projectFilterChanged.emit()
        self._api.getProjectsFirstPage(search_filter = self._project_filter, on_finished = self._onGetProjectsFirstPageFinished, failed = self._onGetProjectsFailed)

    @pyqtProperty(QObject, constant = True)
    def digitalFactoryProjectModel(self) -> "DigitalFactoryProjectModel":
        return self._project_model

    @pyqtProperty(QObject, constant = True)
    def digitalFactoryFileModel(self) -> "DigitalFactoryFileModel":
        return self._file_model

    def setHasMoreProjectsToLoad(self, has_more_projects_to_load: bool) -> None:
        """
        Set the value that indicates whether there are more pages of projects that can be loaded from the API

        :param has_more_projects_to_load: Whether there are more pages of projects
        """
        if has_more_projects_to_load != self._has_more_projects_to_load:
            self._has_more_projects_to_load = has_more_projects_to_load
            self.hasMoreProjectsToLoadChanged.emit()

    @pyqtProperty(bool, fset = setHasMoreProjectsToLoad, notify = hasMoreProjectsToLoadChanged)
    def hasMoreProjectsToLoad(self) -> bool:
        """
        :return: whether there are more pages for projects that can be loaded from the API
        """
        return self._has_more_projects_to_load

    @pyqtSlot(str)
    def createLibraryProjectAndSetAsPreselected(self, project_name: Optional[str]) -> None:
        """
        Creates a new project with the given name in the Digital Library.

        :param project_name: The name that will be used for the new project
        """
        if project_name:
            self._api.createNewProject(project_name, self.setProjectAsPreselected, self._createNewLibraryProjectFailed)
            self.setCreatingNewProjectStatus(RetrievalStatus.InProgress)
        else:
            Logger.log("w", "No project name provided while attempting to create a new project. Aborting the project creation.")

    def _createNewLibraryProjectFailed(self, reply: QNetworkReply, error: QNetworkReply.NetworkError) -> None:
        reply_string = bytes(reply.readAll()).decode()

        self._project_creation_error_text = "Something went wrong while creating the new project. Please try again."
        if reply_string:
            reply_dict = json.loads(reply_string)
            if "errors" in reply_dict and len(reply_dict["errors"]) >= 1 and "title" in reply_dict["errors"][0]:
                self._project_creation_error_text = "Error while creating the new project: {}".format(reply_dict["errors"][0]["title"])
        self.projectCreationErrorTextChanged.emit()

        self.setCreatingNewProjectStatus(RetrievalStatus.Failed)
        Logger.log("e", "Something went wrong while trying to create a new a project. Error: {}".format(reply_string))

    def setRetrievingProjectsStatus(self, new_status: RetrievalStatus) -> None:
        """
        Sets the status of the "retrieving library projects" http call.

        :param new_status: The new status
        """
        self.retrieving_projects_status = new_status
        self.retrievingProjectsStatusChanged.emit(int(new_status))

    @pyqtProperty(int, fset = setRetrievingProjectsStatus, notify = retrievingProjectsStatusChanged)
    def retrievingProjectsStatus(self) -> int:
        return int(self.retrieving_projects_status)

    def setRetrievingFilesStatus(self, new_status: RetrievalStatus) -> None:
        """
        Sets the status of the "retrieving files list in the selected library project" http call.

        :param new_status: The new status
        """
        self.retrieving_files_status = new_status
        self.retrievingFilesStatusChanged.emit(int(new_status))

    @pyqtProperty(int, fset = setRetrievingFilesStatus, notify = retrievingFilesStatusChanged)
    def retrievingFilesStatus(self) -> int:
        return int(self.retrieving_files_status)

    def setCreatingNewProjectStatus(self, new_status: RetrievalStatus) -> None:
        """
        Sets the status of the "creating new library project" http call.

        :param new_status: The new status
        """
        self.creating_new_project_status = new_status
        self.creatingNewProjectStatusChanged.emit(int(new_status))

    @pyqtProperty(int, fset = setCreatingNewProjectStatus, notify = creatingNewProjectStatusChanged)
    def creatingNewProjectStatus(self) -> int:
        return int(self.creating_new_project_status)

    @staticmethod
    def _onEngineCreated() -> None:
        qmlRegisterUncreatableType(DFRetrievalStatus, "DigitalFactory", 1, 0, "RetrievalStatus", "Could not create RetrievalStatus enum type")

    def _applicationInitializationFinished(self) -> None:
        self._supported_file_types = self._application.getInstance().getMeshFileHandler().getSupportedFileTypesRead()

        # Although Cura supports these, it's super confusing in this context to show them.
        for extension in ["jpg", "jpeg", "png", "bmp", "gif"]:
            if extension in self._supported_file_types:
                del self._supported_file_types[extension]

    @pyqtSlot()
    def openSelectedFiles(self) -> None:
        """ Downloads, then opens all files selected in the Qt frontend open dialog.
        """

        temp_dir = tempfile.mkdtemp()
        if temp_dir is None or temp_dir == "":
            Logger.error("Digital Library: Couldn't create temporary directory to store to-be downloaded files.")
            return

        if self._selected_project_idx < 0 or len(self._selected_file_indices) < 1:
            Logger.error("Digital Library: No project or no file selected on open action.")
            return

        to_erase_on_done_set = {
            os.path.join(temp_dir, self._file_model.getItem(i)["fileName"]).replace('\\', '/')
            for i in self._selected_file_indices}

        def onLoadedCallback(filename_done: str) -> None:
            filename_done = os.path.join(temp_dir, filename_done).replace('\\', '/')
            with self._erase_temp_files_lock:
                if filename_done in to_erase_on_done_set:
                    try:
                        os.remove(filename_done)
                        to_erase_on_done_set.remove(filename_done)
                        if len(to_erase_on_done_set) < 1 and os.path.exists(temp_dir):
                            os.rmdir(temp_dir)
                    except (IOError, OSError) as ex:
                        Logger.error("Can't erase temporary (in) {0} because {1}.", temp_dir, str(ex))

            # Save the project id to make sure it will be preselected the next time the user opens the save dialog
            CuraApplication.getInstance().getCurrentWorkspaceInformation().setEntryToStore("digital_factory", "library_project_id", library_project_id)

            # Disconnect the signals so that they are not fired every time another (project) file is loaded
            app.fileLoaded.disconnect(onLoadedCallback)
            app.workspaceLoaded.disconnect(onLoadedCallback)

        app = CuraApplication.getInstance()
        app.fileLoaded.connect(onLoadedCallback)  # fired when non-project files are loaded
        app.workspaceLoaded.connect(onLoadedCallback)  # fired when project files are loaded

        project_name = self._project_model.getItem(self._selected_project_idx)["displayName"]
        for file_index in self._selected_file_indices:
            file_item = self._file_model.getItem(file_index)
            file_name = file_item["fileName"]
            download_url = file_item["downloadUrl"]
            library_project_id = file_item["libraryProjectId"]
            self._openSelectedFile(temp_dir, project_name, file_name, download_url)

    def _openSelectedFile(self, temp_dir: str, project_name: str, file_name: str, download_url: str) -> None:
        """ Downloads, then opens, the single specified file.

        :param temp_dir: The already created temporary directory where the files will be stored.
        :param project_name: Name of the project the file belongs to (used for error reporting).
        :param file_name: Name of the file to be downloaded and opened (used for error reporting).
        :param download_url: This url will be downloaded, then the downloaded file will be opened in Cura.
        """
        if not download_url:
            Logger.log("e", "No download url for file '{}'".format(file_name))
            return

        progress_message = Message(text = "{0}/{1}".format(project_name, file_name), dismissable = False, lifetime = 0,
                                   progress = 0, title = "Downloading...")
        progress_message.setProgress(0)
        progress_message.show()

        def progressCallback(rx: int, rt: int) -> None:
            progress_message.setProgress(math.floor(rx * 100.0 / rt))

        def finishedCallback(reply: QNetworkReply) -> None:
            progress_message.hide()
            try:
                with open(os.path.join(temp_dir, file_name), "wb+") as temp_file:
                    bytes_read = reply.read(self.DISK_WRITE_BUFFER_SIZE)
                    while bytes_read:
                        temp_file.write(bytes_read)
                        bytes_read = reply.read(self.DISK_WRITE_BUFFER_SIZE)
                        CuraApplication.getInstance().processEvents()
                    temp_file_name = temp_file.name
            except IOError as ex:
                Logger.logException("e", "Can't write Digital Library file {0}/{1} download to temp-directory {2}.",
                                    ex, project_name, file_name, temp_dir)
                getBackwardsCompatibleMessage(
                        text = "Failed to write to temporary file for '{}'.".format(file_name),
                        title = "File-system error",
                        message_type_str="ERROR",
                        lifetime = 10
                ).show()
                return

            CuraApplication.getInstance().readLocalFile(
                    QUrl.fromLocalFile(temp_file_name), add_to_recent_files = False)

        def errorCallback(reply: QNetworkReply, error: QNetworkReply.NetworkError, p = project_name,
                          f = file_name) -> None:
            progress_message.hide()
            Logger.error("An error {0} {1} occurred while downloading {2}/{3}".format(str(error), str(reply), p, f))
            getBackwardsCompatibleMessage(
                    text = "Failed Digital Library download for '{}'.".format(f),
                    title = "Network error {}".format(error),
                    message_type_str="ERROR",
                    lifetime = 10
            ).show()

        download_manager = HttpRequestManager.getInstance()
        download_manager.get(download_url, callback = finishedCallback, download_progress_callback = progressCallback,
                             error_callback = errorCallback, scope = UltimakerCloudScope(CuraApplication.getInstance()))

    def setHasPreselectedProject(self, new_has_preselected_project: bool) -> None:
        if not new_has_preselected_project:
            # The preselected project was the only one in the model, at index 0, so when we set the has_preselected_project to
            # false, we also need to clean it from the projects model
            self._project_model.clearProjects()
            self.setSelectedProjectIndex(-1)
            self._api.getProjectsFirstPage(search_filter = self._project_filter, on_finished = self._onGetProjectsFirstPageFinished, failed = self._onGetProjectsFailed)
            self._api.checkUserCanCreateNewLibraryProject(callback = self.setCanCreateNewLibraryProject)
            self.setRetrievingProjectsStatus(RetrievalStatus.InProgress)
        self._has_preselected_project = new_has_preselected_project
        self.preselectedProjectChanged.emit()

    @pyqtProperty(bool, fset = setHasPreselectedProject, notify = preselectedProjectChanged)
    def hasPreselectedProject(self) -> bool:
        return self._has_preselected_project

    def setCanCreateNewLibraryProject(self, can_create_new_library_project: bool) -> None:
        self._user_account_can_create_new_project = can_create_new_library_project
        self.userCanCreateNewLibraryProjectChanged.emit(self._user_account_can_create_new_project)

    @pyqtProperty(bool, fset = setCanCreateNewLibraryProject, notify = userCanCreateNewLibraryProjectChanged)
    def userAccountCanCreateNewLibraryProject(self) -> bool:
        return self._user_account_can_create_new_project

    @pyqtSlot(str, "QStringList")
    def saveFileToSelectedProject(self, filename: str, formats: List[str]) -> None:
        """
        Function triggered whenever the Save button is pressed.

        :param filename: The name (without the extension) that will be used for the files
        :param formats: List of the formats the scene will be exported to. Can include 3mf, ufp, or both
        """
        if self._selected_project_idx == -1:
            Logger.log("e", "No DF Library project is selected.")
            return

        if filename == "":
            Logger.log("w", "The file name cannot be empty.")
            getBackwardsCompatibleMessage(
                    text = "Cannot upload file with an empty name to the Digital Library",
                    title = "Empty file name provided",
                    message_type_str = "ERROR",
                    lifetime = 0
            ).show()
            return

        self._saveFileToSelectedProjectHelper(filename, formats)

    def _saveFileToSelectedProjectHelper(self, filename: str, formats: List[str]) -> None:
        # Indicate we have started sending a job (and propagate any user file name changes back to the open project)
        self.uploadStarted.emit(filename if "3mf" in formats else None)

        library_project_id = self._project_model.items[self._selected_project_idx]["libraryProjectId"]
        library_project_name = self._project_model.items[self._selected_project_idx]["displayName"]

        # Use the file upload manager to export and upload the 3mf and/or ufp files to the DF Library project
        self.file_upload_manager = DFFileExportAndUploadManager(file_handlers = self.file_handlers, nodes = cast(List[SceneNode], self.nodes),
                                                                library_project_id = library_project_id,
                                                                library_project_name = library_project_name,
                                                                file_name = filename, formats = formats,
                                                                on_upload_error = self.uploadFileError.emit,
                                                                on_upload_success = self.uploadFileSuccess.emit,
                                                                on_upload_finished = self.uploadFileFinished.emit,
                                                                on_upload_progress = self.uploadFileProgress.emit)
        self.file_upload_manager.start()

        # Save the project id to make sure it will be preselected the next time the user opens the save dialog
        self._current_workspace_information.setEntryToStore("digital_factory", "library_project_id", library_project_id)

    @pyqtProperty(str, notify = projectCreationErrorTextChanged)
    def projectCreationErrorText(self) -> str:
        return self._project_creation_error_text
