#  Copyright (c) 2021 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtCore import pyqtProperty, pyqtSignal, pyqtSlot
from PyQt6.QtNetwork import QNetworkReply
from typing import Optional, TYPE_CHECKING

from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.TaskManagement.HttpRequestManager import HttpRequestManager  # To request the package list from the API.

from .Constants import PACKAGES_URL   # To get the list of packages. Imported this way to prevent circular imports.
from .PackageList import PackageList
from .PackageModel import PackageModel  # The contents of this list.

if TYPE_CHECKING:
    from PyQt6.QtCore import QObject

catalog = i18nCatalog("cura")


class RemotePackageList(PackageList):
    ITEMS_PER_PAGE = 20  # Pagination of number of elements to download at once.
    SORT_TYPE = "last_updated"   # Default value to send for sort_by filter.

    def __init__(self, parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)

        self._package_type_filter = ""
        self._requested_search_string = ""
        self._current_search_string = ""
        self._search_sort = "sort_by"
        self._search_type = "search"
        self._request_url = self._initialRequestUrl()
        self._ongoing_requests["get_packages"] = None
        self.isLoadingChanged.connect(self._onLoadingChanged)
        self.isLoadingChanged.emit()

    @pyqtSlot()
    def updatePackages(self) -> None:
        """
        Make a request for the first paginated page of packages.

        When the request is done, the list will get updated with the new package models.
        """
        self.setErrorMessage("")  # Clear any previous errors.
        self.setIsLoading(True)

        self._ongoing_requests["get_packages"] = HttpRequestManager.getInstance().get(
            self._request_url,
            scope = self._scope,
            callback = self._parseResponse,
            error_callback = self._onError
        )

    def reset(self) -> None:
        self.clear()
        self._request_url = self._initialRequestUrl()

    packageTypeFilterChanged = pyqtSignal()
    searchStringChanged = pyqtSignal()

    def setPackageTypeFilter(self, new_filter: str) -> None:
        if new_filter != self._package_type_filter:
            self._package_type_filter = new_filter
            self.reset()
            self.packageTypeFilterChanged.emit()

    def setSearchString(self, new_search: str) -> None:
        self._requested_search_string = new_search
        self._onLoadingChanged()

    @pyqtProperty(str, fset = setPackageTypeFilter, notify = packageTypeFilterChanged)
    def packageTypeFilter(self) -> str:
        """
        Get the package type this package list is filtering on, like ``plugin`` or ``material``.
        :return: The package type this list is filtering on.
        """
        return self._package_type_filter

    @pyqtProperty(str, fset = setSearchString, notify = searchStringChanged)
    def searchString(self) -> str:
        """
        Get the string the user is currently searching for (as in: the list is updating) within the packages,
        or an empty string if no extra search filter has to be applied. Does not override package-type filter!
        :return: String the user is searching for. Empty denotes 'no search filter'.
        """
        return self._current_search_string

    def _onLoadingChanged(self) -> None:
        if self._requested_search_string != self._current_search_string and not self._is_loading:
            self._current_search_string = self._requested_search_string
            self.reset()
            self.updatePackages()
            self.searchStringChanged.emit()

    def _initialRequestUrl(self) -> str:
        """
        Get the URL to request the first paginated page with.
        :return: A URL to request.
        """
        request_url = f"{PACKAGES_URL}?limit={self.ITEMS_PER_PAGE}"
        if self._package_type_filter != "":
            request_url += f"&package_type={self._package_type_filter}"
        if self._current_search_string != "":
            request_url += f"&{self._search_type}={self._current_search_string}"
        if self.SORT_TYPE:
            request_url += f"&{self._search_sort}={self.SORT_TYPE}"
        return request_url

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
                self._connectManageButtonSignals(package)
                self.appendItem({"package": package})  # Add it to this list model.
            except RuntimeError:
                # Setting the ownership of this object to not qml can still result in a RuntimeError. Which can occur when quickly toggling
                # between de-/constructing RemotePackageLists. This try-except is here to prevent a hard crash when the wrapped C++ object
                # was deleted when it was still parsing the response
                continue

        self._request_url = response_data["links"].get("next", "")  # Use empty string to signify that there is no next page.
        self._ongoing_requests["get_packages"] = None
        self.setIsLoading(False)
        self.setHasMore(self._request_url != "")

    def _onError(self, reply: "QNetworkReply", error: Optional[QNetworkReply.NetworkError]) -> None:
        """
        Handles networking and server errors when requesting the list of packages.
        :param reply: The reply with packages. This will most likely be incomplete and should be ignored.
        :param error: The error status of the request.
        """
        if error == QNetworkReply.NetworkError.OperationCanceledError or error == QNetworkReply.NetworkError.ProtocolUnknownError:
            Logger.debug("Cancelled request for packages.")
            self._ongoing_requests["get_packages"] = None
            self.setIsLoading(False)
            return  # Don't show an error about this to the user.
        Logger.error("Could not reach Marketplace server.")
        self.setErrorMessage(catalog.i18nc("@info:error", "Could not reach Marketplace."))
        self._ongoing_requests["get_packages"] = None
        self.setIsLoading(False)
