# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from operator import attrgetter

from PyQt5.QtCore import pyqtSlot, QObject

if TYPE_CHECKING:
    from PyQt5.QtCore import QObject
    from PyQt5.QtNetwork import QNetworkReply

from UM.i18n import i18nCatalog
from UM.TaskManagement.HttpRequestManager import HttpRequestManager
from UM.Logger import Logger

from .PackageList import PackageList
from .PackageModel import PackageModel
from .Constants import PACKAGE_UPDATES_URL

catalog = i18nCatalog("cura")


class LocalPackageList(PackageList):
    PACKAGE_CATEGORIES = {
        "installed":
            {
                "plugin": catalog.i18nc("@label", "Installed Plugins"),
                "material": catalog.i18nc("@label", "Installed Materials")
            },
        "bundled":
            {
                "plugin": catalog.i18nc("@label", "Bundled Plugins"),
                "material": catalog.i18nc("@label", "Bundled Materials")
            }
    }  # The section headers to be used for the different package categories

    def __init__(self, parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)
        self._has_footer = False
        self._ongoing_requests["check_updates"] = None

    @pyqtSlot()
    def updatePackages(self) -> None:
        """Update the list with local packages, these are materials or plugin, either bundled or user installed. The list
        will also contain **to be removed** or **to be installed** packages since the user might still want to interact
        with these.
        """
        self.setErrorMessage("")  # Clear any previous errors.
        self.setIsLoading(True)

        # Obtain and sort the local packages
        self.setItems([{"package": p} for p in [self._makePackageModel(p) for p in self._manager.local_packages]])
        self.sort(attrgetter("sectionTitle", "can_update", "displayName"), key = "package", reverse = True)
        self.checkForUpdates(self._manager.local_packages)

        self.setIsLoading(False)
        self.setHasMore(False)  # All packages should have been loaded at this time

    def _makePackageModel(self, package_info: Dict[str, Any]) -> PackageModel:
        """ Create a PackageModel from the package_info and determine its section_title"""

        package_id = package_info["package_id"]
        bundled_or_installed = "bundled" if self._manager.isBundledPackage(package_id) else "installed"
        package_type = package_info["package_type"]
        section_title = self.PACKAGE_CATEGORIES[bundled_or_installed][package_type]
        package = PackageModel(package_info, section_title = section_title, parent = self)
        self._connectManageButtonSignals(package)
        package.can_downgrade = self._manager.canDowngrade(package_id)
        if package_id in self._manager.getPackagesToRemove() or package_id in self._manager.getPackagesToInstall():
            package.is_recently_installed = True
        return package

    def checkForUpdates(self, packages: List[Dict[str, Any]]):
        installed_packages = "installed_packages=".join([f"{package['package_id']}:{package['package_version']}&" for package in packages])
        request_url = f"{PACKAGE_UPDATES_URL}?installed_packages={installed_packages[:-1]}"

        self._ongoing_requests["check_updates"] = HttpRequestManager.getInstance().get(
            request_url,
            scope = self._scope,
            callback = self._parseResponse
        )

    def _parseResponse(self, reply: "QNetworkReply") -> None:
        """
        Parse the response from the package list API request which can update.

        :param reply: A reply containing information about a number of packages.
        """
        response_data = HttpRequestManager.readJSON(reply)
        if "data" not in response_data:
            Logger.error(
                f"Could not interpret the server's response. Missing 'data' from response data. Keys in response: {response_data.keys()}")
            return
        if len(response_data["data"]) == 0:
            return

        try:
            for package_data in response_data["data"]:
                package = self.getPackageModel(package_data["package_id"])
                package.download_url = package_data.get("download_url", "")
                package.can_update = True

            self.sort(attrgetter("sectionTitle", "can_update", "displayName"), key = "package", reverse = True)
            self._ongoing_requests["check_updates"] = None
        except RuntimeError:
            # Setting the ownership of this object to not qml can still result in a RuntimeError. Which can occur when quickly toggling
            # between de-/constructing RemotePackageLists. This try-except is here to prevent a hard crash when the wrapped C++ object
            # was deleted when it was still parsing the response
            return
