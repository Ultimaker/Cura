# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt
from UM.Qt.ListModel import ListModel
from cura import ApplicationMetadata


class SubscribedPackagesModel(ListModel):
    def __init__(self, parent = None):
        super().__init__(parent)

        self._items = []
        self._metadata = None
        self._discrepancies = None
        self._sdk_version = ApplicationMetadata.CuraSDKVersion

        self.addRoleName(Qt.UserRole + 1, "name")
        self.addRoleName(Qt.UserRole + 2, "icon_url")
        self.addRoleName(Qt.UserRole + 3, "is_compatible")

    def setMetadata(self, data):
        if self._metadata != data:
            self._metadata = data

    def addValue(self, discrepancy):
        if self._discrepancies != discrepancy:
            self._discrepancies = discrepancy

    def update(self):
        self._items.clear()

        for item in self._metadata:
            if item["package_id"] not in self._discrepancies:
                continue
            package = {"name": item["display_name"], "sdk_versions": item["sdk_versions"]}
            if self._sdk_version not in item["sdk_versions"]:
                package.update({"is_compatible": False})
            else:
                package.update({"is_compatible": True})
            try:
                package.update({"icon_url": item["icon_url"]})
            except KeyError:  # There is no 'icon_url" in the response payload for this package
                package.update({"icon_url": ""})

            self._items.append(package)
        self.setItems(self._items)
        print(self._items)

    def has_compatible_packages(self):
        has_compatible_items  = False
        for item in self._items:
            if item['is_compatible'] == True:
                has_compatible_items = True
        return has_compatible_items

    def has_incompatible_packages(self):
        has_incompatible_items  = False
        for item in self._items:
            if item['is_compatible'] == False:
                has_incompatible_items = True
        return has_incompatible_items