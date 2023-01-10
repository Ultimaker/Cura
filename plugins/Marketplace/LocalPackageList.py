#  Copyright (c) 2022 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from PyQt6.QtCore import pyqtSlot, QObject

from UM.Version import Version
from UM.i18n import i18nCatalog
from UM.TaskManagement.HttpRequestManager import HttpRequestManager
from UM.Logger import Logger

from .PackageList import PackageList
from .PackageModel import PackageModel
from .Constants import PACKAGE_UPDATES_URL

if TYPE_CHECKING:
    from PyQt6.QtCore import QObject
    from PyQt6.QtNetwork import QNetworkReply

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
        self._package_manager.packagesWithUpdateChanged.connect(self._sortSectionsOnUpdate)
        self._package_manager.packageUninstalled.connect(self._removePackageModel)

    def _sortSectionsOnUpdate(self) -> None:
        section_order = dict(zip([i for k, v in self.PACKAGE_CATEGORIES.items() for i in self.PACKAGE_CATEGORIES[k].values()], ["a", "b", "c", "d"]))
        self.sort(lambda model: (section_order[model.sectionTitle], not model.canUpdate, model.displayName.lower()), key = "package")

    def _removePackageModel(self, package_id: str) -> None:
        """
        Cleanup function to remove the package model from the list. Note that this is only done if the package can't
        be updated, it is in the to remove list and isn't in the to be installed list
        """
        package = self.getPackageModel(package_id)

        if package and not package.canUpdate and \
                package_id in self._package_manager.getToRemovePackageIDs() and \
                package_id not in self._package_manager.getPackagesToInstall():
            index = self.find("package", package_id)
            if index < 0:
                Logger.error(f"Could not find card in Listview corresponding with {package_id}")
                self.updatePackages()
                return
            self.removeItem(index)

    @pyqtSlot()
    def updatePackages(self) -> None:
        """Update the list with local packages, these are materials or plugin, either bundled or user installed. The list
        will also contain **to be removed** or **to be installed** packages since the user might still want to interact
        with these.
        """
        self.setErrorMessage("")  # Clear any previous errors.
        self.setIsLoading(True)

        # Obtain and sort the local packages
        self.setItems([{"package": p} for p in [self._makePackageModel(p) for p in self._package_manager.local_packages]])
        self._sortSectionsOnUpdate()
        self.checkForUpdates(self._package_manager.local_packages)

        self.setIsLoading(False)
        self.setHasMore(False)  # All packages should have been loaded at this time

    def _makePackageModel(self, package_info: Dict[str, Any]) -> PackageModel:
        """ Create a PackageModel from the package_info and determine its section_title"""

        package_id = package_info["package_id"]
        bundled_or_installed = "bundled" if self._package_manager.isBundledPackage(package_id) else "installed"
        package_type = package_info["package_type"]
        section_title = self.PACKAGE_CATEGORIES[bundled_or_installed][package_type]
        package = PackageModel(package_info, section_title = section_title, parent = self)
        self._connectManageButtonSignals(package)
        return package

    def checkForUpdates(self, packages: List[Dict[str, Any]]) -> None:
        installed_packages = "&".join([f"installed_packages={package['package_id']}:{package['package_version']}" for package in packages])
        request_url = f"{PACKAGE_UPDATES_URL}?{installed_packages}"

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
        if response_data is None or "data" not in response_data:
            Logger.error(
                f"Could not interpret the server's response. Missing 'data' from response data. Keys in response: {response_data.keys()}")
            return
        if len(response_data["data"]) == 0:
            return

        packages = response_data["data"]
        for package in packages:
            self._package_manager.addAvailablePackageVersion(package["package_id"], Version(package["package_version"]))
            package_model = self.getPackageModel(package["package_id"])
            if package_model:
                # Also make sure that the local list knows where to get an update
                package_model.setDownloadUrl(package["download_url"])

        self._ongoing_requests["check_updates"] = None
