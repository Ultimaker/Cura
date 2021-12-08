#  Copyright (c) 2021 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional, TYPE_CHECKING

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal

from cura.CuraApplication import CuraApplication

if TYPE_CHECKING:
    from UM.PluginRegistry import PluginRegistry
    from cura.CuraPackageManager import CuraPackageManager


class RestartManager(QObject):
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent = parent)
        self._manager: "CuraPackageManager" = CuraApplication.getInstance().getPackageManager()
        self._plugin_registry: "PluginRegistry" = CuraApplication.getInstance().getPluginRegistry()

        self._manager.installedPackagesChanged.connect(self.checkIfRestartNeeded)
        self._plugin_registry.hasPluginsEnabledOrDisabledChanged.connect(self.checkIfRestartNeeded)

        self._restart_needed = False

    def checkIfRestartNeeded(self):
        if self._manager.hasPackagesToRemoveOrInstall or len(self._plugin_registry.getCurrentSessionActivationChangedPlugins()) > 0:
            self._restart_needed = True
        else:
            self._restart_needed = False
        self.showRestartNotificationChanged.emit()

    showRestartNotificationChanged = pyqtSignal()

    @pyqtProperty(bool, notify = showRestartNotificationChanged)
    def showRestartNotification(self) -> bool:
        return self._restart_needed
