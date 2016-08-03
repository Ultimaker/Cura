from UM.i18n import i18nCatalog
from cura.MachineAction import MachineAction
import cura.Settings.CuraContainerRegistry

from UM.Settings.DefinitionContainer import DefinitionContainer

from UM.Application import Application

from PyQt5.QtCore import pyqtSignal, pyqtProperty, pyqtSlot, QUrl
from PyQt5.QtGui import QDesktopServices

catalog = i18nCatalog("cura")

class DiscoverOctoPrintAction(MachineAction):
    def __init__(self, parent = None):
        super().__init__("DiscoverOctoPrintAction", catalog.i18nc("@action", "Connect OctoPrint"))

        self._qml_url = "DiscoverOctoPrintAction.qml"
        self._window = None
        self._context = None

        self._network_plugin = None

        cura.Settings.CuraContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

    instancesChanged = pyqtSignal()

    @pyqtSlot()
    def startDiscovery(self):
        if not self._network_plugin:
            self._network_plugin = Application.getInstance().getOutputDeviceManager().getOutputDevicePlugin("OctoPrintPlugin")
            self._network_plugin.addInstanceSignal.connect(self._onInstanceDiscovery)
            self._network_plugin.removeInstanceSignal.connect(self._onInstanceDiscovery)
            self.instancesChanged.emit()
        else:
            # Restart bonjour discovery
            self._network_plugin.startDiscovery()

    def _onInstanceDiscovery(self, *args):
        self.instancesChanged.emit()

    def _onContainerAdded(self, container):
        # Add this action as a supported action to all machine definitions
        if isinstance(container, DefinitionContainer) and container.getMetaDataEntry("type") == "machine":
            Application.getInstance().getMachineActionManager().addSupportedAction(container.getId(), self.getKey())

    @pyqtProperty("QVariantList", notify = instancesChanged)
    def discoveredInstances(self):
        if self._network_plugin:
            instances = self._network_plugin.getInstances()
            return [instances[instance] for instance in instances]
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

    @pyqtSlot(str)
    def openWebPage(self, url):
        QDesktopServices.openUrl(QUrl(url))