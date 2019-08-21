# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import socket
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSlot


#
# This is a QObject because some of the functions can be used (and are useful) in QML.
#
class NetworkingUtil(QObject):

    def __init__(self, parent: Optional["QObject"] = None) -> None:
        super().__init__(parent = parent)

    # Checks if the given string is a valid IPv4 address.
    @pyqtSlot(str, result = bool)
    def isIPv4(self, address: str) -> bool:
        try:
            socket.inet_pton(socket.AF_INET, address)
            result = True
        except:
            result = False
        return result

    # Checks if the given string is a valid IPv6 address.
    @pyqtSlot(str, result = bool)
    def isIPv6(self, address: str) -> bool:
        try:
            socket.inet_pton(socket.AF_INET6, address)
            result = True
        except:
            result = False
        return result

    # Checks if the given string is a valid IPv4 or IPv6 address.
    @pyqtSlot(str, result = bool)
    def isValidIP(self, address: str) -> bool:
        return self.isIPv4(address) or self.isIPv6(address)


__all__ = ["NetworkingUtil"]
