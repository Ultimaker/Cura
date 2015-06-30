# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Signal import Signal, SignalEmitter
from . import PrinterConnection
from UM.Application import Application
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Resources import Resources
from UM.Logger import Logger
import threading
import platform
import glob
import time
import os
import sys
from UM.Extension import Extension

from PyQt5.QtQuick import QQuickView
from PyQt5.QtCore import QUrl, QObject, pyqtSlot, pyqtProperty, pyqtSignal

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

class USBPrinterManager(QObject, SignalEmitter, Extension):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._serial_port_list = []
        self._printer_connections = []
        self._check_ports_thread = threading.Thread(target = self._updateConnectionList)
        self._check_ports_thread.daemon = True
        self._check_ports_thread.start()
        
        self._progress = 0

        self._control_view = None
        self._firmware_view = None
        self._extruder_temp = 0
        self._bed_temp = 0
        self._error_message = "" 
        
        ## Add menu item to top menu of the application.
        self.setMenuName("Firmware")
        self.addMenuItem(i18n_catalog.i18n("Update Firmware"), self.updateAllFirmware)
    
    pyqtError = pyqtSignal(str, arguments = ["amount"])
    processingProgress = pyqtSignal(float, arguments = ["amount"])
    pyqtExtruderTemperature = pyqtSignal(float, arguments = ["amount"])
    pyqtBedTemperature = pyqtSignal(float, arguments = ["amount"])
    
    ##  Show firmware interface.
    #   This will create the view if its not already created.
    def spawnFirmwareInterface(self, serial_port):
        if self._firmware_view is None:
            self._firmware_view = QQuickView()
            self._firmware_view.engine().rootContext().setContextProperty("manager",self)
            self._firmware_view.setSource(QUrl("plugins/USBPrinting/FirmwareUpdateWindow.qml"))
        self._firmware_view.show()
    
    ##  Show control interface.
    #   This will create the view if its not already created.
    def spawnControlInterface(self,serial_port):
        if self._control_view is None:
            self._control_view = QQuickView()
            self._control_view.engine().rootContext().setContextProperty("manager",self)
            self._control_view.setSource(QUrl("plugins/USBPrinting/ControlWindow.qml"))
        self._control_view.show()

    @pyqtProperty(float,notify = processingProgress)
    def progress(self):
        return self._progress

    @pyqtProperty(float,notify = pyqtExtruderTemperature)
    def extruderTemperature(self):
        return self._extruder_temp

    @pyqtProperty(float,notify = pyqtBedTemperature)
    def bedTemperature(self):
        return self._bed_temp

    @pyqtProperty(str,notify = pyqtError)
    def error(self):
        return self._error_message
    
    ##  Check all serial ports and create a PrinterConnection object for them.
    #   Note that this does not validate if the serial ports are actually usable!
    #   This (the validation) is only done when the connect function is called.
    def _updateConnectionList(self):  
        while True: 
            temp_serial_port_list = self.getSerialPortList(only_list_usb = True)
            if temp_serial_port_list != self._serial_port_list: # Something changed about the list since we last changed something.
                disconnected_ports = [port for port in self._serial_port_list if port not in temp_serial_port_list ]
                self._serial_port_list = temp_serial_port_list
                for serial_port in self._serial_port_list:
                    if self.getConnectionByPort(serial_port) is None: # If it doesn't already exist, add it
                        if not os.path.islink(serial_port): # Only add the connection if it's a non symbolic link
                            connection = PrinterConnection.PrinterConnection(serial_port)
                            connection.connect()
                            connection.connectionStateChanged.connect(self.serialConectionStateCallback)
                            connection.progressChanged.connect(self.onProgress)
                            connection.onExtruderTemperatureChange.connect(self.onExtruderTemperature)
                            connection.onBedTemperatureChange.connect(self.onBedTemperature)
                            connection.onError.connect(self.onError)
                            self._printer_connections.append(connection)
                
                for serial_port in disconnected_ports: # Close connections and remove them from list.
                    connection = self.getConnectionByPort(serial_port)
                    if connection != None:
                        self._printer_connections.remove(connection)
                        connection.close()
            time.sleep(5) # Throttle, as we don"t need this information to be updated every single second.
    
    def updateAllFirmware(self):
        if not self._printer_connections:
            Logger.log("e", "No printer connected to update firmware of!")
            return

        self.spawnFirmwareInterface("")
        for printer_connection in self._printer_connections:
            try:
                printer_connection.updateFirmware(Resources.getPath(Resources.FirmwareLocation, self._getDefaultFirmwareName()))
            except FileNotFoundError:
                continue
            
    def updateFirmwareBySerial(self, serial_port):
        printer_connection = self.getConnectionByPort(serial_port)
        if printer_connection is not None:
            self.spawnFirmwareInterface(printer_connection.getSerialPort())
            printer_connection.updateFirmware(Resources.getPath(Resources.FirmwareLocation, self._getDefaultFirmwareName()))
        
    def _getDefaultFirmwareName(self):
        machine_type = Application.getInstance().getActiveMachine().getTypeID()
        firmware_name = ""
        baudrate = 250000
        if sys.platform.startswith("linux"):
                baudrate = 115200
        if machine_type == "ultimaker_original":
            firmware_name = "MarlinUltimaker"
            firmware_name += "-%d" % (baudrate)
        elif machine_type == "ultimaker_original_plus":
            firmware_name = "MarlinUltimaker-UMOP-%d" % (baudrate)
        elif machine_type == "Witbox":
            return "MarlinWitbox.hex"
        elif machine_type == "ultimaker2go":
            return "MarlinUltimaker2go.hex"
        elif machine_type == "ultimaker2extended":
            return "MarlinUltimaker2extended.hex"
        elif machine_type == "ultimaker2":
            return "MarlinUltimaker2.hex"

        ##TODO: Add check for multiple extruders
        
        if firmware_name != "":
            firmware_name += ".hex"
        return firmware_name

    ##  Callback for extruder temperature change  
    def onExtruderTemperature(self, serial_port, index, temperature):
        self._extruder_temp = temperature
        self.pyqtExtruderTemperature.emit(temperature)
    
    ##  Callback for bed temperature change    
    def onBedTemperature(self, serial_port,temperature):
        self._bed_temperature = temperature
        self.pyqtBedTemperature.emit(temperature)
    
    ##  Callback for error
    def onError(self, error):
        self._error_message = error
        self.pyqtError.emit(error)
        
    ##  Callback for progress change
    def onProgress(self, progress, serial_port):
        self._progress = progress
        self.processingProgress.emit(progress)

    ##  Attempt to connect with all possible connections. 
    def connectAllConnections(self):
        for connection in self._printer_connections:
            connection.connect()
    
    ##  Send gcode to printer and start printing
    def sendGCodeByPort(self, serial_port, gcode_list):
        printer_connection = self.getConnectionByPort(serial_port)
        if printer_connection is not None:
            printer_connection.printGCode(gcode_list)
            return True
        return False
    
    @pyqtSlot()
    def cancelPrint(self):
        for printer_connection in self.getActiveConnections():
            printer_connection.cancelPrint()
    
    ##  Send gcode to all active printers.
    #   \return True if there was at least one active connection.
    def sendGCodeToAllActive(self, gcode_list):
        for printer_connection in self.getActiveConnections():
            printer_connection.printGCode(gcode_list)
        if len(self.getActiveConnections()):
            return True
        else:
            return False
    
    ##  Send a command to a printer indentified by port
    #   \param serial port String indentifieing the port
    #   \param command String with the g-code command to send.
    #   \return True if connection was found, false otherwise
    def sendCommandByPort(self, serial_port, command):
        printer_connection = self.getConnectionByPort(serial_port)
        if printer_connection is not None:
            printer_connection.sendCommand(command)
            return True
        return False
    
    ##  Send a command to all active (eg; connected) printers
    #   \param command String with the g-code command to send.
    #   \return True if at least one connection was found, false otherwise
    def sendCommandToAllActive(self, command):
        for printer_connection in self.getActiveConnections():
            printer_connection.sendCommand(command)
        if len(self.getActiveConnections()):
            return True
        else: 
            return False
    
    ##  Callback if the connection state of a connection is changed.
    #   This adds or removes the connection as a possible output device.
    def serialConectionStateCallback(self, serial_port):
        connection = self.getConnectionByPort(serial_port)
        if connection.isConnected():
            Application.getInstance().addOutputDevice(serial_port, {
                "id": serial_port,
                "function": self.spawnControlInterface,
                "description": "Print through USB {0}".format(serial_port),
                "shortDescription": "Print through USB",
                "icon": "print_usb",
                "priority": 1
            })
        else:
            Application.getInstance().removeOutputDevice(serial_port)
    
    @pyqtSlot()        
    def startPrint(self):
        gcode_list = getattr(Application.getInstance().getController().getScene(), "gcode_list", None)
        if gcode_list:
            final_list = []
            for gcode in gcode_list:
                final_list += gcode.split("\n")
            self.sendGCodeToAllActive(gcode_list)
    
    ##  Get a list of printer connection objects that are connected.
    def getActiveConnections(self):
        return [connection for connection in self._printer_connections if connection.isConnected()]
    
    ##  Get a printer connection object by serial port
    def getConnectionByPort(self, serial_port):
        for printer_connection in self._printer_connections:
            if serial_port == printer_connection.getSerialPort():
                return printer_connection
        return None

    ##  Create a list of serial ports on the system.
    #   \param only_list_usb If true, only usb ports are listed
    def getSerialPortList(self,only_list_usb=False):
        base_list = []
        if platform.system() == "Windows":
            import winreg
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,"HARDWARE\\DEVICEMAP\\SERIALCOMM")
                i = 0
                while True:
                    values = winreg.EnumValue(key, i)
                    if not base_list or "USBSER" in values[0]:
                        base_list += [values[1]]
                    i += 1
            except Exception as e:
                pass
        
        if base_list:
            base_list = base_list + glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*") + glob.glob("/dev/cu.usb*")
            base_list = filter(lambda s: "Bluetooth" not in s, base_list) # Filter because mac sometimes puts them in the list
        else:
            base_list = base_list + glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*") + glob.glob("/dev/cu.*") + glob.glob("/dev/tty.usb*") + glob.glob("/dev/rfcomm*") + glob.glob("/dev/serial/by-id/*")
        return base_list
