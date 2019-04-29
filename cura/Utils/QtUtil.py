# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional

from PyQt5.QtCore import QObject, pyqtSlot

from . import networking


#
# Exposes the util functions to QML using a QObject.
#
class QtUtil(QObject):

    def __init__(self, parent: Optional["QObject"] = None) -> None:
        super().__init__(parent = parent)

    @pyqtSlot(str, result = bool)
    def isValidIP(self, address: str) -> bool:
        return networking.isValidIP(address)
