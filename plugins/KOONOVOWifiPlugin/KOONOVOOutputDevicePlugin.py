# coding=utf-8
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from . import KOONOVOOutputDevice, SaveOutputDevice

from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange, ServiceInfo
from UM.Signal import Signal, signalemitter
from UM.Application import Application
from UM.Logger import Logger
from UM.Preferences import Preferences
from PyQt5.QtCore import QUrl

from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty
from PyQt5.QtGui import QDesktopServices
from queue import Queue
from threading import Event, Thread

from UM.Message import Message
from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

import time
import json
import re
import os

from cura.CuraApplication import CuraApplication

@signalemitter
class KOONOVOOutputDevicePlugin(QObject, OutputDevicePlugin):
    def __init__(self):
        super().__init__()
        self._zero_conf = None
        self._browser = None
        self._printers = {}
        self._discovered_devices = {}

        self._error_message = None

        self._old_printers = []

        self.addPrinterSignal.connect(self.addPrinter)
        self.removePrinterSignal.connect(self.removePrinter)

        self._preferences = Application.getInstance().getPreferences()
        self._preferences.addPreference("KOONOVOwifi/manual_instances", "")
        self._preferences.addPreference("local_file/last_used_type", "")
        self._preferences.addPreference("local_file/dialog_save_path", "")
        self._manual_instances = self._preferences.getValue("KOONOVOwifi/manual_instances").split(",")
        Application.getInstance().globalContainerStackChanged.connect(self.reCheckConnections)

        self._service_changed_request_queue = Queue()
        self._service_changed_request_event = Event()
        self._service_changed_request_thread = Thread(target=self._handleOnServiceChangedRequests,
                                                      daemon=True)
        self._service_changed_request_thread.start()

        self._changestage = False

    addPrinterSignal = Signal()
    removePrinterSignal = Signal()
    printerListChanged = Signal()

    def start(self):

        self.startDiscovery()

    def startDiscovery(self):
        self.stop()
        self.getOutputDeviceManager().addOutputDevice(SaveOutputDevice.SaveOutputDevice())
        if self._browser:
            self._browser.cancel()
            self._browser = None
            self._old_printers = [printer_name for printer_name in self._printers]
            self._printers = {}
            self.printerListChanged.emit()
        self._zero_conf = Zeroconf()
        self._browser = ServiceBrowser(self._zero_conf, u'_KOONOVO._tcp.local.', [self._appendServiceChangedRequest])
        for address in self._manual_instances:
            if address:
                self.addManualPrinter(address)

    def addManualPrinter(self, address):
        if address not in self._manual_instances:
            self._manual_instances.append(address)
            self._preferences.setValue("KOONOVOwifi/manual_instances", ",".join(self._manual_instances))

        instance_name = "manual:%s" % address
        properties = {
            b"name": address.encode("utf-8"),
            b"address": address.encode("utf-8"),
            b"manual": b"true",
            b"incomplete": b"false"
        }

        if instance_name not in self._printers:
            # Add a preliminary printer instance
            self.addPrinter(instance_name, address, properties)

        # self.checkManualPrinter(address)
        # self.checkClusterPrinter(address)

    def removeManualPrinter(self, key, address=None):
        if key in self._printers:
            if not address:
                address = self._printers[key].ipAddress
            self.removePrinter(key)

        if address in self._manual_instances:
            self._manual_instances.remove(address)
            self._preferences.setValue("KOONOVOwifi/manual_instances", ",".join(self._manual_instances))

    def stop(self):
        # self.getOutputDeviceManager().removeOutputDevice("save_with_screenshot")
        if self._zero_conf is not None:
            Logger.log("d", "zeroconf close...")
            self._zero_conf.close()

    def getPrinters(self):
        return self._printers

    def disConnections(self,key):
        Logger.log("d", "disConnections change %s" % key)
        # for keys in self._printers:
        #     if self._printers[key].isConnected():
        #         Logger.log("d", "Closing connection [%s]..." % key)
        if key in self._printers:
            self._printers[key].disconnect()
                # self._printers[key].connectionStateChanged.disconnect(self._onPrinterConnectionStateChanged)
            self.getOutputDeviceManager().removeOutputDevice(key)
        preferences = Application.getInstance().getPreferences()
        preferences.addPreference("KOONOVOwifi/stopupdate", "True")


    def reCheckConnections(self):
        active_machine = Application.getInstance().getGlobalContainerStack()
        Logger.log("d", "GlobalContainerStack change %s" % active_machine.getMetaDataEntry("KOONOVO_network_key"))
        if not active_machine:
            return

        for key in self._printers:
            if key == active_machine.getMetaDataEntry("KOONOVO_network_key"):
                if not self._printers[key].isConnected():
                    Logger.log("d", "Connecting [%s]..." % key)
                    self._printers[key].connect()
                    self._printers[key].connectionStateChanged.connect(self._onPrinterConnectionStateChanged)
            else:
                if self._printers[key].isConnected():
                    Logger.log("d", "Closing connection [%s]..." % key)
                    self._printers[key].disconnect()
                    self._printers[key].connectionStateChanged.disconnect(self._onPrinterConnectionStateChanged)

    def addPrinter(self, name, address, properties):
        printer = KOONOVOOutputDevice.KOONOVOOutputDevice(name, address, properties)
        # self._api_prefix = "/"
        # printer = NetworkPrinterOutputDevice.NetworkPrinterOutputDevice(name, address, properties, self._api_prefix)
        self._printers[printer.getKey()] = printer
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack and printer.getKey() == global_container_stack.getMetaDataEntry("KOONOVO_network_key"):
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
    
    def printertrytoconnect(self):
        Logger.log("d", "KOONOVO printertrytoconnect")
        self._changestage = True

    def _onPrinterConnectionStateChanged(self, key):
        if key not in self._printers:
            return
        # Logger.log("d", "KOONOVO add output device %s" % self._printers[key].isConnected())
        if self._printers[key].isConnected():
            # Logger.log("d", "KOONOVO add output device--------ok--------- %s" % self._printers[key].isConnected())
            if self._error_message:
                self._error_message.hide()
            name = "Printer connect success"
            if CuraApplication.getInstance().getPreferences().getValue("general/language") == "zh_CN":
                name = "打印机连接成功"
            else:
                name = "Printer connect success"
            self._error_message = Message(name)
            self._error_message.show()
            self.getOutputDeviceManager().addOutputDevice(self._printers[key])
            # preferences = Application.getInstance().getPreferences()
            # if preferences.getValue("KOONOVOwifi/changestage"):
            #     preferences.addPreference("KOONOVOwifi/changestage", "False")     
            #     CuraApplication.getInstance().getController().setActiveStage("MonitorStage")
        else:
            # self.getOutputDeviceManager().removeOutputDevice(key)
            global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
            if global_container_stack:
                meta_data = global_container_stack.getMetaData()
                if "KOONOVO_network_key" in meta_data:
                    localkey = global_container_stack.getMetaDataEntry("KOONOVO_network_key")
                    # global_container_stack.setMetaDataEntry("KOONOVO_network_key", key)
                    # global_container_stack.removeMetaDataEntry(
                    # "network_authentication_id")
                    # global_container_stack.removeMetaDataEntry(
                    # "network_authentication_key")
                    # Logger.log("d", "KOONOVO localkey--------ok--------- %s" % localkey)
                    # Logger.log("d", "KOONOVO key--------ok--------- %s" % key)
                    if localkey != key and key in self._printers:
                        # self.getOutputDeviceManager().connect()          
                        self.getOutputDeviceManager().removeOutputDevice(key)
        # else:
        #     if self._error_message:
        #         self._error_message.hide()
        #     self._error_message = Message(i18n_catalog.i18nc("@info:status", "Printer connect failed"))
        #     self._error_message.show()
        # else:
        #     Logger.log("d", "KOONOVO add output device--------ok--------- %s" % self._printers[key].isConnected())
        #     self._printers[key].disconnect()
            # self._printers[key].connectionStateChanged.disconnect(self._onPrinterConnectionStateChanged)

    def _onServiceChanged(self, zeroconf, service_type, name, state_change):
        if state_change == ServiceStateChange.Added:
            Logger.log("d", "Bonjour service added: %s" % name)

            # First try getting info from zeroconf cache
            info = ServiceInfo(service_type, name, properties={})
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
                        if address in self._excluded_addresses:
                            Logger.log("d",
                                       "The IP address %s of the printer \'%s\' is not correct. Trying to reconnect.",
                                       address, name)
                            return False  # When getting the localhost IP, then try to reconnect
                        self.addPrinterSignal.emit(str(name), address, info.properties)
                    else:
                        Logger.log("w",
                                   "The type of the found device is '%s', not 'printer'! Ignoring.." % type_of_device)
            else:
                Logger.log("w", "Could not get information about %s" % name)
                return False

        elif state_change == ServiceStateChange.Removed:
            Logger.log("d", "Bonjour service removed: %s" % name)
            self.removePrinterSignal.emit(str(name))

        return True

    def _appendServiceChangedRequest(self, zeroconf, service_type, name, state_change):
        # append the request and set the event so the event handling thread can pick it up
        item = (zeroconf, service_type, name, state_change)
        self._service_changed_request_queue.put(item)
        self._service_changed_request_event.set()

    def _handleOnServiceChangedRequests(self):
        while True:
            # wait for the event to be set
            self._service_changed_request_event.wait(timeout=5.0)
            # stop if the application is shutting down
            if Application.getInstance().isShuttingDown():
                return

            self._service_changed_request_event.clear()

            # handle all pending requests
            reschedule_requests = []  # a list of requests that have failed so later they will get re-scheduled
            while not self._service_changed_request_queue.empty():
                request = self._service_changed_request_queue.get()
                zeroconf, service_type, name, state_change = request
                try:
                    result = self._onServiceChanged(zeroconf, service_type, name, state_change)
                    if not result:
                        reschedule_requests.append(request)
                except Exception:
                    Logger.logException("e",
                                        "Failed to get service info for [%s] [%s], the request will be rescheduled",
                                        service_type, name)
                    reschedule_requests.append(request)

            # re-schedule the failed requests if any
            if reschedule_requests:
                for request in reschedule_requests:
                    self._service_changed_request_queue.put(request)

    @pyqtSlot()
    def openControlPanel(self):
        Logger.log("d", "Opening print jobs web UI...")
        selected_device = self.getOutputDeviceManager().getActiveDevice()
        self._monitor_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MonitorItem4x.qml")
        self.__additional_components_view = Application.getInstance().createQmlComponent(self._monitor_view_qml_path, {"manager": self})
        # if isinstance(selected_device, KOONOVOOutputDevice.KOONOVOOutputDevice):
            # QDesktopServices.openUrl(QUrl(selected_device.getPrintJobsUrl()))
