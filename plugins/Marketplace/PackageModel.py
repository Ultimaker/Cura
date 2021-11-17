# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, QObject
from typing import Any, Dict, Optional

from UM.Util import parseBool

from UM.i18n import i18nCatalog  # To translate placeholder names if data is not present.
catalog = i18nCatalog("cura")


class PackageModel(QObject):
    """
    Represents a package, containing all the relevant information to be displayed about a package.

    Effectively this behaves like a glorified named tuple, but as a QObject so that its properties can be obtained from
    QML. The model can also be constructed directly from a response received by the API.
    """

    def __init__(self, package_data: Dict[str, Any], section_title: Optional[str] = None, parent: Optional[QObject] = None) -> None:
        """
        Constructs a new model for a single package.
        :param package_data: The data received from the Marketplace API about the package to create.
        :param section_title: If the packages are to be categorized per section provide the section_title
        :param parent: The parent QML object that controls the lifetime of this model (normally a PackageList).
        """
        super().__init__(parent)
        self._package_id = package_data.get("package_id", "UnknownPackageId")
        self._icon_url = package_data.get("icon_url", "")
        self._display_name = package_data.get("display_name", catalog.i18nc("@label:property", "Unknown Package"))
        self._is_verified = "verified" in package_data.get("tags", [])
        self._package_version = package_data.get("package_version", "")  # Display purpose, no need for 'UM.Version'.
        self._package_info_url = package_data.get("website", "")  # Not to be confused with 'download_url'.
        self._download_count = package_data.get("download_count", 0)
        self._description = package_data.get("description", "")

        self._download_url = package_data.get("download_url", "")  # Not used yet, will be.
        self._release_notes = package_data.get("release_notes", "")  # Not used yet, propose to add to description?

        author_data = package_data.get("author", {})
        self._author_name = author_data.get("display_name", catalog.i18nc("@label:property", "Unknown Author"))
        self._author_info_url = author_data.get("website", "")

        self._section_title = section_title
        # Note that there's a lot more info in the package_data than just these specified here.

    @pyqtProperty(str, constant = True)
    def packageId(self) -> str:
        return self._package_id

    @pyqtProperty(str, constant=True)
    def iconUrl(self):
        return self._icon_url

    @pyqtProperty(str, constant = True)
    def displayName(self) -> str:
        return self._display_name

    @pyqtProperty(bool, constant=True)
    def isVerified(self):
        return self._is_verified

    @pyqtProperty(str, constant=True)
    def packageVersion(self):
        return self._package_version

    @pyqtProperty(str, constant=True)
    def packageInfoUrl(self):
        return self._package_info_url

    @pyqtProperty(int, constant=True)
    def downloadCount(self):
        return self._download_count

    @pyqtProperty(str, constant=True)
    def description(self):
        return self._description

    @pyqtProperty(str, constant=True)
    def authorName(self):
        return self._author_name

    @pyqtProperty(str, constant=True)
    def authorInfoUrl(self):
        return self._author_info_url

    @pyqtProperty(str, constant = True)
    def sectionTitle(self) -> Optional[str]:
        return self._section_title
