# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import threading
import platform
import time
import serial.tools.list_ports

from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal

from UM.Logger import Logger
from UM.Resources import Resources
from UM.Signal import Signal, signalemitter
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from UM.i18n import i18nCatalog

from cura.PrinterOutputDevice import ConnectionState
from cura.CuraApplication import CuraApplication

from . import USBPrinterOutputDevice

i18n_catalog = i18nCatalog("cura")


##  Manager class that ensures that an USBPrinterOutput device is created for every connected USB printer.
@signalemitter
class USBPrinterOutputDeviceManager(QObject, OutputDevicePlugin):
    addUSBOutputDeviceSignal = Signal()
    progressChanged = pyqtSignal()

    def __init__(self, application, parent = None):
        if USBPrinterOutputDeviceManager.__instance is not None:
            raise RuntimeError("Try to create singleton '%s' more than once" % self.__class__.__name__)
        USBPrinterOutputDeviceManager.__instance = self

        super().__init__(parent = parent)
        self._application = application

        self._serial_port_list = []
        self._usb_output_devices = {}
        self._usb_output_devices_model = None
        self._update_thread = threading.Thread(target = self._updateThread)
        self._update_thread.setDaemon(True)

        self._check_updates = True

        self._application.applicationShuttingDown.connect(self.stop)
        # Because the model needs to be created in the same thread as the QMLEngine, we use a signal.
        self.addUSBOutputDeviceSignal.connect(self.addOutputDevice)

        self._application.globalContainerStackChanged.connect(self.updateUSBPrinterOutputDevices)

    # The method updates/reset the USB settings for all connected USB devices
    def updateUSBPrinterOutputDevices(self):
        for key, device in self._usb_output_devices.items():
            if isinstance(device, USBPrinterOutputDevice.USBPrinterOutputDevice):
                device.resetDeviceSettings()

    def start(self):
        self._check_updates = True
        self._update_thread.start()

    def stop(self, store_data: bool = True):
        self._check_updates = False

    def _onConnectionStateChanged(self, serial_port):
        if serial_port not in self._usb_output_devices:
            return

        changed_device = self._usb_output_devices[serial_port]
        if changed_device.connectionState == ConnectionState.connected:
            self.getOutputDeviceManager().addOutputDevice(changed_device)
        else:
            self.getOutputDeviceManager().removeOutputDevice(serial_port)

    def _updateThread(self):
        while self._check_updates:
            container_stack = self._application.getGlobalContainerStack()
            if container_stack is None:
                time.sleep(5)
                continue
            port_list = []  # Just an empty list; all USB devices will be removed.
            if container_stack.getMetaDataEntry("supports_usb_connection"):
                machine_file_formats = [file_type.strip() for file_type in container_stack.getMetaDataEntry("file_formats").split(";")]
                if "text/x-gcode" in machine_file_formats:
                    port_list = self.getSerialPortList(only_list_usb=True)
            self._addRemovePorts(port_list)
            time.sleep(5)

    @pyqtSlot(result = str)
    def getDefaultFirmwareName(self):
        # Check if there is a valid global container stack
        global_container_stack = self._application.getGlobalContainerStack()
        if not global_container_stack:
            Logger.log("e", "There is no global container stack. Can not update firmware.")
            return ""

        # The bottom of the containerstack is the machine definition
        machine_id = global_container_stack.getBottom().id
        machine_has_heated_bed = global_container_stack.getProperty("machine_heated_bed", "value")

        baudrate = 250000
        if platform.system() == "Linux":
            # Linux prefers a baudrate of 115200 here because older versions of
            # pySerial did not support a baudrate of 250000
            baudrate = 115200

        # If a firmware file is available, it should be specified in the definition for the printer
        hex_file = global_container_stack.getMetaDataEntry("firmware_file", None)
        if machine_has_heated_bed:
            hex_file = global_container_stack.getMetaDataEntry("firmware_hbk_file", hex_file)

        if hex_file:
            try:
                return Resources.getPath(CuraApplication.ResourceTypes.Firmware, hex_file.format(baudrate=baudrate))
            except FileNotFoundError:
                Logger.log("w", "Firmware file %s not found.", hex_file)
                return ""
        else:
            Logger.log("w", "There is no firmware for machine %s.", machine_id)
            return ""

    ##  Helper to identify serial ports (and scan for them)
    def _addRemovePorts(self, serial_ports):
        # First, find and add all new or changed keys
        for serial_port in list(serial_ports):
            if serial_port not in self._serial_port_list:
                self.addUSBOutputDeviceSignal.emit(serial_port)  # Hack to ensure its created in main thread
                continue
        self._serial_port_list = list(serial_ports)

        for port, device in self._usb_output_devices.items():
            if port not in self._serial_port_list:
                device.close()

    ##  Because the model needs to be created in the same thread as the QMLEngine, we use a signal.
    def addOutputDevice(self, serial_port):
        device = USBPrinterOutputDevice.USBPrinterOutputDevice(serial_port)
        device.connectionStateChanged.connect(self._onConnectionStateChanged)
        self._usb_output_devices[serial_port] = device
        device.connect()

    ##  Create a list of serial ports on the system.
    #   \param only_list_usb If true, only usb ports are listed
    def getSerialPortList(self, only_list_usb = False):
        base_list = []
        for port in serial.tools.list_ports.comports():
            if not isinstance(port, tuple):
                port = (port.device, port.description, port.hwid)
            if only_list_usb and not port[2].startswith("USB"):
                continue
            base_list += [port[0]]

        return list(base_list)

    __instance = None # type: USBPrinterOutputDeviceManager

    @classmethod
    def getInstance(cls, *args, **kwargs) -> "USBPrinterOutputDeviceManager":
        return cls.__instance
