# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot
from PyQt5.QtNetwork import QNetworkReply
from typing import Optional, TYPE_CHECKING

from cura.CuraApplication import CuraApplication
from cura.UltimakerCloud.UltimakerCloudScope import UltimakerCloudScope  # To make requests to the Ultimaker API with correct authorization.
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.TaskManagement.HttpRequestManager import HttpRequestManager, HttpRequestData  # To request the package list from the API.
from UM.TaskManagement.HttpRequestScope import JsonDecoratorScope  # To request JSON responses from the API.

from . import Marketplace   # To get the list of packages. Imported this way to prevent circular imports.
from .PackageList import PackageList
from .PackageModel import PackageModel  # The contents of this list.

if TYPE_CHECKING:
    from PyQt5.QtCore import QObject

catalog = i18nCatalog("cura")


class RemotePackageList(PackageList):
    ITEMS_PER_PAGE = 20  # Pagination of number of elements to download at once.

    def __init__(self, parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)

        self._ongoing_request: Optional[HttpRequestData] = None
        self._scope = JsonDecoratorScope(UltimakerCloudScope(CuraApplication.getInstance()))

        self._package_type_filter = ""
        self._request_url = self._initialRequestUrl()
        self.isLoadingChanged.emit()

    def __del__(self) -> None:
        """
        When deleting this object, abort the request so that we don't get a callback from it later on a deleted C++
        object.
        """
        self.abortUpdating()

    @pyqtSlot()
    def updatePackages(self) -> None:
        """
        Make a request for the first paginated page of packages.

        When the request is done, the list will get updated with the new package models.
        """
        self.setErrorMessage("")  # Clear any previous errors.
        self.setIsLoading(True)

        self._ongoing_request = HttpRequestManager.getInstance().get(
            self._request_url,
            scope = self._scope,
            callback = self._parseResponse,
            error_callback = self._onError
        )

    @pyqtSlot()
    def abortUpdating(self) -> None:
        HttpRequestManager.getInstance().abortRequest(self._ongoing_request)
        self._ongoing_request = None

    def reset(self) -> None:
        self.clear()
        self._request_url = self._initialRequestUrl()

    packageTypeFilterChanged = pyqtSignal()

    def setPackageTypeFilter(self, new_filter: str) -> None:
        if new_filter != self._package_type_filter:
            self._package_type_filter = new_filter
            self.reset()
            self.packageTypeFilterChanged.emit()

    @pyqtProperty(str, fset = setPackageTypeFilter, notify = packageTypeFilterChanged)
    def packageTypeFilter(self) -> str:
        """
        Get the package type this package list is filtering on, like ``plugin`` or ``material``.
        :return: The package type this list is filtering on.
        """
        return self._package_type_filter

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
            try:
                package = PackageModel(package_data, parent = self)
                self.appendItem({"package": package})  # Add it to this list model.
            except RuntimeError:
                # Setting the ownership of this object to not qml can still result in a RuntimeError. Which can occur when quickly toggling
                # between de-/constructing RemotePackageLists. This try-except is here to prevent a hard crash when the wrapped C++ object
                # was deleted when it was still parsing the response
                return

        self._request_url = response_data["links"].get("next", "")  # Use empty string to signify that there is no next page.
        self._ongoing_request = None
        self.setIsLoading(False)
        self.setHasMore(self._request_url != "")

    def _onError(self, reply: "QNetworkReply", error: Optional[QNetworkReply.NetworkError]) -> None:
        """
        Handles networking and server errors when requesting the list of packages.
        :param reply: The reply with packages. This will most likely be incomplete and should be ignored.
        :param error: The error status of the request.
        """
        if error == QNetworkReply.NetworkError.OperationCanceledError:
            Logger.debug("Cancelled request for packages.")
            self._ongoing_request = None
            return  # Don't show an error about this to the user.
        Logger.error("Could not reach Marketplace server.")
        self.setErrorMessage(catalog.i18nc("@info:error", "Could not reach Marketplace."))
        self._ongoing_request = None
        self.setIsLoading(False)
