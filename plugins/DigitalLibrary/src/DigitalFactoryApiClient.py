# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import json
from json import JSONDecodeError
import re
from time import time
from typing import List, Any, Optional, Union, Type, Tuple, Dict, cast, TypeVar, Callable

from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest

from UM.Logger import Logger
from UM.TaskManagement.HttpRequestManager import HttpRequestManager
from UM.TaskManagement.HttpRequestScope import JsonDecoratorScope
from cura.CuraApplication import CuraApplication
from cura.UltimakerCloud import UltimakerCloudConstants
from cura.UltimakerCloud.UltimakerCloudScope import UltimakerCloudScope
from .DFPrintJobUploadResponse import DFPrintJobUploadResponse
from .BaseModel import BaseModel
from .CloudError import CloudError
from .DFFileUploader import DFFileUploader
from .DFLibraryFileUploadRequest import DFLibraryFileUploadRequest
from .DFLibraryFileUploadResponse import DFLibraryFileUploadResponse
from .DFPrintJobUploadRequest import DFPrintJobUploadRequest
from .DigitalFactoryFeatureBudgetResponse import DigitalFactoryFeatureBudgetResponse
from .DigitalFactoryFileResponse import DigitalFactoryFileResponse
from .DigitalFactoryProjectResponse import DigitalFactoryProjectResponse
from .PaginationLinks import PaginationLinks
from .PaginationManager import PaginationManager

CloudApiClientModel = TypeVar("CloudApiClientModel", bound=BaseModel)
"""The generic type variable used to document the methods below."""


