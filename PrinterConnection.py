from UM.Logger import Logger
from .avr_isp import stk500v2, ispBase
import serial
import threading
import time
import queue
import re
import functools

from UM.Application import Application
from UM.Signal import Signal, SignalEmitter


class PrinterConnection(SignalEmitter):
    def __init__(self, serial_port):
        super().__init__()
        
        self._serial = None
        self._serial_port = serial_port
        self._error_state = None
        
        self._connect_thread = threading.Thread(target = self._connect)
        self._connect_thread.daemon = True
        
        # Printer is connected
        self._is_connected = False
        
        # Printer is in the process of connecting
        self._is_connecting = False
        
        # The baud checking is done by sending a number of m105 commands to the printer and waiting for a readable
        # response. If the baudrate is correct, this should make sense, else we get giberish.
        self._required_responses_auto_baud = 10
        
        self._progress = 0
        
        self._listen_thread = threading.Thread(target=self._listen)
        self._listen_thread.daemon = True
        
        self._heatup_wait_start_time = time.time()
        
        ## Queue for commands that need to be send. Used when command is sent when a print is active.
        self._command_queue = queue.Queue()
        
        self._is_printing = False
        
        ## Set when print is started in order to check running time.
        self._print_start_time = None
        self._print_start_time_100 = None
        
        ## Keep track where in the provided g-code the print is
        self._gcode_position = 0
        
        # List of gcode lines to be printed
        self._gcode = None
        
        # Number of extruders
        self._extruder_count = 1
        
        # Temperatures of all extruders
        self._extruder_temperatures = [0] * self._extruder_count
        
        # Target temperatures of all extruders
        self._target_extruder_temperatures = [0] * self._extruder_count
        
        #Target temperature of the bed
        self._target_bed_temperature = 0 
        
        # Temperature of the bed
        self._bed_temperature = 0
        
        # Current Z stage location 
        self._current_z = 0
        
        # In order to keep the connection alive we request the temperature every so often from a different extruder.
        # This index is the extruder we requested data from the last time.
        self._temperature_requested_extruder_index = 0 
        
    #TODO: Might need to add check that extruders can not be changed when it started printing or loading these settings from settings object    
    def setNumExtuders(self, num):
        self._extruder_count = num
        self._extruder_temperatures = [0] * self._extruder_count
        self._target_extruder_temperatures = [0] * self._extruder_count
    
    
    #TODO: Needs more logic
    def isPrinting(self):
        if not self._is_connected or self._serial is None:
            return False
        return self._is_printing

    ##  Provide a list of G-Codes that need to be printed
    def printGCode(self, gcode_list):
        if self.isPrinting() or not self._is_connected:
            return
        self._gcode = gcode_list
        #Reset line number. If this is not done, first line is sometimes ignored
        self._gcode.insert(0, "M110")
        self._gcode_position = 0
        self._print_start_time_100 = None
        self._is_printing = True
        self._print_start_time = time.time()
        for i in range(0, 4): #Push first 4 entries before accepting other inputs
            self._sendNextGcodeLine()
    
    ##  Get the serial port string of this connection.
    #   \return serial port
    def getSerialPort(self):
        return self._serial_port
    
    ##  Try to connect the serial. This simply starts the thread, which runs _connect.
    def connect(self):
        if not self._connect_thread.isAlive():
            self._connect_thread.start()
    
    ##  Private connect function run by thread. Can be started by calling connect.
    def _connect(self): 
        self._is_connecting = True
        programmer = stk500v2.Stk500v2()    
        try:
            programmer.connect(self._serial_port) #Connect with the serial, if this succeeds, it's an arduino based usb device.
            self._serial = programmer.leaveISP() 
            # Create new printer connection
            Logger.log('i', "Established connection on port %s" % self._serial_port)
        except ispBase.IspError as e:
            Logger.log('i', "Could not establish connection on %s: %s. Device is not arduino based." %(self._serial_port,str(e)))
        except:
            Logger.log('i', "Could not establish connection on %s, unknown reasons.  Device is not arduino based." % self._serial_port)
        
        # If the programmer connected, we know its an atmega based version. Not all that usefull, but it does give some debugging information.
        for baud_rate in self._getBaudrateList(): #Cycle all baud rates (auto detect)
            
            if self._serial is None:
                self._serial = serial.Serial(str(self._serial_port), baud_rate, timeout=3, writeTimeout=10000)
            else:   
                if not self.setBaudRate(baud_rate):
                    continue #Could not set the baud rate, go to the next
            time.sleep(1.5) #Ensure that we are not talking to the bootloader. 1.5 sec seems to be the magic number
            sucesfull_responses = 0
            timeout_time = time.time() + 5  
            self._serial.write(b"\n")
            self._sendCommand("M105")  #Request temperature, as this should (if baudrate is correct) result in a command with 'T:' in it
            while timeout_time > time.time():
                line = self._readline() 
                if b"T:" in line:
                    self._serial.timeout = 0.5
                    self._serial.write(b"\n")
                    self._sendCommand("M105")
                    sucesfull_responses += 1
                    if sucesfull_responses >= self._required_responses_auto_baud:
                        self._serial.timeout = 2 #Reset serial timeout
                        self.setIsConnected(True)
                        return 
        self.setIsConnected(False)

    ##  Set the baud rate of the serial. This can cause exceptions, but we simply want to ignore those.
    def setBaudRate(self, baud_rate):
        try:
            self._serial.baudrate = baud_rate
            return True
        except Exception as e:
            return False

    def setIsConnected(self, state):
        self._is_connecting = False
        if self._is_connected != state:
            self._is_connected = state
            self.connectionStateChanged.emit(self._serial_port)
            if self._is_connected: 
                self._listen_thread.start() #Start listening
                '''Application.getInstance().addOutputDevice(self._serial_port, {
                    'id': self._serial_port,
                    'function': self.printGCode,
                    'description': 'Print with USB {0}'.format(self._serial_port),
                    'icon': 'print_usb',
                    'priority': 1
                })'''
                
        else:
            Logger.log('w', "Printer connection state was not changed")
            
    connectionStateChanged = Signal()    
    
    ##  Close the printer connection    
    def close(self):
        if self._serial != None:
            self._serial.close()
            self.setIsConnected(False)
        self._serial = None
    
    def isConnected(self):
        return self._is_connected 
    
    ##  Directly send the command, withouth checking connection state (eg; printing).
    #   \param cmd string with g-code
    def _sendCommand(self, cmd):
        if self._serial is None:
            return
        if 'M109' in cmd or 'M190' in cmd:
            self._heatup_wait_start_time = time.time()
        if 'M104' in cmd or 'M109' in cmd:
            try:
                t = 0
                if 'T' in cmd:
                    t = int(re.search('T([0-9]+)', cmd).group(1))
                self._target_extruder_temperatures[t] = float(re.search('S([0-9]+)', cmd).group(1))
            except:
                pass
        if 'M140' in cmd or 'M190' in cmd:
            try:
                self._target_bed_temperature = float(re.search('S([0-9]+)', cmd).group(1))
            except:
                pass
        #Logger.log('i','Sending: %s' % (cmd))
        try:
            command = (cmd + '\n').encode()
            #self._serial.write(b'\n')
            self._serial.write(command)
        except serial.SerialTimeoutException:
            Logger.log("w","Serial timeout while writing to serial port, trying again.")
            try:
                time.sleep(0.5)
                self._serial.write((cmd + '\n').encode())
            except Exception as e:
                Logger.log("e","Unexpected error while writing serial port %s " % e)
                self.close()
        except Exception as e:
            Logger.log('e',"Unexpected error while writing serial port %s" % e)
            self.close()
    
    ##  Ensure that close gets called when object is destroyed
    def __del__(self):
        self.close()
    
    ##  Send a command to printer. 
    #   \param cmd string with g-code
    def sendCommand(self, cmd):
        if self.isPrinting():
            self._command_queue.put(cmd)
        elif self.isConnected():
            self._sendCommand(cmd)
    
    ##  Listen thread function. 
    def _listen(self):
        temperature_request_timeout = time.time()
        ok_timeout = time.time()
        while self._is_connected:
            line = self._readline()
            if line is None: 
                break #None is only returned when something went wrong. Stop listening
            if line.startswith(b'Error:'):
                #Oh YEAH, consistency.
                # Marlin reports an MIN/MAX temp error as "Error:x\n: Extruder switched off. MAXTEMP triggered !\n"
                #       But a bed temp error is reported as "Error: Temperature heated bed switched off. MAXTEMP triggered !!"
                #       So we can have an extra newline in the most common case. Awesome work people.
                if re.match(b'Error:[0-9]\n', line):
                    line = line.rstrip() + self._readline()
                #Skip the communication errors, as those get corrected.
                if b'Extruder switched off' in line or b'Temperature heated bed switched off' in line or b'Something is wrong, please turn off the printer.' in line:
                    if not self.hasError():
                        self._error_state = line[6:]
            elif b' T:' in line or line.startswith(b'T:'): #Temperature message
                try: 
                    self._extruder_temperatures[self._temperatureRequestExtruder] = float(re.search(b"T: *([0-9\.]*)", line).group(1))
                except:
                    pass
                if b'B:' in line: #Check if it's a bed temperature
                    try:
                        #print("BED TEMPERATURE" ,float(re.search(b"B: *([0-9\.]*)", line).group(1)))
                        pass
                    except:
                        pass
                #TODO: temperature changed callback
                
            if self._is_printing:
                if time.time() > temperature_request_timeout: #When printing, request temperature every 5 seconds.
                    if self._extruder_count > 0:
                        self._temperature_requested_extruder_index = (self._temperature_requested_extruder_index + 1) % self._extruder_count
                        self.sendCommand("M105 T%d" % (self._temperature_requested_extruder_index))
                    else:
                        self.sendCommand("M105")
                    temperature_request_timeout = time.time() + 5
                if line == b'' and time.time() > ok_timeout:
                    line = b'ok' #Force a timeout (basicly, send next command)
                if b'ok' in line:
                    ok_timeout = time.time() + 5
                    if not self._command_queue.empty():
                        self._sendCommand(self._command_queue.get())
                    else:
                        self._sendNextGcodeLine()
                elif b"resend" in line.lower() or b"rs" in line:
                    try:
                        self._gcode_position = int(line.replace(b"N:",b" ").replace(b"N",b" ").replace(b":",b" ").split()[-1])
                    except:
                        if b"rs" in line:
                            self._gcode_position = int(line.split()[1])

            else: #Request the temperature on comm timeout (every 2 seconds) when we are not printing.)
                if line == b'':
                    if self._extruder_count > 0:
                        self._temperature_requested_extruder_index = (self._temperature_requested_extruder_index + 1) % self._extruder_count
                        self.sendCommand("M105 T%d" % self._temperature_requested_extruder_index)
                    else:
                        self.sendCommand("M105")
    ##  Send next Gcode in the gcode list            
    def _sendNextGcodeLine(self):
        if self._gcode_position >= len(self._gcode):
            #self._changeState(self.STATE_OPERATIONAL)
            return
        if self._gcode_position == 100:
            self._print_start_time_100 = time.time()
        line = self._gcode[self._gcode_position]
        if ';' in line:
            line = line[:line.find(';')]
        line = line.strip()
        try:
            if line == 'M0' or line == 'M1':
                #self.setPause(True)
                line = 'M105'   #Don't send the M0 or M1 to the machine, as M0 and M1 are handled as an LCD menu pause.
            if ('G0' in line or 'G1' in line) and 'Z' in line:
                z = float(re.search('Z([0-9\.]*)', line).group(1))
                if self._current_z != z:
                    self._current_z = z
        except Exception as e:
            Logger.log('e', "Unexpected error: %s" % e)
        checksum = functools.reduce(lambda x,y: x^y, map(ord, 'N%d%s' % (self._gcode_position, line)))
        
        self._sendCommand("N%d%s*%d" % (self._gcode_position, line, checksum))
        self._gcode_position += 1 
        self.setProgress(( self._gcode_position / len(self._gcode)) * 100)
        self.progressChanged.emit(self._progress, self._serial_port)
        
    progressChanged = Signal()
    
    def setProgress(self, progress):
        self._progress = progress
        self.progressChanged.emit(self._progress, self._serial_port)
    
    def cancelPrint(self):
        self._gcode_position = 0
        self.setProgress(0)
        self._gcode = []
        # Turn of temperatures
        self._sendCommand("M140 S0")
        self._sendCommand("M109 S0")
        self._is_printing = False
                
    def hasError(self):
        return False    
        
    def _readline(self):
        if self._serial is None:
            return None
        try:
            ret = self._serial.readline()
        except:
            Logger.log('e',"Unexpected error while reading serial port.")    
            #self._errorValue = getExceptionString()
            self.close()
            return None
        #if ret == '':
            #return ''
        #self._log("Recv: %s" % (unicode(ret, 'ascii', 'replace').encode('ascii', 'replace').rstrip()))
        return ret
    
    
    ##  Create a list of baud rates at which we can communicate.
    #   \return list of int
    def _getBaudrateList(self):
        ret = [250000, 230400, 115200, 57600, 38400, 19200, 9600]
        #if profile.getMachineSetting('serial_baud_auto') != '':
            #prev = int(profile.getMachineSetting('serial_baud_auto'))
            #if prev in ret:
                #ret.remove(prev)
                #ret.insert(0, prev)
        return ret
