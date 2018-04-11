# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.i18n import i18nCatalog
from UM.OutputDevice.OutputDevice import OutputDevice
from PyQt5.QtCore import pyqtProperty, QObject, QTimer, pyqtSignal, QVariant
from PyQt5.QtWidgets import QMessageBox

from UM.Logger import Logger
from UM.Signal import signalemitter
from UM.Application import Application

from enum import IntEnum  # For the connection state tracking.
from typing import List, Optional

MYPY = False
if MYPY:
    from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
    from cura.PrinterOutput.ConfigurationModel import ConfigurationModel

i18n_catalog = i18nCatalog("cura")

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

    def __init__(self, device_id, parent = None):
        super().__init__(device_id = device_id, parent = parent)

        self._printers = []  # type: List[PrinterOutputModel]
        self._unique_configurations = []   # type: List[ConfigurationModel]

        self._monitor_view_qml_path = ""
        self._monitor_component = None
        self._monitor_item = None

        self._control_view_qml_path = ""
        self._control_component = None
        self._control_item = None

        self._qml_context = None
        self._accepts_commands = False

        self._update_timer = QTimer()
        self._update_timer.setInterval(2000)  # TODO; Add preference for update interval
        self._update_timer.setSingleShot(False)
        self._update_timer.timeout.connect(self._update)

        self._connection_state = ConnectionState.closed

        self._firmware_name = None
        self._address = ""
        self._connection_text = ""
        self.printersChanged.connect(self._onPrintersChanged)
        Application.getInstance().getOutputDeviceManager().outputDevicesChanged.connect(self._updateUniqueConfigurations)

    @pyqtProperty(str, notify = connectionTextChanged)
    def address(self):
        return self._address

    def setConnectionText(self, connection_text):
        if self._connection_text != connection_text:
            self._connection_text = connection_text
            self.connectionTextChanged.emit()

    @pyqtProperty(str, constant=True)
    def connectionText(self):
        return self._connection_text

    def materialHotendChangedMessage(self, callback):
        Logger.log("w", "materialHotendChangedMessage needs to be implemented, returning 'Yes'")
        callback(QMessageBox.Yes)

    def isConnected(self):
        return self._connection_state != ConnectionState.closed and self._connection_state != ConnectionState.error

    def setConnectionState(self, connection_state):
        if self._connection_state != connection_state:
            self._connection_state = connection_state
            self.connectionStateChanged.emit(self._id)

    @pyqtProperty(str, notify = connectionStateChanged)
    def connectionState(self):
        return self._connection_state

    def _update(self):
        pass

    def _getPrinterByKey(self, key) -> Optional["PrinterOutputModel"]:
        for printer in self._printers:
            if printer.key == key:
                return printer

        return None

    def requestWrite(self, nodes, file_name = None, filter_by_machine = False, file_handler = None, **kwargs):
        raise NotImplementedError("requestWrite needs to be implemented")

    @pyqtProperty(QObject, notify = printersChanged)
    def activePrinter(self) -> Optional["PrinterOutputModel"]:
        if len(self._printers):
            return self._printers[0]
        return None

    @pyqtProperty("QVariantList", notify = printersChanged)
    def printers(self):
        return self._printers

    @pyqtProperty(QObject, constant=True)
    def monitorItem(self):
        # Note that we specifically only check if the monitor component is created.
        # It could be that it failed to actually create the qml item! If we check if the item was created, it will try to
        # create the item (and fail) every time.
        if not self._monitor_component:
            self._createMonitorViewFromQML()
        return self._monitor_item

    @pyqtProperty(QObject, constant=True)
    def controlItem(self):
        if not self._control_component:
            self._createControlViewFromQML()
        return self._control_item

    def _createControlViewFromQML(self):
        if not self._control_view_qml_path:
            return
        if self._control_item is None:
            self._control_item = Application.getInstance().createQmlComponent(self._control_view_qml_path, {"OutputDevice": self})

    def _createMonitorViewFromQML(self):
        if not self._monitor_view_qml_path:
            return

        if self._monitor_item is None:
            self._monitor_item = Application.getInstance().createQmlComponent(self._monitor_view_qml_path, {"OutputDevice": self})

    ##  Attempt to establish connection
    def connect(self):
        self.setConnectionState(ConnectionState.connecting)
        self._update_timer.start()

    ##  Attempt to close the connection
    def close(self):
        self._update_timer.stop()
        self.setConnectionState(ConnectionState.closed)

    ##  Ensure that close gets called when object is destroyed
    def __del__(self):
        self.close()

    @pyqtProperty(bool, notify=acceptsCommandsChanged)
    def acceptsCommands(self):
        return self._accepts_commands

    ##  Set a flag to signal the UI that the printer is not (yet) ready to receive commands
    def _setAcceptsCommands(self, accepts_commands):
        if self._accepts_commands != accepts_commands:
            self._accepts_commands = accepts_commands

            self.acceptsCommandsChanged.emit()

    # Returns the unique configurations of the printers within this output device
    @pyqtProperty("QVariantList", notify = uniqueConfigurationsChanged)
    def uniqueConfigurations(self):
        return self._unique_configurations

    def _updateUniqueConfigurations(self):
        self._unique_configurations = list(set([printer.printerConfiguration for printer in self._printers if printer.printerConfiguration is not None]))
        self._unique_configurations.sort(key = lambda k: k.printerType)
        self.uniqueConfigurationsChanged.emit()

    def _onPrintersChanged(self):
        for printer in self._printers:
            printer.configurationChanged.connect(self._updateUniqueConfigurations)

        # At this point there may be non-updated configurations
        self._updateUniqueConfigurations()

    ##  Set the device firmware name
    #
    #   \param name \type{str} The name of the firmware.
    def _setFirmwareName(self, name):
        self._firmware_name = name

    ##  Get the name of device firmware
    #
    #   This name can be used to define device type
    def getFirmwareName(self):
        return self._firmware_name


##  The current processing state of the backend.
class ConnectionState(IntEnum):
    closed = 0
    connecting = 1
    connected = 2
    busy = 3
    error = 4
