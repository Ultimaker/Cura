from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from . import OctoPrintOutputDevice

from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange, ServiceInfo
from UM.Signal import Signal, signalemitter
from UM.Application import Application
from UM.Logger import Logger
from UM.Preferences import Preferences

import time
import json
import re

##      This plugin handles the connection detection & creation of output device objects for OctoPrint-connected printers.
#       Zero-Conf is used to detect printers, which are saved in a dict.
#       If we discover an instance that has the same key as the active machine instance a connection is made.
@signalemitter
class OctoPrintOutputDevicePlugin(OutputDevicePlugin):
    def __init__(self):
        super().__init__()
        self._zero_conf = Zeroconf()
        self._browser = None
        self._instances = {}

        # Because the model needs to be created in the same thread as the QMLEngine, we use a signal.
        self.addInstanceSignal.connect(self.addInstance)
        self.removeInstanceSignal.connect(self.removeInstance)
        Application.getInstance().globalContainerStackChanged.connect(self.reCheckConnections)

        # Load custom instances from preferences
        self._preferences = Preferences.getInstance()
        self._preferences.addPreference("octoprint/manual_instances", "{}")

        try:
            self._manual_instances = json.loads(self._preferences.getValue("octoprint/manual_instances"))
        except ValueError:
            self._manual_instances = {}
        if not isinstance(self._manual_instances, dict):
            self._manual_instances = {}

        self._name_regex = re.compile("OctoPrint instance (\".*\"\.|on )(.*)\.")

    addInstanceSignal = Signal()
    removeInstanceSignal = Signal()
    instanceListChanged = Signal()

    ##  Start looking for devices on network.
    def start(self):
        self.startDiscovery()

    def startDiscovery(self):
        if self._browser:
            self._browser.cancel()
            self._browser = None
            self._printers = {}
        self.instanceListChanged.emit()

        self._zero_conf.__init__()
        self._browser = ServiceBrowser(self._zero_conf, u'_octoprint._tcp.local.', [self._onServiceChanged])

        # Add manual instances from preference
        for name, properties in self._manual_instances.items():
            additional_properties = {
                b"path": properties["path"].encode("utf-8"),
                b"useHttps": b"true" if properties.get("useHttps", False) else b"false",
                b"manual": b"true"
            } # These additional properties use bytearrays to mimick the output of zeroconf
            self.addInstance(name, properties["address"], properties["port"], additional_properties)

    def addManualInstance(self, name, address, port, path, useHttps = False):
        self._manual_instances[name] = {"address": address, "port": port, "path": path, "useHttps": useHttps}
        self._preferences.setValue("octoprint/manual_instances", json.dumps(self._manual_instances))

        properties = { b"path": path.encode("utf-8"), b"useHttps": b"true" if useHttps else b"false", b"manual": b"true" }

        if name in self._instances:
            self.removeInstance(name)

        self.addInstance(name, address, port, properties)
        self.instanceListChanged.emit()

    def removeManualInstance(self, name):
        if name in self._instances:
            self.removeInstance(name)
            self.instanceListChanged.emit()

        if name in self._manual_instances:
            self._manual_instances.pop(name, None)
            self._preferences.setValue("octoprint/manual_instances", json.dumps(self._manual_instances))

    ##  Stop looking for devices on network.
    def stop(self):
        self._browser.cancel()
        self._browser = None
        self._zero_conf.close()

    def getInstances(self):
        return self._instances

    def reCheckConnections(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if not global_container_stack:
            return

        for key in self._instances:
            if key == global_container_stack.getMetaDataEntry("octoprint_id"):
                self._instances[key].setApiKey(global_container_stack.getMetaDataEntry("octoprint_api_key", ""))
                self._instances[key].connectionStateChanged.connect(self._onInstanceConnectionStateChanged)
                self._instances[key].connect()
            else:
                if self._instances[key].isConnected():
                    self._instances[key].close()

    ##  Because the model needs to be created in the same thread as the QMLEngine, we use a signal.
    def addInstance(self, name, address, port, properties):
        instance = OctoPrintOutputDevice.OctoPrintOutputDevice(name, address, port, properties)
        self._instances[instance.getKey()] = instance
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack and instance.getKey() == global_container_stack.getMetaDataEntry("octoprint_id"):
            instance.setApiKey(global_container_stack.getMetaDataEntry("octoprint_api_key", ""))
            instance.connectionStateChanged.connect(self._onInstanceConnectionStateChanged)
            instance.connect()

    def removeInstance(self, name):
        instance = self._instances.pop(name, None)
        if instance:
            if instance.isConnected():
                instance.connectionStateChanged.disconnect(self._onInstanceConnectionStateChanged)
                instance.disconnect()

    ##  Handler for when the connection state of one of the detected instances changes
    def _onInstanceConnectionStateChanged(self, key):
        if key not in self._instances:
            return

        if self._instances[key].isConnected():
            self.getOutputDeviceManager().addOutputDevice(self._instances[key])
        else:
            self.getOutputDeviceManager().removeOutputDevice(key)

    ##  Handler for zeroConf detection
    def _onServiceChanged(self, zeroconf, service_type, name, state_change):
        if state_change == ServiceStateChange.Added:
            key = name
            result = self._name_regex.match(name)
            if result:
                if result.group(1) == "on ":
                    name = result.group(2)
                else:
                    name = result.group(1) + result.group(2)

            Logger.log("d", "Bonjour service added: %s" % name)

            # First try getting info from zeroconf cache
            info = ServiceInfo(service_type, key, properties = {})
            for record in zeroconf.cache.entries_with_name(key.lower()):
                info.update_record(zeroconf, time.time(), record)

            for record in zeroconf.cache.entries_with_name(info.server):
                info.update_record(zeroconf, time.time(), record)
                if info.address and info.address[:2] != b'\xa9\xfe': # don't accept 169.254.x.x address
                    break

            # Request more data if info is not complete
            if not info.address or not info.port:
                Logger.log("d", "Trying to get address of %s", name)
                info = zeroconf.get_service_info(service_type, key)

                if not info:
                    Logger.log("w", "Could not get information about %s" % name)
                    return

            if info.address and info.port:
                address = '.'.join(map(lambda n: str(n), info.address))
                self.addInstanceSignal.emit(name, address, info.port, info.properties)
            else:
                Logger.log("d", "Discovered instance named %s but received no address", name)

        elif state_change == ServiceStateChange.Removed:
            self.removeInstanceSignal.emit(str(name))
