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
    
    ##  Check all serial ports and create a PrinterConnection object for them.
    #   Note that this does not validate if the serial ports are actually usable!
    #   This is only done when the connect function is called.
    def _updateConnectionList(self):  
        while True: 
            temp_serial_port_list = self.getSerialPortList(only_list_usb = True)
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
    
    def connectAllConnections(self):
        for connection in self._printer_connections:
            connection.connect()
            
    def getActiveConnections(self):
        return [connection for connection in self._printer_connections if connection.isConnected()]
    
    ##  
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