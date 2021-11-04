# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, Generator, List, Optional, TYPE_CHECKING
from PyQt5.QtCore import pyqtSlot, QObject

if TYPE_CHECKING:
    from PyQt5.QtCore import QObject

from UM.i18n import i18nCatalog

from cura.CuraApplication import CuraApplication

from .PackageList import PackageList
from .PackageModel import PackageModel  # The contents of this list.

catalog = i18nCatalog("cura")


class LocalPackageList(PackageList):
    PACKAGE_SECTION_HEADER = {
        "installed":
            {
                "plugin": catalog.i18nc("@label:property", "Installed Plugins"),
                "material": catalog.i18nc("@label:property", "Installed Materials")
            },
        "bundled":
            {
                "plugin": catalog.i18nc("@label:property", "Bundled Plugins"),
                "material": catalog.i18nc("@label:property", "Bundled Materials")
            }
    }  # The section headers to be used for the different package categories

    def __init__(self, parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)
        self._manager = CuraApplication.getInstance().getPackageManager()
        self._has_footer = False

    @pyqtSlot()
    def updatePackages(self) -> None:
        """Update the list with local packages, these are materials or plugin, either bundled or user installed. The list
        will also contain **to be removed** or **to be installed** packages since the user might still want to interact
        with these.
        """
        self.setErrorMessage("")  # Clear any previous errors.
        self.setIsLoading(True)
        self._getLocalPackages()
        self.setIsLoading(False)
        self.setHasMore(False)  # All packages should have been loaded at this time

    def _getLocalPackages(self) -> None:
        """ Obtain the local packages.

        The list is sorted per category as in  the order of the PACKAGE_SECTION_HEADER dictionary, whereas the packages
        for the sections are sorted alphabetically on the display name. These sorted sections are then added to the items
        """
        package_info = list(self._allPackageInfo())
        sorted_sections: List[Dict[str, PackageModel]] = []
        for section in self._getSections():
            packages = filter(lambda p: p.sectionTitle == section, package_info)
            sorted_sections.extend([{"package": p} for p in sorted(packages, key = lambda p: p.displayName)])
        self.setItems(sorted_sections)

    def _getSections(self) -> Generator[str, None, None]:
        """ Flatten and order the PACKAGE_SECTION_HEADER such that it can be used in obtaining the packages in the
        correct order"""
        for package_type in self.PACKAGE_SECTION_HEADER.values():
            for section in package_type.values():
                yield section

    def _allPackageInfo(self) -> Generator[PackageModel, None, None]:
        """ A generator which returns a unordered list of all the PackageModels"""

        # Get all the installed packages, add a section_title depending on package_type and user installed
        for packages in self._manager.getAllInstalledPackagesInfo().values():
            for package_info in packages:
                yield self._makePackageModel(package_info)

        # Get all to be removed package_info's. These packages are still used in the current session so the user might
        # still want to interact with these.
        for package_data in self._manager.getPackagesToRemove().values():
            yield self._makePackageModel(package_data["package_info"])

        # Get all to be installed package_info's. Since the user might want to interact with these
        for package_data in self._manager.getPackagesToInstall().values():
            yield self._makePackageModel(package_data["package_info"])

    def _makePackageModel(self, package_info: Dict[str, Any]) -> PackageModel:
        """ Create a PackageModel from the package_info and determine its section_title"""
        bundled_or_installed = "installed" if self._manager.isUserInstalledPackage(package_info["package_id"]) else "bundled"
        package_type = package_info["package_type"]
        section_title = self.PACKAGE_SECTION_HEADER[bundled_or_installed][package_type]
        return PackageModel(package_info, section_title = section_title, parent = self)
