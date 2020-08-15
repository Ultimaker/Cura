# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import threading
import time
import serial.tools.list_ports
from os import environ
from re import search

from PyQt5.QtCore import QObject, pyqtSignal

from UM.Signal import Signal, signalemitter
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from UM.i18n import i18nCatalog

from cura.PrinterOutput.PrinterOutputDevice import ConnectionState

from . import USBPrinterOutputDevice

i18n_catalog = i18nCatalog("cura")


@signalemitter
class USBPrinterOutputDeviceManager(QObject, OutputDevicePlugin):
    """Manager class that ensures that an USBPrinterOutput device is created for every connected USB printer."""

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
        for device in self._usb_output_devices.values():
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
        if changed_device.connectionState == ConnectionState.Connected:
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

    def _addRemovePorts(self, serial_ports):
        """Helper to identify serial ports (and scan for them)"""

        # First, find and add all new or changed keys
        for serial_port in list(serial_ports):
            if serial_port not in self._serial_port_list:
                self.addUSBOutputDeviceSignal.emit(serial_port)  # Hack to ensure its created in main thread
                continue
        self._serial_port_list = list(serial_ports)

        for port, device in self._usb_output_devices.items():
            if port not in self._serial_port_list:
                device.close()

    def addOutputDevice(self, serial_port):
        """Because the model needs to be created in the same thread as the QMLEngine, we use a signal."""

        device = USBPrinterOutputDevice.USBPrinterOutputDevice(serial_port)
        device.connectionStateChanged.connect(self._onConnectionStateChanged)
        self._usb_output_devices[serial_port] = device
        device.connect()

    def getSerialPortList(self, only_list_usb = False):
        """Create a list of serial ports on the system.

        :param only_list_usb: If true, only usb ports are listed
        """
        base_list = []
        try:
            port_list = serial.tools.list_ports.comports()
        except TypeError:  # Bug in PySerial causes a TypeError if port gets disconnected while processing.
            port_list = []
        for port in port_list:
            if not isinstance(port, tuple):
                port = (port.device, port.description, port.hwid)
            if not port[2]:  # HWID may be None if the device is not USB or the system doesn't report the type.
                continue
            if only_list_usb and not port[2].startswith("USB"):
                continue

            # To prevent cura from messing with serial ports of other devices,
            # filter by regular expressions passed in as environment variables.
            # Get possible patterns with python3 -m serial.tools.list_ports -v

            # set CURA_DEVICENAMES=USB[1-9] -> e.g. not matching /dev/ttyUSB0
            pattern = environ.get('CURA_DEVICENAMES')
            if pattern and not search(pattern, port[0]):
                continue

            # set CURA_DEVICETYPES=CP2102 -> match a type of serial converter
            pattern = environ.get('CURA_DEVICETYPES')
            if pattern and not search(pattern, port[1]):
                continue

            # set CURA_DEVICEINFOS=LOCATION=2-1.4 -> match a physical port
            # set CURA_DEVICEINFOS=VID:PID=10C4:EA60 -> match a vendor:product
            pattern = environ.get('CURA_DEVICEINFOS')
            if pattern and not search(pattern, port[2]):
                continue

            base_list += [port[0]]

        return list(base_list)

    __instance = None # type: USBPrinterOutputDeviceManager

    @classmethod
    def getInstance(cls, *args, **kwargs) -> "USBPrinterOutputDeviceManager":
        return cls.__instance
