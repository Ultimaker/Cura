from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry

from UM.Settings.ContainerRegistry import ContainerRegistry
from cura.MachineAction import MachineAction

from PyQt5.QtCore import pyqtSignal, pyqtProperty, pyqtSlot, QUrl, QObject
from PyQt5.QtQml import QQmlComponent, QQmlContext
from PyQt5.QtGui import QDesktopServices

import os.path

catalog = i18nCatalog("cura")

class DiscoverOctoPrintAction(MachineAction):
    def __init__(self, parent = None):
        super().__init__("DiscoverOctoPrintAction", catalog.i18nc("@action", "Connect OctoPrint"))

        self._qml_url = "DiscoverOctoPrintAction.qml"
        self._window = None
        self._context = None

        self._network_plugin = None

        ContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)
        Application.getInstance().engineCreatedSignal.connect(self._createAdditionalComponentsView)

    instancesChanged = pyqtSignal()

    @pyqtSlot()
    def startDiscovery(self):
        if not self._network_plugin:
            self._network_plugin = Application.getInstance().getOutputDeviceManager().getOutputDevicePlugin("OctoPrintPlugin")
            self._network_plugin.addInstanceSignal.connect(self._onInstanceDiscovery)
            self._network_plugin.removeInstanceSignal.connect(self._onInstanceDiscovery)
            self._network_plugin.instanceListChanged.connect(self._onInstanceDiscovery)
            self.instancesChanged.emit()
        else:
            # Restart bonjour discovery
            self._network_plugin.startDiscovery()

    def _onInstanceDiscovery(self, *args):
        self.instancesChanged.emit()

    @pyqtSlot(str)
    def removeManualInstance(self, name):
        if not self._network_plugin:
            return

        self._network_plugin.removeManualInstance(name)

    @pyqtSlot(str, str, int, str, bool)
    def setManualInstance(self, name, address, port, path, useHttps):
        # This manual printer could replace a current manual printer
        self._network_plugin.removeManualInstance(name)

        self._network_plugin.addManualInstance(name, address, port, path, useHttps)

    def _onContainerAdded(self, container):
        # Add this action as a supported action to all machine definitions
        if isinstance(container, DefinitionContainer) and container.getMetaDataEntry("type") == "machine" and container.getMetaDataEntry("supports_usb_connection"):
            Application.getInstance().getMachineActionManager().addSupportedAction(container.getId(), self.getKey())

    @pyqtProperty("QVariantList", notify = instancesChanged)
    def discoveredInstances(self):
        if self._network_plugin:
            instances = list(self._network_plugin.getInstances().values())
            instances.sort(key = lambda k: k.name)
            return instances
        else:
            return []

    @pyqtSlot(str)
    def setKey(self, key):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            if "octoprint_id" in global_container_stack.getMetaData():
                global_container_stack.setMetaDataEntry("octoprint_id", key)
            else:
                global_container_stack.addMetaDataEntry("octoprint_id", key)

        if self._network_plugin:
            # Ensure that the connection states are refreshed.
            self._network_plugin.reCheckConnections()

    @pyqtSlot(result = str)
    def getStoredKey(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "octoprint_id" in meta_data:
                return global_container_stack.getMetaDataEntry("octoprint_id")

        return ""

    @pyqtSlot(str)
    def setApiKey(self, api_key):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            if "octoprint_api_key" in global_container_stack.getMetaData():
                global_container_stack.setMetaDataEntry("octoprint_api_key", api_key)
            else:
                global_container_stack.addMetaDataEntry("octoprint_api_key", api_key)

        if self._network_plugin:
            # Ensure that the connection states are refreshed.
            self._network_plugin.reCheckConnections()

    apiKeyChanged = pyqtSignal()

    ##  Get the stored API key of this machine
    #   \return key String containing the key of the machine.
    @pyqtProperty(str, notify = apiKeyChanged)
    def apiKey(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            return global_container_stack.getMetaDataEntry("octoprint_api_key")
        else:
            return ""

    @pyqtSlot(str, str, str)
    def setContainerMetaDataEntry(self, container_id, key, value):
        containers = ContainerRegistry.getInstance().findContainers(None, id = container_id)
        if not containers:
            UM.Logger.log("w", "Could not set metadata of container %s because it was not found.", container_id)
            return False

        container = containers[0]
        if key in container.getMetaData():
            container.setMetaDataEntry(key, value)
        else:
            container.addMetaDataEntry(key, value)

    @pyqtSlot(str)
    def openWebPage(self, url):
        QDesktopServices.openUrl(QUrl(url))

    def _createAdditionalComponentsView(self):
        Logger.log("d", "Creating additional ui components for OctoPrint-connected printers.")

        path = QUrl.fromLocalFile(os.path.join(PluginRegistry.getInstance().getPluginPath("OctoPrintPlugin"), "OctoPrintComponents.qml"))
        self._additional_component = QQmlComponent(Application.getInstance()._engine, path)

        # We need access to engine (although technically we can't)
        self._additional_components_context = QQmlContext(Application.getInstance()._engine.rootContext())
        self._additional_components_context.setContextProperty("manager", self)

        self._additional_components_view = self._additional_component.create(self._additional_components_context)
        if not self._additional_components_view:
            Logger.log("w", "Could not create additional components for OctoPrint-connected printers.")
            return

        Application.getInstance().addAdditionalComponent("monitorButtons", self._additional_components_view.findChild(QObject, "openOctoPrintButton"))
