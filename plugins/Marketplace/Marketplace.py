# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os.path
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtQml import qmlRegisterType
from typing import Optional, TYPE_CHECKING

from cura.CuraApplication import CuraApplication  # Creating QML objects and managing packages.

from UM.Extension import Extension  # We are implementing the main object of an extension here.
from UM.PluginRegistry import PluginRegistry  # To find out where we are stored (the proper way).

from .RemotePackageList import RemotePackageList  # To register this type with QML.
from .LocalPackageList import LocalPackageList  # To register this type with QML.

if TYPE_CHECKING:
    from PyQt5.QtCore import QObject


class Marketplace(Extension):
    """
    The main managing object for the Marketplace plug-in.
    """

    def __init__(self) -> None:
        super().__init__()
        self._window: Optional["QObject"] = None  # If the window has been loaded yet, it'll be cached in here.

        qmlRegisterType(RemotePackageList, "Marketplace", 1, 0, "RemotePackageList")
        qmlRegisterType(LocalPackageList, "Marketplace", 1, 0, "LocalPackageList")

    @pyqtSlot()
    def show(self) -> None:
        """
        Opens the window of the Marketplace.

        If the window hadn't been loaded yet into Qt, it will be created lazily.
        """
        if self._window is None:
            plugin_path = PluginRegistry.getInstance().getPluginPath(self.getPluginId())
            if plugin_path is None:
                plugin_path = os.path.dirname(__file__)
            path = os.path.join(plugin_path, "resources", "qml", "Marketplace.qml")
            self._window = CuraApplication.getInstance().createQmlComponent(path, {})
        if self._window is None:  # Still None? Failed to load the QML then.
            return
        self._window.show()
        self._window.requestActivate()  # Bring window into focus, if it was already open in the background.
