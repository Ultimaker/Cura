# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt
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

    def __init__(self, parent: "QObject" = None):
        super().__init__(parent)

        self._packages: List[PackageModel] = []

    def _update(self) -> None:
        # TODO: Get list of packages from Marketplace class.
        pass
