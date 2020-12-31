# coding=utf-8
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Application import Application

from UM.Settings.ContainerRegistry import ContainerRegistry
from cura.MachineAction import MachineAction
from UM.PluginRegistry import PluginRegistry
from cura.CuraApplication import CuraApplication

from PyQt5.QtCore import pyqtSignal, pyqtProperty, pyqtSlot, QUrl, QObject
from PyQt5.QtQml import QQmlComponent, QQmlContext
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager

import os.path
import json
import base64
import time

from PyQt5.QtCore import QTimer

catalog = i18nCatalog("cura")


class MachineConfig(MachineAction):
    def __init__(self, parent=None):
        super().__init__("MachineConfig", catalog.i18nc("@action", "KOONOVO WIFI"))
        self._qml_url = "MachineConfig.qml"
        ContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

        self._application = CuraApplication.getInstance()
        self._network_plugin = None

        self.__additional_components_context = None
        self.__additional_component = None
        self.__additional_components_view = None

        # Try to get version information from plugin.json
        plugin_file_path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "plugin.json")
        try:
            with open(plugin_file_path) as plugin_file:
                plugin_info = json.load(plugin_file)
                self._plugin_version = plugin_info["version"]
        except:
            # The actual version info is not critical to have so we can continue
            self._plugin_version = "0.0"
            Logger.logException(
                "w", "Could not get version information for the plugin")

        self._user_agent = ("%s/%s %s/%s" % (
            self._application.getApplicationName(),
            self._application.getVersion(),
            "KOONOVOWifiPlugin",
            self._plugin_version
        )).encode()

        self._application.engineCreatedSignal.connect(
            self._createAdditionalComponentsView)

        self._last_zeroconf_event_time = time.time()
        # Time to wait after a zeroconf service change before allowing a zeroconf reset
        self._zeroconf_change_grace_period = 0.25

        self.timer = QTimer(self)
        self.timer.start(10000) # 5s
        self.timer.timeout.connect(self.restartDiscovery)

    printersChanged = pyqtSignal()
    printersTryToConnect = pyqtSignal()

    @pyqtProperty(str, constant=True)
    def pluginVersion(self) -> str:
        return self._plugin_version

    @pyqtSlot()
    def startDiscovery(self):
        if not self._network_plugin:
            Logger.log("d", "Starting printer discovery.")
            self._network_plugin = self._application.getOutputDeviceManager(
            ).getOutputDevicePlugin(self._plugin_id)
            if not self._network_plugin:
                return
            self._network_plugin.printerListChanged.connect(
                self._onPrinterDiscoveryChanged)
            self.printersChanged.emit()

    # Re-filters the list of printers.
    @pyqtSlot()
    def reset(self):
        Logger.log("d", "Reset the list of found printers.")
        self.printersChanged.emit()

    @pyqtSlot()
    def restartDiscovery(self):
        self.timer.stop()
        # Ensure that there is a bit of time after a printer has been discovered.
        # This is a work around for an issue with Qt 5.5.1 up to Qt 5.7 which can segfault if we do this too often.
        # It's most likely that the QML engine is still creating delegates, where the python side already deleted or
        # garbage collected the data.
        # Whatever the case, waiting a bit ensures that it doesn't crash.
        if time.time() - self._last_zeroconf_event_time > self._zeroconf_change_grace_period:
            if not self._network_plugin:
                self.startDiscovery()
            else:
                self._network_plugin.startDiscovery()

    @pyqtSlot(str, str)
    def removeManualPrinter(self, key, address):
        if not self._network_plugin:
            return

        self._network_plugin.removeManualPrinter(key, address)

    @pyqtSlot(str, str)
    def setManualPrinter(self, key, address):
        if key != "":
            # This manual printer replaces a current manual printer
            self._network_plugin.removeManualPrinter(key)

        if address != "":
            self._network_plugin.addManualPrinter(address)

    def _onPrinterDiscoveryChanged(self, *args):
        self._last_zeroconf_event_time = time.time()
        self.printersChanged.emit()

    @pyqtProperty("QVariantList", notify=printersChanged)
    def foundDevices(self):
        if self._network_plugin:
            printers = list(self._network_plugin.getPrinters().values())
            printers.sort(key=lambda k: k.name)
            # printers = list(["1, 2, 3", "2, 2, 3", "3, 3, 2"])
            return printers
        else:
            return []

    @pyqtProperty("QVariantList")
    def getSDFiles(self):
        printers = list(["1, 2, 3", "2, 2, 3", "3, 3, 2"])
        return printers

    @pyqtSlot()
    def changestage(self):
        CuraApplication.getInstance().getController().setActiveStage("MonitorStage")

    @pyqtSlot(str)
    def disConnection(self, key):
        global_container_stack = self._application.getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "KOONOVO_network_key" in meta_data:
                global_container_stack.setMetaDataEntry("KOONOVO_network_key", None)
                # Delete old authentication data.
                global_container_stack.removeMetaDataEntry(
                    "network_authentication_id")
                global_container_stack.removeMetaDataEntry(
                    "network_authentication_key")
        Logger.log("d", "disConnection change %s" % key)
        if self._network_plugin:
            self._network_plugin.disConnections(key)

    @pyqtSlot(str)
    def setKey(self, key):        
        # preferences = Application.getInstance().getPreferences()
        # preferences.addPreference("KOONOVOwifi/changestage", "True")
        Logger.log(
            "d", "KOONOVO Plugin Plugin the network key of the active machine to %s", key)
        global_container_stack = self._application.getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "KOONOVO_network_key" in meta_data:
                global_container_stack.setMetaDataEntry("KOONOVO_network_key", key)
                # Delete old authentication data.
                global_container_stack.removeMetaDataEntry(
                    "network_authentication_id")
                global_container_stack.removeMetaDataEntry(
                    "network_authentication_key")
            else:
                Logger.log("d", "KOONOVO Plugin Plugin add dataEntry")
                global_container_stack.setMetaDataEntry("KOONOVO_network_key", key)

        if self._network_plugin:
            # Ensure that the connection states are refreshed.
            Logger.log("d", "reCheckConnections-----")
            preferences = Application.getInstance().getPreferences()
            preferences.addPreference("KOONOVOwifi/stopupdate", "True")
            self._network_plugin.reCheckConnections()
        

    @pyqtSlot()
    def printtest(self):
        Logger.log("d", "KOONOVO ready for click")

    @pyqtSlot(result=str)
    def getStoredKey(self):
        global_container_stack = self._application.getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "KOONOVO_network_key" in meta_data:
                return global_container_stack.getMetaDataEntry("KOONOVO_network_key")

        return ""

    @pyqtSlot()
    def loadConfigurationFromPrinter(self):
        machine_manager = self._application.getMachineManager()
        hotend_ids = machine_manager.printerOutputDevices[0].hotendIds
        for index in range(len(hotend_ids)):
            machine_manager.printerOutputDevices[0].hotendIdChanged.emit(
                index, hotend_ids[index])
        material_ids = machine_manager.printerOutputDevices[0].materialIds
        for index in range(len(material_ids)):
            machine_manager.printerOutputDevices[0].materialIdChanged.emit(
                index, material_ids[index])

    def _createAdditionalComponentsView(self):
        Logger.log("d", "Creating additional ui components for tft35.")

        # Create networking dialog
        path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "KOONOVOConnectBtn.qml")
        # self.__additional_components_view = self._application.createQmlComponent(path, {"manager": self})
        self.__additional_components_view = CuraApplication.getInstance(
        ).createQmlComponent(path, {"manager": self})
        if not self.__additional_components_view:
            Logger.log("w", "Could not create ui components for tft35.")
            return

        # Create extra components
        self._application.addAdditionalComponent("monitorButtons",
                                                 self.__additional_components_view.findChild(QObject,
                                                                                             "networkPrinterConnectButton"))
        self._application.addAdditionalComponent("machinesDetailPane",
                                                 self.__additional_components_view.findChild(QObject,
                                                                                             "networkPrinterConnectionInfo"))

    def _onContainerAdded(self, container):
        # Add this action as a supported action to all machine definitions
        if isinstance(container, DefinitionContainer) and container.getMetaDataEntry(
                "type") == "machine" and container.getMetaDataEntry("supports_usb_connection"):
            self._application.getMachineActionManager(
            ).addSupportedAction(container.getId(), self.getKey())
