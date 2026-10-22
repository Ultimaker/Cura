# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import threading
import time
import serial.tools.list_ports
from os import environ
from re import search

from PyQt6.QtCore import QObject, pyqtSignal

from UM.Platform import Platform
from UM.Signal import Signal, signalemitter
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from UM.i18n import i18nCatalog

from cura.PrinterOutput.PrinterOutputDevice import ConnectionState

from . import USBPrinterOutputDevice

i18n_catalog = i18nCatalog("cura")

USB_PRINT_PREFERENCE_KEY = "usb_printing/enabled"
USB_MANUAL_PORT_PREFERENCE_KEY = "usb_printing/manual_port"
USB_MANUAL_BAUDRATE_PREFERENCE_KEY = "usb_printing/manual_baudrate"

ALL_BAUD_RATES = [115200, 250000, 500000, 230400, 76800, 57600, 38400, 19200, 9600]

@signalemitter
class USBPrinterOutputDeviceManager(QObject, OutputDevicePlugin):
    """Manager class that ensures that an USBPrinterOutput device is created for every connected USB printer."""

    addUSBOutputDeviceSignal = Signal()
    progressChanged = pyqtSignal()

    def __init__(self, application, parent = None):
        if USBPrinterOutputDeviceManager.__instance is not None:
            raise RuntimeError("Try to create singleton '%s' more than once" % self.__class__.__name__)

        super().__init__(parent = parent)
        USBPrinterOutputDeviceManager.__instance = self

        self._application = application

        self._serial_port_list = []
        self._usb_output_devices = {}
        self._usb_output_devices_model = None
        self._update_thread = threading.Thread(target = self._updateThread)
        self._update_thread.daemon = True

        preferences = self._application.getPreferences()
        preferences.addPreference(USB_PRINT_PREFERENCE_KEY, False)
        preferences.addPreference(USB_MANUAL_PORT_PREFERENCE_KEY, "")
        preferences.addPreference(USB_MANUAL_BAUDRATE_PREFERENCE_KEY, "")
        preferences.addPreference(USBPrinterOutputDevice.LOG_COMM_PREFERENCE_KEY, False)
        self._check_updates = preferences.getValue(USB_PRINT_PREFERENCE_KEY)

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
        self._check_updates = self._application.getPreferences().getValue(USB_PRINT_PREFERENCE_KEY)
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

    def getManualPort(self) -> str:
        try:
            value = self._application.getPreferences().getValue(USB_MANUAL_PORT_PREFERENCE_KEY)
        except Exception:
            return ""
        return str(value).strip() if value else ""

    def getManualBaudRate(self):
        """Return the manually configured baud rate as int, or None when set to Auto."""
        try:
            value = self._application.getPreferences().getValue(USB_MANUAL_BAUDRATE_PREFERENCE_KEY)
        except Exception:
            return None
        if value is None or str(value).strip() in ("", "0", "Auto", "auto"):
            return None
        try:
            baud_rate = int(str(value).strip())
        except ValueError:
            return None
        if baud_rate not in ALL_BAUD_RATES:
            return None
        return baud_rate

    def reconnectWithManualSettings(self) -> None:
        """Close stale connections and force the scan loop to (re)connect with manual settings.

        Every tracked device is closed first: after a printer reboot the OS
        invalidates open handles, and creating a new device for a port whose
        old handle is still open leaves two handles on the same port, which
        surfaces as "Access denied" write failures.
        """
        for device in list(self._usb_output_devices.values()):
            try:
                device.close()
            except Exception:
                pass
        manual_port = self.getManualPort()
        if manual_port:
            # Force re-adding of the manual port on next pass (or right now).
            if manual_port in self._serial_port_list:
                self._serial_port_list.remove(manual_port)
            self._addRemovePorts([manual_port])
        else:
            # Back to auto: force a full rescan on the next update pass.
            self._serial_port_list = []

    def resolvePortList(self, auto_ports) -> list:
        """Apply the manual port override to an auto-scanned port list.

        Returns [manual_port] when a manual port is configured, else the
        auto-scanned list unchanged. Extracted for testability.
        """
        manual_port = self.getManualPort()
        if manual_port:
            return [manual_port]
        return list(auto_ports)

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
                    # We only limit listing usb on windows is a fix for connecting tty/cu printers on MacOS and Linux
                    port_list = self.getSerialPortList(only_list_usb=Platform.isWindows())
                    # Only watch the manually selected port when configured. This also avoids
                    # probing unrelated serial devices every 5 seconds.
                    port_list = self.resolvePortList(port_list)
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

        manual_port = self.getManualPort()
        if manual_port and serial_port != manual_port:
            return
        # Never stack two devices (two open serial handles) on the same port:
        # the 5 s scan loop and "Reconnect now" can both trigger a re-add while
        # the old device is still tracked. Closing first also lets the
        # connection-state handler drop the stale device from Cura.
        old_device = self._usb_output_devices.get(serial_port)
        if old_device is not None:
            try:
                old_device.close()
            except Exception:
                pass
        manual_baud_rate = self.getManualBaudRate()
        device = USBPrinterOutputDevice.USBPrinterOutputDevice(serial_port, baud_rate = manual_baud_rate)
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
