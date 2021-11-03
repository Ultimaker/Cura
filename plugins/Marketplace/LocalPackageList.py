# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtSlot, Qt
from typing import TYPE_CHECKING

from UM.i18n import i18nCatalog
from UM.Logger import Logger

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
        }

    def __init__(self, parent: "QObject" = None) -> None:
        super().__init__(parent)
        self._application = CuraApplication.getInstance()
        self._has_footer = False

    @pyqtSlot()
    def updatePackages(self) -> None:
        """
        Make a request for the first paginated page of packages.

        When the request is done, the list will get updated with the new package models.
        """
        self.setErrorMessage("")  # Clear any previous errors.
        self.setIsLoading(True)
        self._getLocalPackages()

    def _getLocalPackages(self) -> None:
        sorted_sections = {}
        for section in self._getSections():
            packages = filter(lambda p: p["section_title"] == section, self._allPackageInfo())
            sorted_sections[section] = sorted(packages, key = lambda p: p["display_name"])

        for section in sorted_sections.values():
            for package_data in section:
                package = PackageModel(package_data, parent = self)
                self.appendItem({"package": package})

        self.setIsLoading(False)
        self.setHasMore(False)

    def _getSections(self):
        for package_type in self.PACKAGE_SECTION_HEADER.values():
            for section in package_type.values():
                yield section

    def _allPackageInfo(self):
        manager = self._application.getPackageManager()
        for package_type, packages in manager.getAllInstalledPackagesInfo().items():
            for package_data in packages:
                bundled_or_installed = "installed" if manager.isUserInstalledPackage(package_data["package_id"]) else "bundled"
                package_data["section_title"] = self.PACKAGE_SECTION_HEADER[bundled_or_installed][package_type]
                yield package_data

        for package_data in manager.getPackagesToRemove().values():
            yield package_data["package_info"]

        for package_data in manager.getPackagesToInstall().values():
            package_info = package_data["package_info"]
            package_type = package_info["package_type"]
            package_info["section_title"] = self.PACKAGE_SECTION_HEADER["installed"][package_type]
            yield package_info
