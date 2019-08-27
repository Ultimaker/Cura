# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from enum import IntEnum
from typing import Callable, List, Optional, Union

from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject, QTimer, QUrl
from PyQt5.QtWidgets import QMessageBox

from UM.Logger import Logger
from UM.Signal import signalemitter
from UM.Qt.QtApplication import QtApplication
from UM.FlameProfiler import pyqtSlot
from UM.Decorators import deprecated
from UM.i18n import i18nCatalog
from UM.OutputDevice.OutputDevice import OutputDevice

MYPY = False
if MYPY:
    from UM.FileHandler.FileHandler import FileHandler
    from UM.Scene.SceneNode import SceneNode
    from .Models.PrinterOutputModel import PrinterOutputModel
    from .Models.PrinterConfigurationModel import PrinterConfigurationModel
    from .FirmwareUpdater import FirmwareUpdater

i18n_catalog = i18nCatalog("cura")


##  The current processing state of the backend.
class ConnectionState(IntEnum):
    Closed = 0
    Connecting = 1
    Connected = 2
    Busy = 3
    Error = 4


class ConnectionType(IntEnum):
    NotConnected = 0
    UsbConnection = 1
    NetworkConnection = 2
    CloudConnection = 3


##  Printer output device adds extra interface options on top of output device.
#
#   The assumption is made the printer is a FDM printer.
#
#   Note that a number of settings are marked as "final". This is because decorators
#   are not inherited by children. To fix this we use the private counter part of those
#   functions to actually have the implementation.
#
#   For all other uses it should be used in the same way as a "regular" OutputDevice.
@signalemitter
class PrinterOutputDevice(QObject, OutputDevice):

    printersChanged = pyqtSignal()
    connectionStateChanged = pyqtSignal(str)
    acceptsCommandsChanged = pyqtSignal()

    # Signal to indicate that the material of the active printer on the remote changed.
    materialIdChanged = pyqtSignal()

    # # Signal to indicate that the hotend of the active printer on the remote changed.
    hotendIdChanged = pyqtSignal()

    # Signal to indicate that the info text about the connection has changed.
    connectionTextChanged = pyqtSignal()

    # Signal to indicate that the configuration of one of the printers has changed.
    uniqueConfigurationsChanged = pyqtSignal()

    def __init__(self, device_id: str, connection_type: "ConnectionType" = ConnectionType.NotConnected, parent: QObject = None) -> None:
        super().__init__(device_id = device_id, parent = parent) # type: ignore  # MyPy complains with the multiple inheritance

        self._printers = []  # type: List[PrinterOutputModel]
        self._unique_configurations = []   # type: List[PrinterConfigurationModel]

        self._monitor_view_qml_path = ""  # type: str
        self._monitor_component = None  # type: Optional[QObject]
        self._monitor_item = None  # type: Optional[QObject]

        self._control_view_qml_path = ""  # type: str
        self._control_component = None  # type: Optional[QObject]
        self._control_item = None  # type: Optional[QObject]

        self._accepts_commands = False  # type: bool

        self._update_timer = QTimer()  # type: QTimer
        self._update_timer.setInterval(2000)  # TODO; Add preference for update interval
        self._update_timer.setSingleShot(False)
        self._update_timer.timeout.connect(self._update)

        self._connection_state = ConnectionState.Closed  # type: ConnectionState
        self._connection_type = connection_type  # type: ConnectionType

        self._firmware_updater = None  # type: Optional[FirmwareUpdater]
        self._firmware_name = None  # type: Optional[str]
        self._address = ""  # type: str
        self._connection_text = ""  # type: str
        self.printersChanged.connect(self._onPrintersChanged)
        QtApplication.getInstance().getOutputDeviceManager().outputDevicesChanged.connect(self._updateUniqueConfigurations)

    @pyqtProperty(str, notify = connectionTextChanged)
    def address(self) -> str:
        return self._address

    def setConnectionText(self, connection_text):
        if self._connection_text != connection_text:
            self._connection_text = connection_text
            self.connectionTextChanged.emit()

    @pyqtProperty(str, constant=True)
    def connectionText(self) -> str:
        return self._connection_text

    def materialHotendChangedMessage(self, callback: Callable[[int], None]) -> None:
        Logger.log("w", "materialHotendChangedMessage needs to be implemented, returning 'Yes'")
        callback(QMessageBox.Yes)

    def isConnected(self) -> bool:
        return self._connection_state != ConnectionState.Closed and self._connection_state != ConnectionState.Error

    def setConnectionState(self, connection_state: "ConnectionState") -> None:
        if self._connection_state != connection_state:
            self._connection_state = connection_state
            self.connectionStateChanged.emit(self._id)

    @pyqtProperty(int, constant = True)
    def connectionType(self) -> "ConnectionType":
        return self._connection_type

    @pyqtProperty(int, notify = connectionStateChanged)
    def connectionState(self) -> "ConnectionState":
        return self._connection_state

    def _update(self) -> None:
        pass

    def _getPrinterByKey(self, key: str) -> Optional["PrinterOutputModel"]:
        for printer in self._printers:
            if printer.key == key:
                return printer

        return None

    def requestWrite(self, nodes: List["SceneNode"], file_name: Optional[str] = None, limit_mimetypes: bool = False,
                     file_handler: Optional["FileHandler"] = None, filter_by_machine: bool = False, **kwargs) -> None:
        raise NotImplementedError("requestWrite needs to be implemented")

    @pyqtProperty(QObject, notify = printersChanged)
    def activePrinter(self) -> Optional["PrinterOutputModel"]:
        if len(self._printers):
            return self._printers[0]
        return None

    @pyqtProperty("QVariantList", notify = printersChanged)
    def printers(self) -> List["PrinterOutputModel"]:
        return self._printers

    @pyqtProperty(QObject, constant = True)
    def monitorItem(self) -> QObject:
        # Note that we specifically only check if the monitor component is created.
        # It could be that it failed to actually create the qml item! If we check if the item was created, it will try to
        # create the item (and fail) every time.
        if not self._monitor_component:
            self._createMonitorViewFromQML()
        return self._monitor_item

    @pyqtProperty(QObject, constant = True)
    def controlItem(self) -> QObject:
        if not self._control_component:
            self._createControlViewFromQML()
        return self._control_item

    def _createControlViewFromQML(self) -> None:
        if not self._control_view_qml_path:
            return
        if self._control_item is None:
            self._control_item = QtApplication.getInstance().createQmlComponent(self._control_view_qml_path, {"OutputDevice": self})

    def _createMonitorViewFromQML(self) -> None:
        if not self._monitor_view_qml_path:
            return

        if self._monitor_item is None:
            self._monitor_item = QtApplication.getInstance().createQmlComponent(self._monitor_view_qml_path, {"OutputDevice": self})

    ##  Attempt to establish connection
    def connect(self) -> None:
        self.setConnectionState(ConnectionState.Connecting)
        self._update_timer.start()

    ##  Attempt to close the connection
    def close(self) -> None:
        self._update_timer.stop()
        self.setConnectionState(ConnectionState.Closed)

    ##  Ensure that close gets called when object is destroyed
    def __del__(self) -> None:
        self.close()

    @pyqtProperty(bool, notify = acceptsCommandsChanged)
    def acceptsCommands(self) -> bool:
        return self._accepts_commands

    @deprecated("Please use the protected function instead", "3.2")
    def setAcceptsCommands(self, accepts_commands: bool) -> None:
        self._setAcceptsCommands(accepts_commands)

    ##  Set a flag to signal the UI that the printer is not (yet) ready to receive commands
    def _setAcceptsCommands(self, accepts_commands: bool) -> None:
        if self._accepts_commands != accepts_commands:
            self._accepts_commands = accepts_commands

            self.acceptsCommandsChanged.emit()

    # Returns the unique configurations of the printers within this output device
    @pyqtProperty("QVariantList", notify = uniqueConfigurationsChanged)
    def uniqueConfigurations(self) -> List["PrinterConfigurationModel"]:
        return self._unique_configurations

    def _updateUniqueConfigurations(self) -> None:
        all_configurations = set()
        for printer in self._printers:
            if printer.printerConfiguration is not None and printer.printerConfiguration.hasAnyMaterialLoaded():
                all_configurations.add(printer.printerConfiguration)
            all_configurations.update(printer.availableConfigurations)
        new_configurations = sorted(all_configurations, key = lambda config: config.printerType)
        if new_configurations != self._unique_configurations:
            self._unique_configurations = new_configurations
            self.uniqueConfigurationsChanged.emit()

    # Returns the unique configurations of the printers within this output device
    @pyqtProperty("QStringList", notify = uniqueConfigurationsChanged)
    def uniquePrinterTypes(self) -> List[str]:
        return list(sorted(set([configuration.printerType for configuration in self._unique_configurations])))

    def _onPrintersChanged(self) -> None:
        for printer in self._printers:
            printer.configurationChanged.connect(self._updateUniqueConfigurations)
            printer.availableConfigurationsChanged.connect(self._updateUniqueConfigurations)

        # At this point there may be non-updated configurations
        self._updateUniqueConfigurations()

    ##  Set the device firmware name
    #
    #   \param name The name of the firmware.
    def _setFirmwareName(self, name: str) -> None:
        self._firmware_name = name

    ##  Get the name of device firmware
    #
    #   This name can be used to define device type
    def getFirmwareName(self) -> Optional[str]:
        return self._firmware_name

    def getFirmwareUpdater(self) -> Optional["FirmwareUpdater"]:
        return self._firmware_updater

    @pyqtSlot(str)
    def updateFirmware(self, firmware_file: Union[str, QUrl]) -> None:
        if not self._firmware_updater:
            return

        self._firmware_updater.updateFirmware(firmware_file)
