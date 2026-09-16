#  Copyright (c) 2022 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, TYPE_CHECKING, Dict, List

from .PackageModel import PackageModel
from .RemotePackageList import RemotePackageList
from PyQt6.QtCore import pyqtSignal, QObject, pyqtProperty, QCoreApplication

from UM.i18n import i18nCatalog

if TYPE_CHECKING:
    from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal

catalog = i18nCatalog("cura")

class MissingPackageList(RemotePackageList):
    def __init__(self, packages_metadata: List[Dict[str, str]], parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)
        self._packages_metadata: List[Dict[str, str]] = packages_metadata
        self._search_type = "package_ids"
        self._requested_search_string = ",".join(map(lambda package: package["id"], packages_metadata))

    def _parseResponse(self, reply: "QNetworkReply") -> None:
        super()._parseResponse(reply)

        # At the end of the list we want to show some information about packages the user is missing that can't be found
        # This will add cards with some information about the missing packages
        if not self.hasMore:
            self._addPackagesMissingFromRequest()

    def _addPackagesMissingFromRequest(self) -> None:
        """Create cards for packages the user needs to install that could not be found"""
        returned_packages_ids = [item["package"].packageId for item in self._items]

        for package_metadata in self._packages_metadata:
            if package_metadata["id"] not in returned_packages_ids:
                package_type = package_metadata["type"] if "type" in package_metadata else "material"
                # When this feature was originally introduced only missing materials were detected. With the inclusion
                # of backend plugins this system was extended to also detect missing plugins. With that change the type
                # of the package was added to the metadata. Project files before this change do not have this type. So
                # if the type is not present we assume it is a material.
                package = PackageModel.fromIncompletePackageInformation(package_metadata["display_name"],
                                                                        package_metadata["package_version"],
                                                                        package_type)
                self.appendItem({"package": package})

        self.itemsChanged.emit()


