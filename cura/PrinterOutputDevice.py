# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.i18n import i18nCatalog
from UM.OutputDevice.OutputDevice import OutputDevice
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject, QTimer, pyqtSignal, QUrl
from PyQt5.QtQml import QQmlComponent, QQmlContext
from enum import IntEnum  # For the connection state tracking.

from UM.Logger import Logger
from UM.Signal import signalemitter
from UM.Application import Application

import os

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

    def __init__(self, device_id, parent = None):
        super().__init__(device_id = device_id, parent = parent)

        self._printers = []

        self._monitor_view_qml_path = ""
        self._monitor_component = None
        self._monitor_item = None

        self._control_view_qml_path = ""
        self._control_component = None
        self._control_item = None

        self._qml_context = None

        self._update_timer = QTimer()
        self._update_timer.setInterval(2000)  # TODO; Add preference for update interval
        self._update_timer.setSingleShot(False)
        self._update_timer.timeout.connect(self._update)

        self._connection_state = ConnectionState.closed

    def isConnected(self):
        return self._connection_state != ConnectionState.closed and self._connection_state != ConnectionState.error

    def setConnectionState(self, connection_state):
        if self._connection_state != connection_state:
            self._connection_state = connection_state
            self.connectionStateChanged.emit(self._id)

    def _update(self):
        pass

    def _getPrinterByKey(self, key):
        for printer in self._printers:
            if printer.key == key:
                return printer

        return None

    def requestWrite(self, nodes, file_name = None, filter_by_machine = False, file_handler = None):
        raise NotImplementedError("requestWrite needs to be implemented")

    @pyqtProperty(QObject, notify = printersChanged)
    def activePrinter(self):
        if len(self._printers):

            return self._printers[0]
        return None

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

        path = QUrl.fromLocalFile(self._control_view_qml_path)

        # Because of garbage collection we need to keep this referenced by python.
        self._control_component = QQmlComponent(Application.getInstance()._engine, path)

        # Check if the context was already requested before (Printer output device might have multiple items in the future)
        if self._qml_context is None:
            self._qml_context = QQmlContext(Application.getInstance()._engine.rootContext())
            self._qml_context.setContextProperty("OutputDevice", self)

        self._control_item = self._control_component.create(self._qml_context)
        if self._control_item is None:
            Logger.log("e", "QQmlComponent status %s", self._control_component.status())
            Logger.log("e", "QQmlComponent error string %s", self._control_component.errorString())

    def _createMonitorViewFromQML(self):
        if not self._monitor_view_qml_path:
            return
        path = QUrl.fromLocalFile(self._monitor_view_qml_path)

        # Because of garbage collection we need to keep this referenced by python.
        self._monitor_component = QQmlComponent(Application.getInstance()._engine, path)

        # Check if the context was already requested before (Printer output device might have multiple items in the future)
        if self._qml_context is None:
            self._qml_context = QQmlContext(Application.getInstance()._engine.rootContext())
            self._qml_context.setContextProperty("OutputDevice", self)

        self._monitor_item = self._monitor_component.create(self._qml_context)
        if self._monitor_item is None:
            Logger.log("e", "QQmlComponent status %s", self._monitor_component.status())
            Logger.log("e", "QQmlComponent error string %s", self._monitor_component.errorString())

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


##  The current processing state of the backend.
class ConnectionState(IntEnum):
    closed = 0
    connecting = 1
    connected = 2
    busy = 3
    error = 4