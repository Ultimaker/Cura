# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import re
from typing import Dict

from PyQt5.QtCore import Qt, pyqtProperty

from UM.Logger import Logger
from UM.Qt.ListModel import ListModel

from .ConfigsModel import ConfigsModel


from UM.PluginRegistry import PluginRegistry

##  Model that holds Cura packages. By setting the filter property the instances held by this model can be changed.
class SubscribedPackagesModel(ListModel):
    def __init__(self, parent = None):
        super().__init__(parent)

        # self._metadata = None

        self.addRoleName(Qt.UserRole + 1, "name")
        self.addRoleName(Qt.UserRole + 2, "icon_url")
        self.addRoleName(Qt.UserRole + 3, "is_compatible")


        # List of filters for queries. The result is the union of the each list of results.
        self._filter = {}  # type: Dict[str, str]
    #
    # def setMetadata(self, data):
    #     if self._metadata != data:
    #         self._metadata = data
    #         self._update()

    def update(self):
        print("---- in update function")
        items1 = []
        items2 = []

        # if self._metadata is None:
        #     Logger.logException("w", "Failed to load packages for Marketplace")
        #     self.setItems(items)
        #     return

        toolbox = PluginRegistry.getInstance().getPluginObject("Toolbox")
        print(toolbox.subscribed_compatible_packages)
        print(toolbox.subscribed_incompatible_packages)

        for incompatible in toolbox.subscribed_incompatible_packages:
            items1.append({
                "name": incompatible.package_id
            })

        for compatible in toolbox.subscribed_compatible_packages:
            items2.append({
                "name": compatible.package_id
            })
        print("======================0----------------------")
        print(items1)
        print(items2)

        # for package in self._metadata:
        #     has_configs = False
        #     configs_model = None
        #
        #     links_dict = {}
        #     if "data" in package:
        #         if "supported_configs" in package["data"]:
        #             if len(package["data"]["supported_configs"]) > 0:
        #                 has_configs = True
        #                 configs_model = ConfigsModel()
        #                 configs_model.setConfigs(package["data"]["supported_configs"])
        #
        #         # Links is a list of dictionaries with "title" and "url". Convert this list into a dict so it's easier
        #         # to process.
        #         link_list = package["data"]["links"] if "links" in package["data"] else []
        #         links_dict = {d["title"]: d["url"] for d in link_list}
        #
        #     if "author_id" not in package["author"] or "display_name" not in package["author"]:
        #         package["author"]["author_id"] = ""
        #         package["author"]["display_name"] = ""
        #
        #     items.append({
        #         "id":                   package["package_id"],
        #         "type":                 package["package_type"],
        #         "name":                 package["display_name"],
        #         "version":              package["package_version"],
        #         "author_id":            package["author"]["author_id"],
        #         "author_name":          package["author"]["display_name"],
        #         "author_email":         package["author"]["email"] if "email" in package["author"] else None,
        #         "description":          package["description"] if "description" in package else None,
        #         "icon_url":             package["icon_url"] if "icon_url" in package else None,
        #         "image_urls":           package["image_urls"] if "image_urls" in package else None,
        #         "download_url":         package["download_url"] if "download_url" in package else None,
        #         "last_updated":         package["last_updated"] if "last_updated" in package else None,
        #         "is_bundled":           package["is_bundled"] if "is_bundled" in package else False,
        #         "is_active":            package["is_active"] if "is_active" in package else False,
        #         "is_installed":         package["is_installed"] if "is_installed" in package else False,
        #         "has_configs":          has_configs,
        #         "supported_configs":    configs_model,
        #         "download_count":       package["download_count"] if "download_count" in package else 0,
        #         "tags":                 package["tags"] if "tags" in package else [],
        #         "links":                links_dict,
        #         "website":              package["website"] if "website" in package else None,
        #         "login_required":       "login-required" in package.get("tags", []),
        #         "average_rating":       float(package.get("rating", {}).get("average", 0)),
        #         "num_ratings":          package.get("rating", {}).get("count", 0),
        #         "user_rating":          package.get("rating", {}).get("user_rating", 0)
        #     })
        #
        # # Filter on all the key-word arguments.
        # for key, value in self._filter.items():
        #     if key == "tags":
        #         key_filter = lambda item, v = value: v in item["tags"]
        #     elif "*" in value:
        #         key_filter = lambda candidate, k = key, v = value: self._matchRegExp(candidate, k, v)
        #     else:
        #         key_filter = lambda candidate, k = key, v = value: self._matchString(candidate, k, v)
        #     items = filter(key_filter, items)
        #
        # # Execute all filters.
        # filtered_items = list(items)
        #
        # filtered_items.sort(key = lambda k: k["name"])
        # self.setItems(filtered_items)
        final_list = items1 + items2
        print(final_list)
        self.setItems(final_list)

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
