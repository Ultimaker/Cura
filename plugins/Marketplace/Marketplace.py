# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os.path
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtQml import qmlRegisterType
from typing import Optional, TYPE_CHECKING

from cura.CuraApplication import CuraApplication  # Creating QML objects and managing packages.

from UM.Extension import Extension  # We are implementing the main object of an extension here.
from UM.PluginRegistry import PluginRegistry  # To find out where we are stored (the proper way).

from .RemotePackageList import RemotePackageList  # To register this type with QML.
from .LocalPackageList import LocalPackageList  # To register this type with QML.
from .RestartManager import RestartManager  # To register this type with QML.


class Marketplace(Extension):
    """
    The main managing object for the Marketplace plug-in.
    """

    class TabManager(QObject):
        def __init__(self) -> None:
            super().__init__(parent=CuraApplication.getInstance())
            self._tab_shown: int = 0

        def getTabShown(self) -> int:
            return self._tab_shown

        def setTabShown(self, tab_shown: int) -> None:
            if tab_shown != self._tab_shown:
                self._tab_shown = tab_shown
                self.tabShownChanged.emit()

        tabShownChanged = pyqtSignal()
        tabShown = pyqtProperty(int, fget=getTabShown, fset=setTabShown, notify=tabShownChanged)

    def __init__(self) -> None:
        super().__init__()
        self._window: Optional["QObject"] = None  # If the window has been loaded yet, it'll be cached in here.
        self._plugin_registry: Optional[PluginRegistry] = None
        self._tab_manager = Marketplace.TabManager()

        qmlRegisterType(RemotePackageList, "Marketplace", 1, 0, "RemotePackageList")
        qmlRegisterType(LocalPackageList, "Marketplace", 1, 0, "LocalPackageList")
        qmlRegisterType(RestartManager, "Marketplace", 1, 0, "RestartManager")

    @pyqtSlot()
    def show(self) -> None:
        """
        Opens the window of the Marketplace.

        If the window hadn't been loaded yet into Qt, it will be created lazily.
        """
        if self._window is None:
            self._plugin_registry = PluginRegistry.getInstance()
            plugin_path = PluginRegistry.getInstance().getPluginPath(self.getPluginId())
            if plugin_path is None:
                plugin_path = os.path.dirname(__file__)
            path = os.path.join(plugin_path, "resources", "qml", "Marketplace.qml")
            self._window = CuraApplication.getInstance().createQmlComponent(path, {"tabManager": self._tab_manager})
        if self._window is None:  # Still None? Failed to load the QML then.
            return
        self._tab_manager.setTabShown(0)
        self._window.show()
        self._window.requestActivate()  # Bring window into focus, if it was already open in the background.

    @pyqtSlot()
    def setVisibleTabToMaterials(self) -> None:
        """
        Set the tab shown to the remote materials one.
        Not implemented in a more generic way because it needs the ability to be called with 'callExtensionMethod'.
        """
        self._tab_manager.setTabShown(1)
