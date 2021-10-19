# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt

from UM.Qt.ListModel import ListModel

class PackageList(ListModel):
    """
    Represents a list of packages to be displayed in the interface.

    The list can be filtered (e.g. on package type, materials vs. plug-ins) and
    paginated.
    """

    PackageIDRole = Qt.UserRole + 1
    DisplayNameRole = Qt.UserRole + 2
    # TODO: Add more roles here when we need to display more information about packages.

    def _update(self) -> None:
        # TODO: Get list of packages from Marketplace class.
        pass
