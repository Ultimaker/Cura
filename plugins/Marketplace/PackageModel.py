# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, QObject

class PackageModel(QObject):
    """
    Represents a package, containing all the relevant information to be displayed about a package.

    Effectively this behaves like a glorified named tuple, but as a QObject so that its properties can be obtained from
    QML.
    """

    def __init__(self, package_id: str, display_name: str, parent: QObject = None):
        super().__init__(parent)
        self._package_id = package_id
        self._display_name = display_name

    @pyqtProperty(str, constant = True)
    def packageId(self) -> str:
        return self._package_id

    @pyqtProperty(str, constant = True)
    def displayName(self) -> str:
        return self._display_name
