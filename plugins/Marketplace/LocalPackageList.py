# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtSlot, Qt
from typing import TYPE_CHECKING

from UM.i18n import i18nCatalog

from cura.CuraApplication import CuraApplication

from .PackageList import PackageList
from .PackageModel import PackageModel  # The contents of this list.

if TYPE_CHECKING:
    from PyQt5.QtCore import QObject

catalog = i18nCatalog("cura")


class LocalPackageList(PackageList):
    PackageRole = Qt.UserRole + 1

    def __init__(self, parent: "QObject" = None) -> None:
        super().__init__(parent)
        self._application = CuraApplication.getInstance()

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
        plugin_registry = self._application.getPluginRegistry()
        package_manager = self._application.getPackageManager()

        bundled = plugin_registry.getInstalledPlugins()
        for b in bundled:
            package = PackageModel({"package_id": b, "display_name": b, "section_title": "bundled"}, parent = self)
            self.appendItem({"package": package})
        packages = package_manager.getInstalledPackageIDs()
        for p in packages:
            package = PackageModel({"package_id": p, "display_name": p, "section_title": "package"}, parent = self)
            self.appendItem({"package": package})
        self.setIsLoading(False)
        self.setHasMore(False)