class DigitalFactoryApiClient:
    # The URL to access the digital factory.
    ROOT_PATH = UltimakerCloudConstants.CuraCloudAPIRoot
    CURA_API_ROOT = "{}/cura/v1".format(ROOT_PATH)

    DEFAULT_REQUEST_TIMEOUT = 10  # seconds

    # In order to avoid garbage collection we keep the callbacks in this list.
    _anti_gc_callbacks = []  # type: List[Callable[[Any], None]]

    def __init__(self, application: CuraApplication, on_error: Callable[[List[CloudError]], None], projects_limit_per_page: Optional[int] = None) -> None:
        """Initializes a new digital factory API client.

        :param application:
        :param on_error: The callback to be called whenever we receive errors from the server.
        """
        super().__init__()
        self._application = application
        self._account = application.getCuraAPI().account
        self._scope = JsonDecoratorScope(UltimakerCloudScope(application))
        self._http = HttpRequestManager.getInstance()
        self._on_error = on_error
        self._file_uploader = None  # type: Optional[DFFileUploader]
        self._library_max_private_projects: Optional[int] = None

        self._projects_pagination_mgr = PaginationManager(limit = projects_limit_per_page) if projects_limit_per_page else None  # type: Optional[PaginationManager]

    def checkUserHasAccess(self, callback: Callable) -> None:
        """Checks if the user has any sort of access to the digital library.
           A user is considered to have access if the max-# of private projects is greater then 0 (or -1 for unlimited).
        """

        def callbackWrap(response: Optional[Any] = None, *args, **kwargs) -> None:
            if (response is not None and isinstance(response, DigitalFactoryFeatureBudgetResponse) and
                    response.library_max_private_projects is not None):
                # A user has DF access when library_max_private_projects is either -1 (unlimited) or bigger then 0
                has_access = response.library_max_private_projects == -1 or response.library_max_private_projects > 0
                callback(has_access)
                self._library_max_private_projects = response.library_max_private_projects
                # update the account with the additional user rights
                self._account.updateAdditionalRight(df_access = has_access)
            else:
                Logger.warning(f"Digital Factory: Response is not a feature budget, likely an error: {str(response)}")
                callback(False)

        self._http.get(f"{self.CURA_API_ROOT}/feature_budgets",
                       scope = self._scope,
                       callback = self._parseCallback(callbackWrap, DigitalFactoryFeatureBudgetResponse, callbackWrap),
                       error_callback = callbackWrap,
                       timeout = self.DEFAULT_REQUEST_TIMEOUT)

    def checkUserCanCreateNewLibraryProject(self, callback: Callable) -> None:
        """
        Checks if the user is allowed to create new library projects.
        A user is allowed to create new library projects if the haven't reached their maximum allowed private projects.
        """

        def callbackWrap(response: Optional[Any] = None, *args, **kwargs) -> None:
            if response is not None:
                if isinstance(response, DigitalFactoryProjectResponse):  # The user has only one private project
                    callback(True)
                elif isinstance(response, list) and all(isinstance(r, DigitalFactoryProjectResponse) for r in response):
                    callback(len(response) < cast(int, self._library_max_private_projects))
                else:
                    Logger.warning(f"Digital Factory: Incorrect response type received when requesting private projects: {str(response)}")
                    callback(False)
            else:
                Logger.warning(f"Digital Factory: Response is empty, likely an error: {str(response)}")
                callback(False)

        if self._library_max_private_projects is not None and self._library_max_private_projects > 0:
            # The user has a limit in the number of private projects they can create. Check whether they have already
            # reached that limit.
            # Note: Set the pagination manager to None when doing this get request, or else the next/previous links
            #       of the pagination will become corrupted
            url = f"{self.CURA_API_ROOT}/projects?shared=false&limit={self._library_max_private_projects}"
            self._http.get(url,
                           scope = self._scope,
                           callback = self._parseCallback(callbackWrap, DigitalFactoryProjectResponse, callbackWrap, pagination_manager = None),
                           error_callback = callbackWrap,
                           timeout = self.DEFAULT_REQUEST_TIMEOUT)
        else:
            # If the limit is -1, then the user is allowed unlimited projects. If its 0 then they are not allowed to
            # create any projects
            callback(self._library_max_private_projects == -1)

    def getProject(self, library_project_id: str, on_finished: Callable[[DigitalFactoryProjectResponse], Any], failed: Callable) -> None:
        """
        Retrieves a digital factory project by its library project id.

        :param library_project_id: The id of the library project
        :param on_finished: The function to be called after the result is parsed.
        :param failed: The function to be called if the request fails.
        """
        url = "{}/projects/{}".format(self.CURA_API_ROOT, library_project_id)

        self._http.get(url,
                       scope = self._scope,
                       callback = self._parseCallback(on_finished, DigitalFactoryProjectResponse, failed),
                       error_callback = failed,
                       timeout = self.DEFAULT_REQUEST_TIMEOUT)

    def getProjectsFirstPage(self, search_filter: str, on_finished: Callable[[List[DigitalFactoryProjectResponse]], Any], failed: Callable) -> None:
        """
        Retrieves digital factory projects for the user that is currently logged in.

        If a projects pagination manager exists, then it attempts to get the first page of the paginated projects list,
        according to the limit set in the pagination manager. If there is no projects pagination manager, this function
        leaves the project limit to the default set on the server side (999999).

        :param search_filter: Text to filter the search results. If given an empty string, results are not filtered.
        :param on_finished: The function to be called after the result is parsed.
        :param failed: The function to be called if the request fails.
        """
        url = f"{self.CURA_API_ROOT}/projects"
        query_character = "?"
        if self._projects_pagination_mgr:
            self._projects_pagination_mgr.reset()  # reset to clear all the links and response metadata
            url += f"{query_character}limit={self._projects_pagination_mgr.limit}"
            query_character = "&"
        if search_filter != "":
            url += f"{query_character}search={search_filter}"

        self._http.get(url,
                       scope = self._scope,
                       callback = self._parseCallback(on_finished, DigitalFactoryProjectResponse, failed, pagination_manager = self._projects_pagination_mgr),
                       error_callback = failed,
                       timeout = self.DEFAULT_REQUEST_TIMEOUT)

    def getMoreProjects(self,
                        on_finished: Callable[[List[DigitalFactoryProjectResponse]], Any],
                        failed: Callable) -> None:
        """Retrieves the next page of the paginated projects list from the API, provided that there is any.

        :param on_finished: The function to be called after the result is parsed.
        :param failed: The function to be called if the request fails.
        """

        if self.hasMoreProjectsToLoad():
            url = cast(PaginationLinks, cast(PaginationManager, self._projects_pagination_mgr).links).next_page
            self._http.get(url,
                           scope = self._scope,
                           callback = self._parseCallback(on_finished, DigitalFactoryProjectResponse, failed, pagination_manager = self._projects_pagination_mgr),
                           error_callback = failed,
                           timeout = self.DEFAULT_REQUEST_TIMEOUT)
        else:
            Logger.log("d", "There are no more projects to load.")

    def hasMoreProjectsToLoad(self) -> bool:
        """
        Determines whether the client can get more pages of projects list from the API.

        :return: Whether there are more pages in the projects list available to be retrieved from the API.
        """
        return self._projects_pagination_mgr is not None and self._projects_pagination_mgr.links is not None and self._projects_pagination_mgr.links.next_page is not None

    def getListOfFilesInProject(self, library_project_id: str, on_finished: Callable[[List[DigitalFactoryFileResponse]], Any], failed: Callable) -> None:
        """Retrieves the list of files contained in the project with library_project_id from the Digital Factory Library.

        :param library_project_id: The id of the digital factory library project in which the files are included
        :param on_finished: The function to be called after the result is parsed.
        :param failed: The function to be called if the request fails.
        """

        url = "{}/projects/{}/files".format(self.CURA_API_ROOT, library_project_id)
        self._http.get(url,
                       scope = self._scope,
                       callback = self._parseCallback(on_finished, DigitalFactoryFileResponse, failed),
                       error_callback = failed,
                       timeout = self.DEFAULT_REQUEST_TIMEOUT)

    def _parseCallback(self,
                       on_finished: Union[Callable[[CloudApiClientModel], Any],
                                          Callable[[List[CloudApiClientModel]], Any]],
                       model: Type[CloudApiClientModel],
                       on_error: Optional[Callable] = None,
                       pagination_manager: Optional[PaginationManager] = None) -> Callable[[QNetworkReply], None]:

        """
        Creates a callback function so that it includes the parsing of the response into the correct model.
        The callback is added to the 'finished' signal of the reply. If a paginated request was made and a pagination
        manager is given, the pagination metadata will be held there.

        :param on_finished: The callback in case the response is successful. Depending on the endpoint it will be either
        a list or a single item.
        :param model: The type of the model to convert the response to.
        :param on_error: The callback in case the response is ... less successful.
        :param pagination_manager: Holds the pagination links and metadata contained in paginated responses.
                                   If no pagination manager is provided, the pagination metadata is ignored.
        """

        def parse(reply: QNetworkReply) -> None:

            self._anti_gc_callbacks.remove(parse)

            # Don't try to parse the reply if we didn't get one
            if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) is None:
                if on_error is not None:
                    on_error()
                return

            status_code, response = self._parseReply(reply)
            if status_code >= 300 and on_error is not None:
                on_error()
            else:
                self._parseModels(response, on_finished, model, pagination_manager = pagination_manager)

        self._anti_gc_callbacks.append(parse)
        return parse

    @staticmethod
    def _parseReply(reply: QNetworkReply) -> Tuple[int, Dict[str, Any]]:
        """Parses the given JSON network reply into a status code and a dictionary, handling unexpected errors as well.

        :param reply: The reply from the server.
        :return: A tuple with a status code and a dictionary.
        """

        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        try:
            response = bytes(reply.readAll()).decode()
            return status_code, json.loads(response)
        except (UnicodeDecodeError, JSONDecodeError, ValueError) as err:
            error = CloudError(code = type(err).__name__, title = str(err), http_code = str(status_code),
                               id = str(time()), http_status = "500")
            Logger.logException("e", "Could not parse the stardust response: %s", error.toDict())
            return status_code, {"errors": [error.toDict()]}

    def _parseModels(self,
                     response: Dict[str, Any],
                     on_finished: Union[Callable[[CloudApiClientModel], Any],
                                        Callable[[List[CloudApiClientModel]], Any]],
                     model_class: Type[CloudApiClientModel],
                     pagination_manager: Optional[PaginationManager] = None) -> None:
        """Parses the given models and calls the correct callback depending on the result.

        :param response: The response from the server, after being converted to a dict.
        :param on_finished: The callback in case the response is successful.
        :param model_class: The type of the model to convert the response to. It may either be a single record or a list.
        :param pagination_manager: Holds the pagination links and metadata contained in paginated responses.
                                   If no pagination manager is provided, the pagination metadata is ignored.
        """

        if "data" in response:
            data = response["data"]
            if "meta" in response and pagination_manager:
                pagination_manager.setResponseMeta(response["meta"])
            if "links" in response and pagination_manager:
                pagination_manager.setLinks(response["links"])
            if isinstance(data, list):
                results = [model_class(**c) for c in data]  # type: List[CloudApiClientModel]
                on_finished_list = cast(Callable[[List[CloudApiClientModel]], Any], on_finished)
                on_finished_list(results)
            else:
                result = model_class(**data)  # type: CloudApiClientModel
                on_finished_item = cast(Callable[[CloudApiClientModel], Any], on_finished)
                on_finished_item(result)
        elif "errors" in response:
            self._on_error([CloudError(**error) for error in response["errors"]])
        else:
            Logger.log("e", "Cannot find data or errors in the cloud response: %s", response)

    def requestUpload3MF(self, request: DFLibraryFileUploadRequest,
                         on_finished: Callable[[DFLibraryFileUploadResponse], Any],
                         on_error: Optional[Callable[["QNetworkReply", "QNetworkReply.NetworkError"], None]] = None) -> None:

        """Requests the Digital Factory to register the upload of a file in a library project.

        :param request: The request object.
        :param on_finished: The function to be called after the result is parsed.
        :param on_error: The callback in case the request fails.
        """

        url = "{}/files/upload".format(self.CURA_API_ROOT)
        data = json.dumps({"data": request.toDict()}).encode()

        self._http.put(url,
                       scope = self._scope,
                       data = data,
                       callback = self._parseCallback(on_finished, DFLibraryFileUploadResponse),
                       error_callback = on_error,
                       timeout = self.DEFAULT_REQUEST_TIMEOUT)

    def requestUploadUFP(self, request: DFPrintJobUploadRequest,
                         on_finished: Callable[[DFPrintJobUploadResponse], Any],
                         on_error: Optional[Callable[["QNetworkReply", "QNetworkReply.NetworkError"], None]] = None) -> None:
        """Requests the Digital Factory to register the upload of a file in a library project.

        :param request: The request object.
        :param on_finished: The function to be called after the result is parsed.
        :param on_error: The callback in case the request fails.
        """

        url = "{}/jobs/upload".format(self.CURA_API_ROOT)
        data = json.dumps({"data": request.toDict()}).encode()

        self._http.put(url,
                       scope = self._scope,
                       data = data,
                       callback = self._parseCallback(on_finished, DFPrintJobUploadResponse),
                       error_callback = on_error,
                       timeout = self.DEFAULT_REQUEST_TIMEOUT)

    def uploadExportedFileData(self,
                               df_file_upload_response: Union[DFLibraryFileUploadResponse, DFPrintJobUploadResponse],
                               mesh: bytes,
                               on_finished: Callable[[str], Any],
                               on_success: Callable[[str], Any],
                               on_progress: Callable[[str, int], Any],
                               on_error: Callable[[str, "QNetworkReply", "QNetworkReply.NetworkError"], Any]) -> None:

        """Uploads an exported file (in bytes) to the Digital Factory Library.

        :param df_file_upload_response: The response received after requesting an upload with `self.requestUpload`.
        :param mesh: The mesh data (in bytes) to be uploaded.
        :param on_finished: The function to be called after the upload has finished. Called both after on_success and on_error.
                            It receives the name of the file that has finished uploading.
        :param on_success: The function to be called if the upload was successful.
                            It receives the name of the file that was uploaded successfully.
        :param on_progress: A function to be called during upload progress. It receives a percentage (0-100).
                            It receives the name of the file for which the upload progress should be updated.
        :param on_error: A function to be called if the upload fails.
                         It receives the name of the file that produced errors during the upload process.
        """

        self._file_uploader = DFFileUploader(self._http, df_file_upload_response, mesh, on_finished, on_success, on_progress, on_error)
        self._file_uploader.start()

    def createNewProject(self, project_name: str, on_finished: Callable[[DigitalFactoryProjectResponse], Any], on_error: Callable) -> None:
        """ Create a new project in the Digital Factory.

        :param project_name: Name of the new to be created project.
        :param on_finished: The function to be called after the result is parsed.
        :param on_error: The function to be called if anything goes wrong.
        """
        Logger.log("i", "Attempt to create new DF project '{}'.".format(project_name))

        url = "{}/projects".format(self.CURA_API_ROOT)
        data = json.dumps({"data": {"display_name": project_name}}).encode()
        self._http.put(url,
                       scope = self._scope,
                       data = data,
                       callback = self._parseCallback(on_finished, DigitalFactoryProjectResponse),
                       error_callback = on_error,
                       timeout = self.DEFAULT_REQUEST_TIMEOUT)

    def clear(self) -> None:
        if self._projects_pagination_mgr is not None:
            self._projects_pagination_mgr.reset()
