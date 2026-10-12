# Copyright (c) 2026 UltiMaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
from typing import List

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot

from UM.Extension import Extension
from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry
from UM.i18n import i18nCatalog

from cura.CuraApplication import CuraApplication

catalog = i18nCatalog("cura")

# Preference keys. "" means "Auto". Must stay in sync with USBPrinterOutputDeviceManager.
MANUAL_PORT_PREFERENCE_KEY = "usb_printing/manual_port"
MANUAL_BAUDRATE_PREFERENCE_KEY = "usb_printing/manual_baudrate"

AUTO_LABEL = "Auto"

ALL_BAUD_RATES = [115200, 250000, 500000, 230400, 76800, 57600, 38400, 19200, 9600]


class USBPrintingExtension(QObject, Extension):
    """Extension that adds a settings dialog to pick COM port and baud rate manually.

    This avoids the very slow baud-rate auto-detection: when a baud rate is
    configured, USBPrinterOutputDevice.connect() opens the serial port directly
    instead of launching AutoDetectBaudJob. When a port is configured, the
    manager only watches that port instead of scanning everything.
    """

    portsChanged = pyqtSignal()
    settingsChanged = pyqtSignal()

    def __init__(self, parent=None) -> None:
        QObject.__init__(self, parent)
        Extension.__init__(self)

        self.setMenuName(catalog.i18nc("@item:inmenu", "USB Printing"))
        self.addMenuItem(catalog.i18nc("@item:inmenu", "USB Printing Settings..."), self.showSettingsDialog)

        preferences = CuraApplication.getInstance().getPreferences()
        preferences.addPreference(MANUAL_PORT_PREFERENCE_KEY, "")
        preferences.addPreference(MANUAL_BAUDRATE_PREFERENCE_KEY, "")

        self._dialog = None  # type: ignore
        self._cached_ports = []  # type: List[str]
        self.refreshSerialPorts()

    def showSettingsDialog(self) -> None:
        if self._dialog is not None:
            self.refreshSerialPorts()
            self._dialog.show()
            return
        plugin_path = PluginRegistry.getInstance().getPluginPath("USBPrinting")
        if not plugin_path:
            Logger.log("e", "USBPrinting settings dialog: cannot find plugin path.")
            return
        qml_path = os.path.join(plugin_path, "USBPrintingSettingsDialog.qml")
        self._dialog = CuraApplication.getInstance().createQmlSubWindow(qml_path, {"manager": self})
        if self._dialog is None:
            Logger.log("e", "USBPrinting settings dialog: failed to create QML component.")
            return
        self.refreshSerialPorts()
        self._dialog.show()

    @pyqtProperty("QStringList", notify=portsChanged)
    def serialPorts(self) -> List[str]:
        return list(self._cached_ports)

    @pyqtProperty("QStringList", constant=True)
    def baudRateOptions(self) -> List[str]:
        return [AUTO_LABEL] + [str(b) for b in ALL_BAUD_RATES]

    @pyqtProperty(str, notify=settingsChanged)
    def manualPort(self) -> str:
        try:
            value = CuraApplication.getInstance().getPreferences().getValue(MANUAL_PORT_PREFERENCE_KEY)
        except Exception:
            return ""
        return str(value) if value else ""

    @pyqtProperty(str, notify=settingsChanged)
    def manualBaudRate(self) -> str:
        try:
            value = CuraApplication.getInstance().getPreferences().getValue(MANUAL_BAUDRATE_PREFERENCE_KEY)
        except Exception:
            return ""
        if value is None or str(value).strip() in ("", "0", AUTO_LABEL):
            return ""
        return str(value)

    @pyqtSlot()
    def refreshSerialPorts(self) -> None:
        ports: List[str] = []
        try:
            from .USBPrinterOutputDeviceManager import USBPrinterOutputDeviceManager
            manager = USBPrinterOutputDeviceManager.getInstance()
            if manager is not None:
                from UM.Platform import Platform
                ports = manager.getSerialPortList(only_list_usb=Platform.isWindows())
            else:
                import serial.tools.list_ports
                ports = [p.device for p in serial.tools.list_ports.comports()]
        except Exception:
            Logger.logException("w", "USBPrinting settings: failed to list serial ports.")
            ports = []
        if ports != self._cached_ports:
            self._cached_ports = ports
            self.portsChanged.emit()

    @pyqtSlot(str)
    def setManualPort(self, port: str) -> None:
        if port in (AUTO_LABEL, None):
            port = ""
        port = (port or "").strip()
        preferences = CuraApplication.getInstance().getPreferences()
        try:
            preferences.setValue(MANUAL_PORT_PREFERENCE_KEY, port)
        except Exception:
            Logger.logException("w", "USBPrinting settings: failed to store manual port.")
            return
        self.settingsChanged.emit()

    @pyqtSlot(str)
    def setManualBaudRate(self, baudrate: str) -> None:
        if baudrate in (AUTO_LABEL, None):
            baudrate = ""
        baudrate = (baudrate or "").strip()
        if baudrate not in ("", AUTO_LABEL):
            try:
                baud_int = int(baudrate)
            except ValueError:
                Logger.log("w", "USBPrinting settings: ignoring invalid baud rate '%s'." % baudrate)
                return
            if baud_int not in ALL_BAUD_RATES:
                Logger.log("w", "USBPrinting settings: ignoring unknown baud rate '%s'." % baudrate)
                return
        preferences = CuraApplication.getInstance().getPreferences()
        try:
            preferences.setValue(MANUAL_BAUDRATE_PREFERENCE_KEY, baudrate)
        except Exception:
            Logger.logException("w", "USBPrinting settings: failed to store manual baud rate.")
            return
        self.settingsChanged.emit()

    @pyqtSlot()
    def reconnect(self) -> None:
        """Apply the stored port/baud rate by reconnecting the output device."""
        try:
            from .USBPrinterOutputDeviceManager import USBPrinterOutputDeviceManager
            manager = USBPrinterOutputDeviceManager.getInstance()
            if manager is None:
                Logger.log("w", "USBPrinting settings: no output device manager found.")
                return
            if hasattr(manager, "reconnectWithManualSettings"):
                manager.reconnectWithManualSettings()
            else:
                Logger.log("w", "USBPrinting settings: manager has no reconnectWithManualSettings().")
        except Exception:
            Logger.logException("e", "USBPrinting settings: reconnect failed.")
