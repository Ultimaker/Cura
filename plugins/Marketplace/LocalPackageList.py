# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtSlot, Qt
from typing import Any, Dict, Generator, TYPE_CHECKING

from UM.i18n import i18nCatalog

from cura.CuraApplication import CuraApplication

from .PackageList import PackageList
from .PackageModel import PackageModel  # The contents of this list.

if TYPE_CHECKING:
    from PyQt5.QtCore import QObject

catalog = i18nCatalog("cura")


class LocalPackageList(PackageList):
    PackageRole = Qt.UserRole + 1
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

    def __init__(self, parent: "QObject" = None) -> None:
        super().__init__(parent)
        self._application = CuraApplication.getInstance()
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
        self.setIsLoading(True)

    def _getLocalPackages(self) -> None:
        """ Obtain the local packages.
        The list is sorted per category as in  the order of the PACKAGE_SECTION_HEADER dictionary, whereas the packages
        for the sections are sorted alphabetically on the display name
        """

        sorted_sections = {}
        # Filter the package list per section_title and sort these
        for section in self._getSections():
            packages = filter(lambda p: p["section_title"] == section, self._allPackageInfo())
            sorted_sections[section] = sorted(packages, key = lambda p: p["display_name"])

        # Create a PackageModel from the sorted package_info and append them to the list
        for section in sorted_sections.values():
            for package_data in section:
                package = PackageModel(package_data, parent = self)
                self.appendItem({"package": package})

        self.setIsLoading(False)
        self.setHasMore(False)  # All packages should have been loaded at this time

    def _getSections(self) -> Generator[str]:
        """ Flatten and order the PACKAGE_SECTION_HEADER such that it can be used in obtaining the packages in the
        correct order"""
        for package_type in self.PACKAGE_SECTION_HEADER.values():
            for section in package_type.values():
                yield section

    def _allPackageInfo(self) -> Generator[Dict[str, Any]]:
        """ A generator which returns a unordered list of package_info, the section_title is appended to the each
        package_info"""

        manager = self._application.getPackageManager()

        # Get all the installed packages, add a section_title depending on package_type and user installed
        for package_type, packages in manager.getAllInstalledPackagesInfo().items():
            for package_data in packages:
                bundled_or_installed = "installed" if manager.isUserInstalledPackage(package_data["package_id"]) else "bundled"
                package_data["section_title"] = self.PACKAGE_SECTION_HEADER[bundled_or_installed][package_type]
                yield package_data

        # Get all to be removed package_info's. These packages are still used in the current session so the user might
        # to interact with these in the list
        for package_data in manager.getPackagesToRemove().values():
            yield package_data["package_info"]

        for package_data in manager.getPackagesToInstall().values():
            package_info = package_data["package_info"]
            package_type = package_info["package_type"]
            package_info["section_title"] = self.PACKAGE_SECTION_HEADER["installed"][package_type]
            yield package_info
