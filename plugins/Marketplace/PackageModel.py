# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, QObject
from typing import Any, Dict, Optional

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
        self._display_name = package_data.get("display_name", catalog.i18nc("@label:property", "Unknown Package"))
        self._section_title = section_title

    @pyqtProperty(str, constant = True)
    def packageId(self) -> str:
        return self._package_id

    @pyqtProperty(str, constant = True)
    def displayName(self) -> str:
        return self._display_name

    @pyqtProperty(str, constant = True)
    def sectionTitle(self) -> Optional[str]:
        return self._section_title
