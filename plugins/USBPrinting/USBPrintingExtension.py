# Copyright (c) 2026 UltiMaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
from typing import List, Optional, Tuple

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot

from UM.Extension import Extension
from UM.Logger import Logger
from UM.Message import Message
from UM.PluginRegistry import PluginRegistry
from UM.i18n import i18nCatalog

from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.PrinterOutputDevice import ConnectionState

from .USBPrinterOutputDevice import LOG_COMM_PREFERENCE_KEY, getCommLogPath
from .USBMaintenance import (
    build_prep_script,
    build_purge_script,
    build_unload_script,
    clean_temperature,
    validate_maintenance_temps,
)

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
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Maintenance: Prepare + Level..."), self.maintenancePrepare)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Maintenance: Purge Nozzle..."), self.maintenancePurge)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Maintenance: Unload Filament..."), self.maintenanceUnload)

        preferences = CuraApplication.getInstance().getPreferences()
        preferences.addPreference(MANUAL_PORT_PREFERENCE_KEY, "")
        preferences.addPreference(MANUAL_BAUDRATE_PREFERENCE_KEY, "")
        preferences.addPreference(LOG_COMM_PREFERENCE_KEY, False)

        self._dialog = None  # type: ignore
        self._cached_ports = []  # type: List[str]
        self._pending_maintenance = None  # type: Optional[Tuple[str, List[str], int, int]]
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

    @pyqtProperty(bool, notify=settingsChanged)
    def logCommunication(self) -> bool:
        try:
            return bool(CuraApplication.getInstance().getPreferences().getValue(LOG_COMM_PREFERENCE_KEY))
        except Exception:
            return False

    @pyqtSlot(bool)
    def setLogCommunication(self, enabled: bool) -> None:
        try:
            CuraApplication.getInstance().getPreferences().setValue(LOG_COMM_PREFERENCE_KEY, bool(enabled))
        except Exception:
            Logger.logException("w", "USBPrinting settings: failed to store log flag.")
            return
        self.settingsChanged.emit()

    @pyqtProperty(str, constant=True)
    def logFilePath(self) -> str:
        try:
            return getCommLogPath()
        except Exception:
            return ""

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

    # ------------------------------------------------------------------
    # Maintenance routines. Temperatures come from the active material
    # profile (extruder stack) so TPU (unheated bed) and PLA (60 C bed)
    # behave correctly without hardcoded values.
    # ------------------------------------------------------------------

    def maintenancePrepare(self) -> None:
        hotend, bed = self._getMaintenanceTemps()
        status, reason = validate_maintenance_temps(hotend, bed)
        if status == "blocked":
            self._showMaintenanceMessage(reason, Message.MessageType.ERROR)
            return
        self._requestMaintenance(
            catalog.i18nc("@item:inmenu", "Prepare + Level"),
            build_prep_script(hotend, bed), hotend, bed, status, reason)

    def maintenancePurge(self) -> None:
        hotend, bed = self._getMaintenanceTemps()
        status, reason = validate_maintenance_temps(hotend, bed)
        if status == "blocked":
            self._showMaintenanceMessage(reason, Message.MessageType.ERROR)
            return
        self._requestMaintenance(
            catalog.i18nc("@item:inmenu", "Purge Nozzle"),
            build_purge_script(hotend), hotend, bed, status, reason)

    def maintenanceUnload(self) -> None:
        hotend, bed = self._getMaintenanceTemps()
        status, reason = validate_maintenance_temps(hotend, bed)
        if status == "blocked":
            self._showMaintenanceMessage(reason, Message.MessageType.ERROR)
            return
        self._requestMaintenance(
            catalog.i18nc("@item:inmenu", "Unload Filament"),
            build_unload_script(hotend), hotend, bed, status, reason)

    def _getMaintenanceTemps(self) -> Tuple[Optional[int], Optional[int]]:
        """(hotend, bed) in C from the active material profile, None when unavailable."""
        try:
            source = None
            try:
                from cura.Settings.ExtruderManager import ExtruderManager
                stacks = ExtruderManager.getInstance().getActiveExtruderStacks()
                if stacks:
                    source = stacks[0]
            except Exception:
                source = None
            if source is None:
                source = CuraApplication.getInstance().getGlobalContainerStack()
            if source is None:
                return None, None
            hotend = clean_temperature(source.getProperty("material_print_temperature", "value"))
            bed = clean_temperature(source.getProperty("material_bed_temperature", "value"))
            return hotend, bed
        except Exception:
            Logger.logException("w", "USB maintenance: could not resolve temperatures.")
            return None, None

    def _findIdleUsbDevice(self):
        """Connected, non-printing USB device, or None."""
        try:
            from .USBPrinterOutputDeviceManager import USBPrinterOutputDeviceManager
            from .USBPrinterOutputDevice import USBPrinterOutputDevice
            manager = USBPrinterOutputDeviceManager.getInstance()
            if manager is None:
                return None
            for device in manager._usb_output_devices.values():
                if isinstance(device, USBPrinterOutputDevice) \
                        and device.connectionState == ConnectionState.Connected \
                        and not device._is_printing:
                    return device
        except Exception:
            Logger.logException("w", "USB maintenance: device lookup failed.")
        return None

    def _requestMaintenance(self, label: str, script: List[str], hotend: int, bed: int,
                            status: str, reason: str) -> None:
        if status == "confirm_bed":
            # Bed target 0 is valid (TPU) but wrong for most materials: ask first.
            self._pending_maintenance = (label, script, hotend, bed)
            message = Message(
                text=catalog.i18nc("@message",
                                   "%s: bed target is 0 C (unheated bed, normal for TPU). Run anyway?" % label),
                title=catalog.i18nc("@message", "USB maintenance"),
                message_type=Message.MessageType.WARNING,
                lifetime=0)
            try:
                message.addAction("run", catalog.i18nc("@action:button", "Run anyway"), "", "")
                message.addAction("cancel", catalog.i18nc("@action:button", "Cancel"), "", "")
                message.actionTriggered.connect(self._onMaintenanceAction)
            except Exception:
                # No confirmation possible: fail safe, do not run.
                self._pending_maintenance = None
                Logger.logException("w", "USB maintenance: cannot ask for confirmation.")
                self._showMaintenanceMessage(
                    catalog.i18nc("@message", "%s: cannot ask for confirmation, cancelled." % label),
                    Message.MessageType.ERROR)
                return
            message.show()
            return
        self._startMaintenance(label, script, hotend, bed)

    def _onMaintenanceAction(self, message=None, action_id: str = "") -> None:
        pending, self._pending_maintenance = self._pending_maintenance, None
        try:
            if message is not None:
                message.hide()
        except Exception:
            pass
        if pending is None or action_id != "run":
            return
        label, script, hotend, bed = pending
        self._startMaintenance(label, script, hotend, bed)

    def _startMaintenance(self, label: str, script: List[str], hotend: int, bed: int) -> None:
        device = self._findIdleUsbDevice()
        if device is None:
            self._showMaintenanceMessage(
                catalog.i18nc("@message",
                              "%s: no connected USB printer (or a print is in progress)." % label),
                Message.MessageType.ERROR)
            return
        if not device.runMaintenanceScript(script, label):
            self._showMaintenanceMessage(
                catalog.i18nc("@message", "%s: could not start, check the USB connection." % label),
                Message.MessageType.ERROR)
            return
        self._showMaintenanceMessage(
            catalog.i18nc("@message", "%s started (hotend %d C, bed %d C). Watch the printer." % (label, hotend, bed)),
            Message.MessageType.POSITIVE)

    @staticmethod
    def _showMaintenanceMessage(text: str, message_type) -> None:
        try:
            Message(text=text,
                    title=catalog.i18nc("@message", "USB maintenance"),
                    message_type=message_type).show()
        except Exception:
            Logger.log("w", "USB maintenance: %s" % text)
