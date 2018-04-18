# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import re
from typing import Dict

from PyQt5.QtCore import Qt, pyqtProperty, pyqtSignal

from UM.Qt.ListModel import ListModel

##  Model that holds cura packages. By setting the filter property the instances held by this model can be changed.
class AuthorsModel(ListModel):
    def __init__(self, parent = None):
        super().__init__(parent)

        self._metadata = None

        self.addRoleName(Qt.UserRole + 1, "name")
        self.addRoleName(Qt.UserRole + 2, "email")
        self.addRoleName(Qt.UserRole + 3, "website")
        self.addRoleName(Qt.UserRole + 4, "type")
        self.addRoleName(Qt.UserRole + 5, "icon_url")
        self.addRoleName(Qt.UserRole + 6, "packages_count")

        # List of filters for queries. The result is the union of the each list of results.
        self._filter = {}  # type: Dict[str,str]

    def setMetadata(self, data):
        self._metadata = data
        self._update()

    def _update(self):
        items = []

        for author in self._metadata:
            items.append({
                "name": author["name"],
                "email": author["email"] if "email" in author else None,
                "website": author["website"],
                "type": author["type"] if "type" in author else None,
                "icon_url": author["icon_url"] if "icon_url" in author else None,
                "packages_count": author["packages_count"] if "packages_count" in author else 0
            })

        # Filter on all the key-word arguments.
        for key, value in self._filter.items():
            if "*" in value:
                key_filter = lambda candidate, key = key, value = value: self._matchRegExp(candidate, key, value)
            else:
                key_filter = lambda candidate, key = key, value = value: self._matchString(candidate, key, value)
            items = filter(key_filter, items)

        # Execute all filters.
        filtered_items = list(items)

        filtered_items.sort(key = lambda k: k["name"])
        self.setItems(filtered_items)

    ##  Set the filter of this model based on a string.
    #   \param filter_dict \type{Dict} Dictionary to do the filtering by.
    def setFilter(self, filter_dict: Dict[str, str]) -> None:
        if filter_dict != self._filter:
            self._filter = filter_dict
            self._update()

    @pyqtProperty("QVariantMap", fset = setFilter, constant = True)
    def filter(self) -> Dict[str, str]:
        return self._filter

    # Check to see if a container matches with a regular expression
    def _matchRegExp(self, metadata, property_name, value):
        if property_name not in metadata:
            return False
        value = re.escape(value) #Escape for regex patterns.
        value = "^" + value.replace("\\*", ".*") + "$" #Instead of (now escaped) asterisks, match on any string. Also add anchors for a complete match.
        if self._ignore_case:
            value_pattern = re.compile(value, re.IGNORECASE)
        else:
            value_pattern = re.compile(value)

        return value_pattern.match(str(metadata[property_name]))

    # Check to see if a container matches with a string
    def _matchString(self, metadata, property_name, value):
        if property_name not in metadata:
            return False
        return value.lower() == str(metadata[property_name]).lower()
