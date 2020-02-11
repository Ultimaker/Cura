# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt, pyqtProperty, pyqtSlot

from UM.PackageManager import PackageManager
from UM.Qt.ListModel import ListModel
from UM.Version import Version

from cura import ApplicationMetadata
from typing import List, Dict, Any


class SubscribedPackagesModel(ListModel):
    def __init__(self, parent = None):
        super().__init__(parent)

        self._items = []
        self._metadata = None
        self._discrepancies = None
        self._sdk_version = ApplicationMetadata.CuraSDKVersion

        self.addRoleName(Qt.UserRole + 1, "package_id")
        self.addRoleName(Qt.UserRole + 2, "display_name")
        self.addRoleName(Qt.UserRole + 3, "icon_url")
        self.addRoleName(Qt.UserRole + 4, "is_compatible")
        self.addRoleName(Qt.UserRole + 5, "is_dismissed")

    @pyqtProperty(bool, constant=True)
    def hasCompatiblePackages(self) -> bool:
        for item in self._items:
            if item['is_compatible']:
                return True
        return False

    @pyqtProperty(bool, constant=True)
    def hasIncompatiblePackages(self) -> bool:
        for item in self._items:
            if not item['is_compatible']:
                return True
        return False

    def addDiscrepancies(self, discrepancy: List[str]) -> None:
        self._discrepancies = discrepancy

    def getCompatiblePackages(self) -> List[Dict[str, Any]]:
        return [package for package in self._items if package["is_compatible"]]

    def getIncompatiblePackages(self) -> List[str]:
        return [package["package_id"] for package in self._items if not package["is_compatible"]]

    def initialize(self, package_manager: PackageManager, subscribed_packages_payload: List[Dict[str, Any]]) -> None:
        self._items.clear()
        for item in subscribed_packages_payload:
            if item["package_id"] not in self._discrepancies:
                continue
            package = {
                "package_id": item["package_id"],
                "display_name": item["display_name"],
                "sdk_versions": item["sdk_versions"],
                "download_url": item["download_url"],
                "md5_hash": item["md5_hash"],
                "is_dismissed": False,
            }

            package.update({"is_compatible": self._isAnyVersionCompatible(package_manager, item["sdk_versions"])})

            try:
                package.update({"icon_url": item["icon_url"]})
            except KeyError:  # There is no 'icon_url" in the response payload for this package
                package.update({"icon_url": ""})
            self._items.append(package)
        self.setItems(self._items)

    @staticmethod
    def _isAnyVersionCompatible(package_manager: PackageManager, api_versions: [str]) -> bool:
        """
        Check a list of version numbers if any of them applies to our
        application.
        :return: ``True`` when any of the provided API versions is compatible.
        """
        return any(package_manager.isPackageCompatible(Version(version)) for version in api_versions)
