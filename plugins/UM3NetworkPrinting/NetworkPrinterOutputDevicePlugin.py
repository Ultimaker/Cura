# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
import time
import json

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager, QNetworkReply
from PyQt5.QtQml import QQmlComponent, QQmlContext
from UM.Application import Application
from UM.Logger import Logger
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from UM.PluginRegistry import PluginRegistry
from UM.Preferences import Preferences
from UM.Signal import Signal, signalemitter
from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange, ServiceInfo  # type: ignore

from . import NetworkPrinterOutputDevice, NetworkClusterPrinterOutputDevice


##      This plugin handles the connection detection & creation of output device objects for the UM3 printer.
#       Zero-Conf is used to detect printers, which are saved in a dict.
#       If we discover a printer that has the same key as the active machine instance a connection is made.
@signalemitter
class NetworkPrinterOutputDevicePlugin(QObject, OutputDevicePlugin):
    def __init__(self):
        super().__init__()
        self._zero_conf = None
        self._browser = None
        self._printers = {}

        self._api_version = "1"
        self._api_prefix = "/api/v" + self._api_version + "/"
        self._cluster_api_version = "1"
        self._cluster_api_prefix = "/cluster-api/v" + self._cluster_api_version + "/"

        self._network_manager = QNetworkAccessManager()
        self._network_manager.finished.connect(self._onNetworkRequestFinished)

        # List of old printer names. This is used to ensure that a refresh of zeroconf does not needlessly forces
        # authentication requests.
        self._old_printers = []

        # Because the model needs to be created in the same thread as the QMLEngine, we use a signal.
        self.addPrinterSignal.connect(self.addPrinter)
        self.removePrinterSignal.connect(self.removePrinter)
        Application.getInstance().globalContainerStackChanged.connect(self.reCheckConnections)

        # Get list of manual printers from preferences
        self._preferences = Preferences.getInstance()
        self._preferences.addPreference("um3networkprinting/manual_instances", "") #  A comma-separated list of ip adresses or hostnames
        self._manual_instances = self._preferences.getValue("um3networkprinting/manual_instances").split(",")

        self._network_requests_buffer = {}  # store api responses until data is complete

    addPrinterSignal = Signal()
    removePrinterSignal = Signal()
    printerListChanged = Signal()

    ##  Start looking for devices on network.
    def start(self):
        self.startDiscovery()

    def startDiscovery(self):
        self.stop()
        if self._browser:
            self._browser.cancel()
            self._browser = None
            self._old_printers = [printer_name for printer_name in self._printers]
            self._printers = {}
            self.printerListChanged.emit()
        # After network switching, one must make a new instance of Zeroconf
        # On windows, the instance creation is very fast (unnoticable). Other platforms?
        self._zero_conf = Zeroconf()
        self._browser = ServiceBrowser(self._zero_conf, u'_ultimaker._tcp.local.', [self._onServiceChanged])

        # Look for manual instances from preference
        for address in self._manual_instances:
            if address:
                self.addManualPrinter(address)

    def addManualPrinter(self, address):
        if address not in self._manual_instances:
            self._manual_instances.append(address)
            self._preferences.setValue("um3networkprinting/manual_instances", ",".join(self._manual_instances))

        instance_name = "manual:%s" % address
        properties = {
            b"name": address.encode("utf-8"),
            b"address": address.encode("utf-8"),
            b"manual": b"true",
            b"incomplete": b"true"
        }

        if instance_name not in self._printers:
            # Add a preliminary printer instance
            self.addPrinter(instance_name, address, properties)

        self.checkManualPrinter(address)
        self.checkClusterPrinter(address)

    def removeManualPrinter(self, key, address = None):
        if key in self._printers:
            if not address:
                address = self._printers[key].ipAddress
            self.removePrinter(key)

        if address in self._manual_instances:
            self._manual_instances.remove(address)
            self._preferences.setValue("um3networkprinting/manual_instances", ",".join(self._manual_instances))

    def checkManualPrinter(self, address):
        # Check if a printer exists at this address
        # If a printer responds, it will replace the preliminary printer created above
        # origin=manual is for tracking back the origin of the call
        url = QUrl("http://" + address + self._api_prefix + "system?origin=manual_name")
        name_request = QNetworkRequest(url)
        self._network_manager.get(name_request)

    def checkClusterPrinter(self, address):
        cluster_url = QUrl("http://" + address + self._cluster_api_prefix + "printers/?origin=check_cluster")
        cluster_request = QNetworkRequest(cluster_url)
        self._network_manager.get(cluster_request)

    ##  Handler for all requests that have finished.
    def _onNetworkRequestFinished(self, reply):
        reply_url = reply.url().toString()
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)

        if reply.operation() == QNetworkAccessManager.GetOperation:
            address = reply.url().host()
            if "origin=manual_name" in reply_url:  # Name returned from printer.
                if status_code == 200:

                    try:
                        system_info = json.loads(bytes(reply.readAll()).decode("utf-8"))
                    except json.JSONDecodeError:
                        Logger.log("e", "Printer returned invalid JSON.")
                        return
                    except UnicodeDecodeError:
                        Logger.log("e", "Printer returned incorrect UTF-8.")
                        return

                    if address not in self._network_requests_buffer:
                        self._network_requests_buffer[address] = {}
                    self._network_requests_buffer[address]["system"] = system_info
            elif "origin=check_cluster" in reply_url:
                if address not in self._network_requests_buffer:
                    self._network_requests_buffer[address] = {}
                if status_code == 200:
                    # We know it's a cluster printer
                    Logger.log("d", "Cluster printer detected: [%s]", reply.url())

                    try:
                        cluster_printers_list = json.loads(bytes(reply.readAll()).decode("utf-8"))
                    except json.JSONDecodeError:
                        Logger.log("e", "Printer returned invalid JSON.")
                        return
                    except UnicodeDecodeError:
                        Logger.log("e", "Printer returned incorrect UTF-8.")
                        return

                    self._network_requests_buffer[address]["cluster"] = True
                    self._network_requests_buffer[address]["cluster_size"] = len(cluster_printers_list)
                else:
                    Logger.log("d", "This url is not from a cluster printer: [%s]", reply.url())
                    self._network_requests_buffer[address]["cluster"] = False

            # Both the system call and cluster call are finished
            if (address in self._network_requests_buffer and
                "system" in self._network_requests_buffer[address] and
                "cluster" in self._network_requests_buffer[address]):

                instance_name = "manual:%s" % address
                system_info = self._network_requests_buffer[address]["system"]
                machine = "unknown"
                if "variant" in system_info:
                    variant = system_info["variant"]
                    if variant == "Ultimaker 3":
                        machine = "9066"
                    elif variant == "Ultimaker 3 Extended":
                        machine = "9511"

                properties = {
                    b"name": system_info["name"].encode("utf-8"),
                    b"address": address.encode("utf-8"),
                    b"firmware_version": system_info["firmware"].encode("utf-8"),
                    b"manual": b"true",
                    b"machine": machine.encode("utf-8")
                }

                if self._network_requests_buffer[address]["cluster"]:
                    properties[b"cluster_size"] = self._network_requests_buffer[address]["cluster_size"]

                if instance_name in self._printers:
                    # Only replace the printer if it is still in the list of (manual) printers
                    self.removePrinter(instance_name)
                    self.addPrinter(instance_name, address, properties)

                del self._network_requests_buffer[address]

    ##  Stop looking for devices on network.
    def stop(self):
        if self._zero_conf is not None:
            Logger.log("d", "zeroconf close...")
            self._zero_conf.close()

    def getPrinters(self):
        return self._printers

    def reCheckConnections(self):
        active_machine = Application.getInstance().getGlobalContainerStack()
        if not active_machine:
            return

        for key in self._printers:
            if key == active_machine.getMetaDataEntry("um_network_key"):
                if not self._printers[key].isConnected():
                    Logger.log("d", "Connecting [%s]..." % key)
                    self._printers[key].connect()
                    self._printers[key].connectionStateChanged.connect(self._onPrinterConnectionStateChanged)
            else:
                if self._printers[key].isConnected():
                    Logger.log("d", "Closing connection [%s]..." % key)
                    self._printers[key].close()
                    self._printers[key].connectionStateChanged.disconnect(self._onPrinterConnectionStateChanged)

    ##  Because the model needs to be created in the same thread as the QMLEngine, we use a signal.
    def addPrinter(self, name, address, properties):
        cluster_size = int(properties.get(b"cluster_size", -1))
        if cluster_size >= 0:
            printer = NetworkClusterPrinterOutputDevice.NetworkClusterPrinterOutputDevice(
                name, address, properties, self._api_prefix)
        else:
            printer = NetworkPrinterOutputDevice.NetworkPrinterOutputDevice(name, address, properties, self._api_prefix)
        self._printers[printer.getKey()] = printer
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack and printer.getKey() == global_container_stack.getMetaDataEntry("um_network_key"):
            if printer.getKey() not in self._old_printers:  # Was the printer already connected, but a re-scan forced?
                Logger.log("d", "addPrinter, connecting [%s]..." % printer.getKey())
                self._printers[printer.getKey()].connect()
                printer.connectionStateChanged.connect(self._onPrinterConnectionStateChanged)
        self.printerListChanged.emit()

    def removePrinter(self, name):
        printer = self._printers.pop(name, None)
        if printer:
            if printer.isConnected():
                printer.disconnect()
                printer.connectionStateChanged.disconnect(self._onPrinterConnectionStateChanged)
                Logger.log("d", "removePrinter, disconnecting [%s]..." % name)
        self.printerListChanged.emit()

    ##  Handler for when the connection state of one of the detected printers changes
    def _onPrinterConnectionStateChanged(self, key):
        if key not in self._printers:
            return
        if self._printers[key].isConnected():
            self.getOutputDeviceManager().addOutputDevice(self._printers[key])
        else:
            self.getOutputDeviceManager().removeOutputDevice(key)

    ##  Handler for zeroConf detection
    def _onServiceChanged(self, zeroconf, service_type, name, state_change):
        if state_change == ServiceStateChange.Added:
            Logger.log("d", "Bonjour service added: %s" % name)

            # First try getting info from zeroconf cache
            info = ServiceInfo(service_type, name, properties = {})
            for record in zeroconf.cache.entries_with_name(name.lower()):
                info.update_record(zeroconf, time.time(), record)

            for record in zeroconf.cache.entries_with_name(info.server):
                info.update_record(zeroconf, time.time(), record)
                if info.address:
                    break

            # Request more data if info is not complete
            if not info.address:
                Logger.log("d", "Trying to get address of %s", name)
                info = zeroconf.get_service_info(service_type, name)

            if info:
                type_of_device = info.properties.get(b"type", None)
                if type_of_device:
                    if type_of_device == b"printer":
                        address = '.'.join(map(lambda n: str(n), info.address))
                        self.addPrinterSignal.emit(str(name), address, info.properties)
                    else:
                        Logger.log("w", "The type of the found device is '%s', not 'printer'! Ignoring.." % type_of_device )
            else:
                Logger.log("w", "Could not get information about %s" % name)

        elif state_change == ServiceStateChange.Removed:
            Logger.log("d", "Bonjour service removed: %s" % name)
            self.removePrinterSignal.emit(str(name))

    @pyqtSlot()
    def openControlPanel(self):
        Logger.log("d", "Opening print jobs web UI...")
        selected_device = self.getOutputDeviceManager().getActiveDevice()
        if isinstance(selected_device, NetworkClusterPrinterOutputDevice.NetworkClusterPrinterOutputDevice):
            QDesktopServices.openUrl(QUrl(selected_device.getPrintJobsUrl()))
