from UM.Signal import Signal, SignalEmitter
from UM.PluginObject import PluginObject
from . import PrinterConnection

import threading
import platform
import glob
import time
import os

class USBPrinterManager(SignalEmitter,PluginObject):
    def __init__(self):
        super().__init__()
        self._serial_port_list = []
        self._printer_connections = []
        self._check_ports_thread = threading.Thread(target=self._updateConnectionList)
        self._check_ports_thread.daemon = True
        self._check_ports_thread.start()
        
        ## DEBUG CODE
        #time.sleep(1)
        #self.connectAllConnections()
        #time.sleep(5)
        #f = open("Orb.gcode")
        #lines = f.readlines()
        #print(len(lines))
        #print(len(self._printer_connections))
        #self.sendGCodeToAllActive(lines)
        #print("sending heat " , self.sendCommandToAllActive("M104 S190"))
        
    
    ##  Check all serial ports and create a PrinterConnection object for them.
    #   Note that this does not validate if the serial ports are actually usable!
    #   This is only done when the connect function is called.
    def _updateConnectionList(self):  
        while True: 
            temp_serial_port_list = self.getSerialPortList(only_list_usb = True)
            print(temp_serial_port_list)
            if temp_serial_port_list != self._serial_port_list: # Something changed about the list since we last changed something.
                disconnected_ports = [port for port in self._serial_port_list if port not in temp_serial_port_list ]
                self._serial_port_list = temp_serial_port_list
                for serial_port in self._serial_port_list:
                    if self.getConnectionByPort(serial_port) is None: #If it doesn't already exist, add it
                        if not os.path.islink(serial_port): #Only add the connection if it's a non symbolic link
                            self._printer_connections.append(PrinterConnection.PrinterConnection(serial_port))
                
                for serial_port in disconnected_ports: # Close connections and remove them from list.
                    connection = self.getConnectionByPort(serial_port)
                    connection.close()
                    self._printer_connections.remove(connection)
            time.sleep(5) #Throttle, as we don't need this information to be updated every single second.        
    
    ##  Attempt to connect with all possible connections. 
    def connectAllConnections(self):
        print("DERP DERP")
        for connection in self._printer_connections:
            print("connection ",connection)
            connection.connect()
    
    ##  send gcode to printer and start printing
    def sendGCodeByPort(self, serial_port, gcode_list):
        printer_connection = self.getConnectionByPort(serial_port)
        if printer_connection is not None:
            printer_connection.printGCode(gcode_list)
            return True
        return False
    
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
    
    ## Get a list of printer connection objects that are connected.
    def getActiveConnections(self):
        return [connection for connection in self._printer_connections if connection.isConnected()]
    
    ##  get a printer connection object by serial port
    def getConnectionByPort(self, serial_port):
        for printer_connection in self._printer_connections:
            if serial_port == printer_connection.getSerialPort():
                return printer_connection
        return None

    ##  Create a list of serial ports on the system.
    #   \param only_list_usb If true, only usb ports are listed
    def getSerialPortList(self,only_list_usb=False):
        base_list=[]
        if platform.system() == "Windows":
            try:
                key=_winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,"HARDWARE\\DEVICEMAP\\SERIALCOMM")
                i=0
                while True:
                    values = _winreg.EnumValue(key, i)
                    if not base_list or 'USBSER' in values[0]:
                        base_list+=[values[1]]
                    i+=1
            except:
                pass
        
        if base_list:
            base_list = base_list + glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*') + glob.glob("/dev/cu.usb*")
            base_list = filter(lambda s: not 'Bluetooth' in s, base_list) #Filter because mac sometimes puts them in the list
            #prev = profile.getMachineSetting('serial_port_auto')
            #if prev in base_list:
            #    base_list.remove(prev)
            #    base_list.insert(0, prev)
        else:
            base_list = base_list + glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*') + glob.glob("/dev/cu.*") + glob.glob("/dev/tty.usb*") + glob.glob("/dev/rfcomm*") + glob.glob('/dev/serial/by-id/*')
        #if version.isDevVersion() and not base_list:
            #base_list.append('VIRTUAL')
        return base_list