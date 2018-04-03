# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Dict

from PyQt5.QtCore import Qt, pyqtProperty, pyqtSignal

from UM.Qt.ListModel import ListModel

##  Model that holds cura packages. By setting the filter property the instances held by this model can be changed.
class CuraPackageModel(ListModel):
    IdRole = Qt.UserRole + 1
    TypeRole = Qt.UserRole + 2
    NameRole = Qt.UserRole + 3
    VersionRole = Qt.UserRole + 4
    AuthorRole = Qt.UserRole + 5
    DescriptionRole = Qt.UserRole + 6
    IconURLRole = Qt.UserRole + 7
    ImageURLsRole = Qt.UserRole + 8

    def __init__(self, parent = None):
        super().__init__(parent)

        self._packages_metadata = None

        self.addRoleName(CuraPackageModel.IdRole, "id")
        self.addRoleName(CuraPackageModel.TypeRole, "type")
        self.addRoleName(CuraPackageModel.NameRole, "name")
        self.addRoleName(CuraPackageModel.VersionRole, "version")
        self.addRoleName(CuraPackageModel.AuthorRole, "author")
        self.addRoleName(CuraPackageModel.DescriptionRole, "description")
        self.addRoleName(CuraPackageModel.IconURLRole, "icon_url")
        self.addRoleName(CuraPackageModel.ImageURLsRole, "image_urls")

        # List of filters for queries. The result is the union of the each list of results.
        self._filter = None  # type: Dict[str,str]

    def setPackagesMetaData(self, data):
        self._packages_metadata = data
        self._update()

    def _update(self):
        items = []

        for package in self._packages_metadata:
            items.append({
                "id": package["package_id"],
                "type": package["package_type"],
                "name": package["display_name"],
                "version": package["package_version"],
                "author": package["author"],
                "description": package["description"],
                "icon_url": package["icon_url"] if "icon_url" in package else None,
                "image_urls": package["image_urls"]
            })

        items.sort(key = lambda k: k["name"])
        self.setItems(items)

    filterChanged = pyqtSignal()

    ##  Set the filter of this model based on a string.
    #   \param filter_dict \type{Dict} Dictionary to do the filtering by.
    def setFilter(self, filter_dict: Dict[str, str]) -> None:
        if filter_dict != self._filter:
            self._filter = filter_dict
            self.filterChanged.emit()

    @pyqtProperty("QVariantMap", fset = setFilter, notify = filterChanged)
    def filter(self) -> Dict[str, str]:
        return self._filter
