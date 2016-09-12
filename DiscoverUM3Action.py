from cura.MachineAction import MachineAction

from UM.Application import Application
from UM.PluginRegistry import PluginRegistry
from UM.Logger import Logger

from PyQt5.QtCore import pyqtSignal, pyqtProperty, pyqtSlot, QUrl, QObject
from PyQt5.QtQml import QQmlComponent, QQmlContext

import os.path

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

class DiscoverUM3Action(MachineAction):
    def __init__(self):
        super().__init__("DiscoverUM3Action", catalog.i18nc("@action","Connect via Network"))
        self._qml_url = "DiscoverUM3Action.qml"

        self._network_plugin = None

        self._context = None
        self._additional_component = None
        self._additional_components_view = None

        Application.getInstance().engineCreatedSignal.connect(self._createAdditionalComponentsView)

    printersChanged = pyqtSignal()

    @pyqtSlot()
    def startDiscovery(self):
        if not self._network_plugin:
            self._network_plugin = Application.getInstance().getOutputDeviceManager().getOutputDevicePlugin("JediWifiPrintingPlugin")
            self._network_plugin.addPrinterSignal.connect(self._onPrinterDiscoveryChanged)
            self._network_plugin.removePrinterSignal.connect(self._onPrinterDiscoveryChanged)
            self.printersChanged.emit()

    @pyqtSlot()
    def restartDiscovery(self):
        if not self._network_plugin:
            self.startDiscovery()
        else:
            self._network_plugin.startDiscovery()

    def _onPrinterDiscoveryChanged(self, *args):
        self.printersChanged.emit()

    @pyqtProperty("QVariantList", notify = printersChanged)
    def foundDevices(self):
        if self._network_plugin:
            printers = list(self._network_plugin.getPrinters().values())
            printers.sort(key = lambda k: k.name)
            return printers
        else:
            return []

    @pyqtSlot(str)
    def setKey(self, key):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "um_network_key" in meta_data:
                global_container_stack.setMetaDataEntry("um_network_key", key)
                # Delete old authentication data.
                global_container_stack.removeMetaDataEntry("network_authentication_id")
                global_container_stack.removeMetaDataEntry("network_authentication_key")
            else:
                global_container_stack.addMetaDataEntry("um_network_key", key)

        if self._network_plugin:
            # Ensure that the connection states are refreshed.
            self._network_plugin.reCheckConnections()

    @pyqtSlot(result = str)
    def getStoredKey(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "um_network_key" in meta_data:
                return global_container_stack.getMetaDataEntry("um_network_key")

        return ""

    def _createAdditionalComponentsView(self):
        Logger.log("d", "Creating additional ui components for UM3.")

        path = QUrl.fromLocalFile(os.path.join(PluginRegistry.getInstance().getPluginPath("JediWifiPrintingPlugin"), "UM3InfoComponents.qml"))
        self._additional_component = QQmlComponent(Application.getInstance()._engine, path)

        # We need access to engine (although technically we can't)
        self._context = QQmlContext(Application.getInstance()._engine.rootContext())
        self._context.setContextProperty("manager", self)
        self._additional_components_view = self._additional_component.create(self._context)

        Application.getInstance().addAdditionalComponent("monitorButtons", self._additional_components_view.findChild(QObject, "networkPrinterConnectButton"))
        Application.getInstance().addAdditionalComponent("machinesDetailPane", self._additional_components_view.findChild(QObject, "networkPrinterConnectionInfo"))
