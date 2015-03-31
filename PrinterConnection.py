from UM.Logger import Logger
from .avr_isp import stk500v2
import threading

class PrinterConnection():
    def __init__(self, serial_port):
        super().__init__()
        
        self._serial = None
        self._serial_port = serial_port
        self._error_state = None
        
        self._connect_thread = threading.Thread(target = self._connect)
        self._connect_thread.daemon = True
        
        self._is_connected = False
        self._is_connecting = False
        self._required_responses_auto_baud = 10
        
        self._listen_thread = threading.Thread(target=self._listen)
        self._listen_thread.daemon = True
        #self._listen_thread.start()
    def getSerialPort(self):
        return self._serial_port
    
    ##  Try to connect the serial. This simply starts the thread.
    def connect(self):
        self._connect_thread.start()
    
    def _connect(self): 
        self._is_connecting = True
        programmer = stk500v2.Stk500v2()
        programmer.connect(self._serial_port) #Connect with the serial, if this succeeds, it's an arduino based usb device.
        try:
            self._serial = programmer.leaveISP() 
            # Create new printer connection
            self.active_printer_connection = PrinterConnection(temp_serial)
            Logger.log('i', "Established connection on port %s" % serial_port)
        except ispBase.IspError as e:
            Logger.log('i', "Could not establish connection on %s: %s. Device is not arduino based." %(serial_port,str(e)))
        except:
            Logger.log('i', "Could not establish connection on %s, unknown reasons.  Device is not arduino based." % serial_port)
        
        if self._serial is None:
            #Device is not arduino based, so we need to cycle the baud rates.
            for baud_rate in self._getBaudrateList():
                timeout_time = time.time() + 5
                if self._serial is None:
                    self._serial = serial.Serial(str(self._port), baud_rate, timeout=5, writeTimeout=10000)
                else:
                    if not self.setBaudRate(baud_rate):
                        continue #Could not set the baud rate, go to the next
                sucesfull_responses = 0
                while timeout_time > time.time():
                    line = self._readline()
                    if "T:" in line:
                        self._serial.timeout = 0.5
                        self._sendCommand("M105") # Request temperature, as this should (if baudrate is correct) result in a command with 'T:' in it
                        sucesfull_responses += 1
                        if sucesfull_responses >= self._required_responses_auto_baud:
                            self.setIsConnected(True)
                            return 
            self.setIsConnected(False)
        else: 
            self.setIsConnected(True)
            return #Stop trying to connect, we are connected.
    
    def _listen(self):
        pass
    
    def setBaudRate(self, baud_rate):
        try:
            self._serial.baudrate = baud_rate
        except:
            return False
    
    def setIsConnected(self, state):
        self._is_connecting = False
        if state != state:
            self._is_connected = state
        else:
            Logger.log('w', "Printer connection state was not changed")
            
        if self._is_connected:
             self._listen_thread.start() #Start listening
        
    def close(self):
        pass #TODO: handle 
    
    def isConnected(self):
        return self._is_connected 
    
    def _listen(self):
        while True:
            line = self._readline()
            if line is None: 
                break #None is only returned when something went wrong. Stop listening
            
            if line.startswith('Error:'):
                #Oh YEAH, consistency.
                # Marlin reports an MIN/MAX temp error as "Error:x\n: Extruder switched off. MAXTEMP triggered !\n"
                #       But a bed temp error is reported as "Error: Temperature heated bed switched off. MAXTEMP triggered !!"
                #       So we can have an extra newline in the most common case. Awesome work people.
                if re.match('Error:[0-9]\n', line):
                        line = line.rstrip() + self._readline()
                #Skip the communication errors, as those get corrected.
                if 'Extruder switched off' in line or 'Temperature heated bed switched off' in line or 'Something is wrong, please turn off the printer.' in line:
                    if not self.hasError():
                        self._error_state = line[6:]
            if ' T:' in line or line.startswith('T:'): #Temperature message
                try:
                    print("TEMPERATURE", float(re.search("T: *([0-9\.]*)", line).group(1)))
                except:
                    pass
                if 'B:' in line: #Check if it's a bed temperature
                    try:
                        print("BED TEMPERATURE" ,float(re.search("B: *([0-9\.]*)", line).group(1)))
                    except:
                        pass
                #TODO: temperature changed callback
                
                
                
    def hasError(self):
        return False
        
        
    def _readline(self):
        if self._serial is None:
            return None
        try:
            ret = self._serial.readline()
        except:
            self._log("Unexpected error while reading serial port.")    
            self._errorValue = getExceptionString()
            self.close(True)
            return None
        if ret == '':
            return ''
        #self._log("Recv: %s" % (unicode(ret, 'ascii', 'replace').encode('ascii', 'replace').rstrip()))
        return ret
    
    
    ##  Create a list of baud rates at which we can communicate.
    #   \return list of int
    def _getBaudrateList():
        ret = [250000, 230400, 115200, 57600, 38400, 19200, 9600]
        #if profile.getMachineSetting('serial_baud_auto') != '':
            #prev = int(profile.getMachineSetting('serial_baud_auto'))
            #if prev in ret:
                #ret.remove(prev)
                #ret.insert(0, prev)
        return ret
            