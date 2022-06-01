#  Copyright (c) 2022 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, TYPE_CHECKING, Dict, List

from .Constants import PACKAGES_URL
from .PackageModel import PackageModel
from .RemotePackageList import RemotePackageList
from PyQt6.QtCore import pyqtSignal, QObject, pyqtProperty, QCoreApplication

from UM.TaskManagement.HttpRequestManager import HttpRequestManager  # To request the package list from the API.
from UM.i18n import i18nCatalog

if TYPE_CHECKING:
    from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal

catalog = i18nCatalog("cura")

class MissingPackageList(RemotePackageList):
    def __init__(self, parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)
        self._package_metadata: List[Dict[str, str]] = []
        # self.packageTypeFilter = None # This will be our new filter
        self._package_type_filter = "material"

    def setPackageIds(self, packages: List[Dict[str, str]]) -> None:
        self._package_metadata = packages
        search_string = ", ".join(map(lambda package: package["id"], packages))
        # self.setSearchString(search_string)
        self.setSearchString("ABS")


