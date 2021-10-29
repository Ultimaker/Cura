# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtNetwork import QNetworkReply
from typing import Optional, TYPE_CHECKING

from cura.CuraApplication import CuraApplication
from cura.UltimakerCloud.UltimakerCloudScope import UltimakerCloudScope  # To make requests to the Ultimaker API with correct authorization.
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Qt.ListModel import ListModel
from UM.TaskManagement.HttpRequestManager import HttpRequestManager, HttpRequestData  # To request the package list from the API.
from UM.TaskManagement.HttpRequestScope import JsonDecoratorScope  # To request JSON responses from the API.

from . import Marketplace   # To get the list of packages. Imported this way to prevent circular imports.
from .PackageModel import PackageModel  # The contents of this list.

if TYPE_CHECKING:
    from PyQt5.QtCore import QObject

catalog = i18nCatalog("cura")


class PackageList(ListModel):
    """
    Represents a list of packages to be displayed in the interface.

    The list can be filtered (e.g. on package type, materials vs. plug-ins) and
    paginated.
    """

    PackageRole = Qt.UserRole + 1

    ITEMS_PER_PAGE = 20  # Pagination of number of elements to download at once.

    def __init__(self, parent: "QObject" = None) -> None:
        super().__init__(parent)

        self._ongoing_request: Optional[HttpRequestData] = None
        self._scope = JsonDecoratorScope(UltimakerCloudScope(CuraApplication.getInstance()))
        self._error_message = ""

        self._package_type_filter = ""
        self._request_url = self._initialRequestUrl()

        self.addRoleName(self.PackageRole, "package")

    def __del__(self) -> None:
        """
        When deleting this object, abort the request so that we don't get a callback from it later on a deleted C++
        object.
        """
        self.abortRequest()

    @pyqtSlot()
    def request(self) -> None:
        """
        Make a request for the first paginated page of packages.

        When the request is done, the list will get updated with the new package models.
        """
        self.setErrorMessage("")  # Clear any previous errors.

        http = HttpRequestManager.getInstance()
        self._ongoing_request = http.get(
            self._request_url,
            scope = self._scope,
            callback = self._parseResponse,
            error_callback = self._onError
        )
        self.isLoadingChanged.emit()

    @pyqtSlot()
    def abortRequest(self) -> None:
        HttpRequestManager.getInstance().abortRequest(self._ongoing_request)
        self._ongoing_request = None

    def reset(self) -> None:
        self.clear()
        self._request_url = self._initialRequestUrl()

    isLoadingChanged = pyqtSignal()

    @pyqtProperty(bool, notify = isLoadingChanged)
    def isLoading(self) -> bool:
        """
        Gives whether the list is currently loading the first page or loading more pages.
        :return: ``True`` if the list is downloading, or ``False`` if not downloading.
        """
        return self._ongoing_request is not None

    hasMoreChanged = pyqtSignal()

    @pyqtProperty(bool, notify = hasMoreChanged)
    def hasMore(self) -> bool:
        """
        Returns whether there are more packages to load.
        :return: ``True`` if there are more packages to load, or ``False`` if we've reached the last page of the
        pagination.
        """
        return self._request_url != ""

    packageTypeFilterChanged = pyqtSignal()

    def setPackageTypeFilter(self, new_filter: str) -> None:
        if new_filter != self._package_type_filter:
            self._package_type_filter = new_filter
            self.reset()
            self.packageTypeFilterChanged.emit()

    @pyqtProperty(str, notify = packageTypeFilterChanged, fset = setPackageTypeFilter)
    def packageTypeFilter(self) -> str:
        """
        Get the package type this package list is filtering on, like ``plugin`` or ``material``.
        :return: The package type this list is filtering on.
        """
        return self._package_type_filter

    def setErrorMessage(self, error_message: str) -> None:
        if self._error_message != error_message:
            self._error_message = error_message
            self.errorMessageChanged.emit()

    errorMessageChanged = pyqtSignal()

    @pyqtProperty(str, notify = errorMessageChanged, fset = setErrorMessage)
    def errorMessage(self) -> str:
        """
        If an error occurred getting the list of packages, an error message will be held here.

        If no error occurred (yet), this will be an empty string.
        :return: An error message, if any, or an empty string if everything went okay.
        """
        return self._error_message

    def _initialRequestUrl(self) -> str:
        """
        Get the URL to request the first paginated page with.
        :return: A URL to request.
        """
        if self._package_type_filter != "":
            return f"{Marketplace.PACKAGES_URL}?package_type={self._package_type_filter}&limit={self.ITEMS_PER_PAGE}"
        return f"{Marketplace.PACKAGES_URL}?limit={self.ITEMS_PER_PAGE}"

    def _parseResponse(self, reply: "QNetworkReply") -> None:
        """
        Parse the response from the package list API request.

        This converts that response into PackageModels, and triggers the ListModel to update.
        :param reply: A reply containing information about a number of packages.
        """
        response_data = HttpRequestManager.readJSON(reply)
        if "data" not in response_data or "links" not in response_data:
            Logger.error(f"Could not interpret the server's response. Missing 'data' or 'links' from response data. Keys in response: {response_data.keys()}")
            self.setErrorMessage(catalog.i18nc("@info:error", "Could not interpret the server's response."))
            return

        for package_data in response_data["data"]:
            package = PackageModel(package_data, parent = self)
            self.appendItem({"package": package})  # Add it to this list model.

        self._request_url = response_data["links"].get("next", "")  # Use empty string to signify that there is no next page.
        self.hasMoreChanged.emit()
        self._ongoing_request = None
        self.isLoadingChanged.emit()

    def _onError(self, reply: "QNetworkReply", error: Optional[QNetworkReply.NetworkError]) -> None:
        """
        Handles networking and server errors when requesting the list of packages.
        :param reply: The reply with packages. This will most likely be incomplete and should be ignored.
        :param error: The error status of the request.
        """
        if error == QNetworkReply.NetworkError.OperationCanceledError:
            Logger.error("Cancelled request for packages.")
            self._ongoing_request = None
            return  # Don't show an error about this to the user.
        Logger.error("Could not reach Marketplace server.")
        self.setErrorMessage(catalog.i18nc("@info:error", "Could not reach Marketplace."))
        self._ongoing_request = None
        self.isLoadingChanged.emit()
