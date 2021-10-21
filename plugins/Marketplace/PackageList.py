# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, Qt
from typing import List, TYPE_CHECKING
from UM.Qt.ListModel import ListModel

from .PackageModel import PackageModel  # This list is a list of PackageModels.

if TYPE_CHECKING:
    from PyQt5.QtCore import QObject

class PackageList(ListModel):
    """
    Represents a list of packages to be displayed in the interface.

    The list can be filtered (e.g. on package type, materials vs. plug-ins) and
    paginated.
    """

    PackageRole = Qt.UserRole + 1

    ITEMS_PER_PAGE = 20  # Pagination of number of elements to download at once.

    def __init__(self, parent: "QObject" = None):
        super().__init__(parent)

        self._packages: List[PackageModel] = []
        self.setIsLoading(True)

        self.requestFirst()

    def requestFirst(self) -> None:
        """
        Make a request for the first paginated page of packages.

        When the request is done, the list will get updated with the new package models.
        """
        self.setIsLoading(True)

    isLoadingChanged = pyqtSignal()

    @pyqtSlot(bool)
    def setIsLoading(self, is_loading: bool) -> None:
        if(is_loading != self._is_loading):
            self._is_loading = is_loading
            self.isLoadingChanged.emit()

    @pyqtProperty(bool, notify = isLoadingChanged, fset = setIsLoading)
    def isLoading(self) -> bool:
        """
        Gives whether the list is currently loading the first page or loading more pages.
        :return: ``True`` if the list is downloading, or ``False`` if not downloading.
        """
        return self._is_loading

    def _update(self) -> None:
        # TODO: Get list of packages from Marketplace class.
        pass
