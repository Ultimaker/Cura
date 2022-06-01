import os

from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty
from typing import Optional, List, Dict, cast
from cura.CuraApplication import CuraApplication
from UM.PluginRegistry import PluginRegistry
from cura.CuraPackageManager import CuraPackageManager

from plugins.Marketplace.MissingPackageList import MissingPackageList


class InstallMissingPackageDialog(QObject):
    """Dialog used to display packages that need to be installed to load 3mf file materials"""
    def __init__(self, packages_metadata: List[Dict[str, str]]):
        """Initialize

        :param packages_metadata: List of dictionaries containing information about missing packages.
        """
        super().__init__()

        self._plugin_registry: PluginRegistry = CuraApplication.getInstance().getPluginRegistry()
        self._package_manager: CuraPackageManager = cast(CuraPackageManager, CuraApplication.getInstance().getPackageManager())
        self._package_manager.installedPackagesChanged.connect(self.checkIfRestartNeeded)

        self._dialog: Optional[QObject] = None
        self._restart_needed = False
        self._package_metadata: List[Dict[str, str]] = packages_metadata

        self._package_model = MissingPackageList()
        self._package_model.setPackageIds(packages_metadata)

    def show(self):
        plugin_path = self._plugin_registry.getPluginPath("Marketplace")
        if plugin_path is None:
            plugin_path = os.path.dirname(__file__)

        # create a QML component for the license dialog
        license_dialog_component_path = os.path.join(plugin_path, "resources", "qml", "InstallMissingPackagesDialog.qml")
        self._dialog = CuraApplication.getInstance().createQmlComponent(license_dialog_component_path, {"manager": self})
        self._dialog.show()

    def checkIfRestartNeeded(self) -> None:
        if self._dialog is None:
            return

        if self._package_manager.hasPackagesToRemoveOrInstall:
            self._restart_needed = True
        else:
            self._restart_needed = False
        self.showRestartChanged.emit()

    showRestartChanged = pyqtSignal()

    @pyqtProperty(bool, notify=showRestartChanged)
    def showRestartNotification(self) -> bool:
        return self._restart_needed

    @pyqtProperty(QObject)
    def model(self):
        return self._package_model
