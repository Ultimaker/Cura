# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from .avr_isp import stk500v2, ispBase, intelHex
import serial
import threading
import time
import queue
import re
import functools
import os.path

from UM.Application import Application
from UM.Signal import Signal, SignalEmitter
from UM.Logger import Logger
from UM.OutputDevice.OutputDevice import OutputDevice
from UM.PluginRegistry import PluginRegistry

from PyQt5.QtQuick import QQuickView
from PyQt5.QtQml import QQmlComponent, QQmlContext
from PyQt5.QtCore import QUrl, QObject, pyqtSlot, pyqtProperty, pyqtSignal, Qt

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

class PrinterConnection(OutputDevice, QObject, SignalEmitter):
    def __init__(self, serial_port, parent = None):
        QObject.__init__(self, parent)
        OutputDevice.__init__(self, serial_port)
        SignalEmitter.__init__(self)
        #super().__init__(serial_port)
        self.setName(catalog.i18nc("@item:inmenu", "USB printing"))
        self.setShortDescription(catalog.i18nc("@action:button", "Print with USB"))
        self.setDescription(catalog.i18nc("@info:tooltip", "Print with USB"))
        self.setIconName("print")

        self._serial = None
        self._serial_port = serial_port
        self._error_state = None

        self._connect_thread = threading.Thread(target = self._connect)
        self._connect_thread.daemon = True

        self._end_stop_thread = threading.Thread(target = self._pollEndStop)
        self._end_stop_thread.daemon = True
        self._poll_endstop = -1

        # Printer is connected
        self._is_connected = False

        # Printer is in the process of connecting
        self._is_connecting = False

        # The baud checking is done by sending a number of m105 commands to the printer and waiting for a readable
        # response. If the baudrate is correct, this should make sense, else we get giberish.
        self._required_responses_auto_baud = 3

        self._progress = 0

        self._listen_thread = threading.Thread(target=self._listen)
        self._listen_thread.daemon = True

        self._update_firmware_thread = threading.Thread(target= self._updateFirmware)
        self._update_firmware_thread.daemon = True
        self.firmwareUpdateComplete.connect(self._onFirmwareUpdateComplete)
        
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
        self._gcode = []

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

        self._x_min_endstop_pressed = False
        self._y_min_endstop_pressed = False
        self._z_min_endstop_pressed = False

        self._x_max_endstop_pressed = False
        self._y_max_endstop_pressed = False
        self._z_max_endstop_pressed = False

        # In order to keep the connection alive we request the temperature every so often from a different extruder.
        # This index is the extruder we requested data from the last time.
        self._temperature_requested_extruder_index = 0 

        self._updating_firmware = False

        self._firmware_file_name = None

        self._control_view = None

    onError = pyqtSignal()
    progressChanged = pyqtSignal()
    extruderTemperatureChanged = pyqtSignal()
    bedTemperatureChanged = pyqtSignal()
    firmwareUpdateComplete = pyqtSignal()

    endstopStateChanged = pyqtSignal(str ,bool, arguments = ["key","state"])

    @pyqtProperty(float, notify = progressChanged)
    def progress(self):
        return self._progress

    @pyqtProperty(float, notify = extruderTemperatureChanged)
    def extruderTemperature(self):
        return self._extruder_temperatures[0]

    @pyqtProperty(float, notify = bedTemperatureChanged)
    def bedTemperature(self):
        return self._bed_temperature

    @pyqtProperty(str, notify = onError)
    def error(self):
        return self._error_state

    # TODO: Might need to add check that extruders can not be changed when it started printing or loading these settings from settings object    
    def setNumExtuders(self, num):
        self._extruder_count = num
        self._extruder_temperatures = [0] * self._extruder_count
        self._target_extruder_temperatures = [0] * self._extruder_count

    ##  Is the printer actively printing
    def isPrinting(self):
        if not self._is_connected or self._serial is None:
            return False
        return self._is_printing

    @pyqtSlot()
    def startPrint(self):
        self.writeStarted.emit(self)
        gcode_list = getattr( Application.getInstance().getController().getScene(), "gcode_list")
        self.printGCode(gcode_list)

    ##  Start a print based on a g-code.
    #   \param gcode_list List with gcode (strings).
    def printGCode(self, gcode_list):
        if self.isPrinting() or not self._is_connected:
            Logger.log("d", "Printer is busy or not connected, aborting print")
            self.writeError.emit(self)
            return

        self._gcode.clear()
        for layer in gcode_list:
            self._gcode.extend(layer.split("\n"))

        #Reset line number. If this is not done, first line is sometimes ignored
        self._gcode.insert(0, "M110")
        self._gcode_position = 0
        self._print_start_time_100 = None
        self._is_printing = True
        self._print_start_time = time.time()

        for i in range(0, 4): #Push first 4 entries before accepting other inputs
            self._sendNextGcodeLine()

        self.writeFinished.emit(self)

    ##  Get the serial port string of this connection.
    #   \return serial port
    def getSerialPort(self):
        return self._serial_port

    ##  Try to connect the serial. This simply starts the thread, which runs _connect.
    def connect(self):
        if not self._updating_firmware and not self._connect_thread.isAlive():
            self._connect_thread.start()

    ##  Private fuction (threaded) that actually uploads the firmware.
    def _updateFirmware(self):
        self.setProgress(0, 100)

        if self._is_connecting or  self._is_connected:
            self.close()
        hex_file = intelHex.readHex(self._firmware_file_name)

        if len(hex_file) == 0:
            Logger.log("e", "Unable to read provided hex file. Could not update firmware")
            return 

        programmer = stk500v2.Stk500v2()
        programmer.progressCallback = self.setProgress 

        try:
            programmer.connect(self._serial_port)
        except Exception:
            pass

        time.sleep(1) # Give programmer some time to connect. Might need more in some cases, but this worked in all tested cases.

        if not programmer.isConnected():
            Logger.log("e", "Unable to connect with serial. Could not update firmware")
            return 

        self._updating_firmware = True

        try:
            programmer.programChip(hex_file)
            self._updating_firmware = False
        except Exception as e:
            Logger.log("e", "Exception while trying to update firmware %s" %e)
            self._updating_firmware = False
            return
        programmer.close()

        self.setProgress(100, 100)

        self.firmwareUpdateComplete.emit()

    ##  Upload new firmware to machine
    #   \param filename full path of firmware file to be uploaded
    def updateFirmware(self, file_name):
        Logger.log("i", "Updating firmware of %s using %s", self._serial_port, file_name)
        self._firmware_file_name = file_name
        self._update_firmware_thread.start()

    @pyqtSlot()
    def startPollEndstop(self):
        if self._poll_endstop == -1:
            self._poll_endstop = True
            self._end_stop_thread.start()

    @pyqtSlot()
    def stopPollEndstop(self):
        self._poll_endstop = False

    def _pollEndStop(self):
        while self._is_connected and self._poll_endstop:
            self.sendCommand("M119")
            time.sleep(0.5)

    ##  Private connect function run by thread. Can be started by calling connect.
    def _connect(self):
        Logger.log("d", "Attempting to connect to %s", self._serial_port)
        self._is_connecting = True
        programmer = stk500v2.Stk500v2()
        try:
            programmer.connect(self._serial_port) # Connect with the serial, if this succeeds, it"s an arduino based usb device.
            self._serial = programmer.leaveISP()
        except ispBase.IspError as e:
            Logger.log("i", "Could not establish connection on %s: %s. Device is not arduino based." %(self._serial_port,str(e)))
        except Exception as e:
            Logger.log("i", "Could not establish connection on %s, unknown reasons.  Device is not arduino based." % self._serial_port)

        # If the programmer connected, we know its an atmega based version. Not all that usefull, but it does give some debugging information.
        for baud_rate in self._getBaudrateList(): # Cycle all baud rates (auto detect)
            Logger.log("d","Attempting to connect to printer with serial %s on baud rate %s", self._serial_port, baud_rate)
            if self._serial is None:
                try:
                    self._serial = serial.Serial(str(self._serial_port), baud_rate, timeout = 3, writeTimeout = 10000)
                except serial.SerialException:
                    #Logger.log("i", "Could not open port %s" % self._serial_port)
                    continue
            else:
                if not self.setBaudRate(baud_rate):
                    continue # Could not set the baud rate, go to the next

            time.sleep(1.5) # Ensure that we are not talking to the bootloader. 1.5 sec seems to be the magic number
            sucesfull_responses = 0
            timeout_time = time.time() + 5
            self._serial.write(b"\n")
            self._sendCommand("M105")  # Request temperature, as this should (if baudrate is correct) result in a command with "T:" in it
            while timeout_time > time.time():
                line = self._readline()
                if line is None:
                    self.setIsConnected(False) # Something went wrong with reading, could be that close was called.
                    return
                
                if b"T:" in line:
                    self._serial.timeout = 0.5
                    sucesfull_responses += 1
                    if sucesfull_responses >= self._required_responses_auto_baud:
                        self._serial.timeout = 2 #Reset serial timeout
                        self.setIsConnected(True)
                        Logger.log("i", "Established printer connection on port %s" % self._serial_port)
                        return 

                self._sendCommand("M105") # Send M105 as long as we are listening, otherwise we end up in an undefined state

        Logger.log("e", "Baud rate detection for %s failed", self._serial_port)
        self.close() # Unable to connect, wrap up.
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
        else:
            Logger.log("w", "Printer connection state was not changed")

    connectionStateChanged = Signal()

    ##  Close the printer connection
    def close(self):
        Logger.log("d", "Closing the printer connection.")
        if self._connect_thread.isAlive():
            try:
                self._connect_thread.join()
            except Exception as e:
                Logger.log("d", "PrinterConnection.close: %s (expected)", e)
                pass # This should work, but it does fail sometimes for some reason

        self._connect_thread = threading.Thread(target=self._connect)
        self._connect_thread.daemon = True
        
        self.setIsConnected(False)
        if self._serial is not None:
            try:
                self._listen_thread.join()
            except:
                pass
            self._serial.close()

        self._listen_thread = threading.Thread(target=self._listen)
        self._listen_thread.daemon = True
        self._serial = None

    def isConnected(self):
        return self._is_connected

    @pyqtSlot(int)
    def heatupNozzle(self, temperature):
        Logger.log("d", "Setting nozzle temperature to %s", temperature)
        self._sendCommand("M104 S%s" % temperature)

    @pyqtSlot(int)
    def heatupBed(self, temperature):
        Logger.log("d", "Setting bed temperature to %s", temperature)
        self._sendCommand("M140 S%s" % temperature)

    @pyqtSlot()
    def setMoveToRelative(self):
        self._sendCommand("G91")

    @pyqtSlot()
    def setMoveToAbsolute(self):
        self._sendCommand("G90")

    @pyqtSlot("long", "long","long")
    def moveHead(self, x, y, z):
        Logger.log("d","Moving head to %s, %s , %s", x, y, z)
        self._sendCommand("G0 X%s Y%s Z%s F3000" % (x, y, z))

    @pyqtSlot("long", "long","long")
    def moveHeadRelative(self, x, y, z):
        self.setMoveToRelative()
        self.moveHead(x,y,z)
        self.setMoveToAbsolute()

    @pyqtSlot()
    def homeHead(self):
        self._sendCommand("G28")

    @pyqtSlot()
    def homeBed(self):
        self._sendCommand("G28 Z")

    ##  Directly send the command, withouth checking connection state (eg; printing).
    #   \param cmd string with g-code
    def _sendCommand(self, cmd):
        if self._serial is None:
            return

        if "M109" in cmd or "M190" in cmd:
            self._heatup_wait_start_time = time.time()
        if "M104" in cmd or "M109" in cmd:
            try:
                t = 0
                if "T" in cmd:
                    t = int(re.search("T([0-9]+)", cmd).group(1))
                self._target_extruder_temperatures[t] = float(re.search("S([0-9]+)", cmd).group(1))
            except:
                pass
        if "M140" in cmd or "M190" in cmd:
            try:
                self._target_bed_temperature = float(re.search("S([0-9]+)", cmd).group(1))
            except:
                pass
        try:
            command = (cmd + "\n").encode()
            self._serial.write(b"\n")
            self._serial.write(command)
        except serial.SerialTimeoutException:
            Logger.log("w","Serial timeout while writing to serial port, trying again.")
            try:
                time.sleep(0.5)
                self._serial.write((cmd + "\n").encode())
            except Exception as e:
                Logger.log("e","Unexpected error while writing serial port %s " % e)
                self._setErrorState("Unexpected error while writing serial port %s " % e)
                self.close()
        except Exception as e:
            Logger.log("e","Unexpected error while writing serial port %s" % e)
            self._setErrorState("Unexpected error while writing serial port %s " % e)
            self.close()

    ##  Ensure that close gets called when object is destroyed
    def __del__(self):
        self.close()

    def createControlInterface(self):
        if self._control_view is None:
            Logger.log("d", "Creating control interface for printer connection")
            path = QUrl.fromLocalFile(os.path.join(PluginRegistry.getInstance().getPluginPath("USBPrinting"), "ControlWindow.qml"))
            component = QQmlComponent(Application.getInstance()._engine, path)
            self._control_context = QQmlContext(Application.getInstance()._engine.rootContext())
            self._control_context.setContextProperty("manager", self)
            self._control_view = component.create(self._control_context)

    ##  Show control interface.
    #   This will create the view if its not already created.
    def showControlInterface(self):
        if self._control_view is None:
            self.createControlInterface()
        self._control_view.show()

    ##  Send a command to printer. 
    #   \param cmd string with g-code
    def sendCommand(self, cmd):
        if self.isPrinting():
            self._command_queue.put(cmd)
        elif self.isConnected():
            self._sendCommand(cmd)

    ##  Set the error state with a message.
    #   \param error String with the error message.
    def _setErrorState(self, error):
        self._error_state = error
        self.onError.emit()

    ##  Private function to set the temperature of an extruder
    #   \param index index of the extruder
    #   \param temperature recieved temperature
    def _setExtruderTemperature(self, index, temperature):
        try: 
            self._extruder_temperatures[index] = temperature
            self.extruderTemperatureChanged.emit()
        except Exception as e:
            Logger.log("d", "PrinterConnection._setExtruderTemperature: ", e)
            pass

    ##  Private function to set the temperature of the bed.
    #   As all printers (as of time of writing) only support a single heated bed,
    #   these are not indexed as with extruders.
    def _setBedTemperature(self, temperature):
        self._bed_temperature = temperature
        self.bedTemperatureChanged.emit()

    def requestWrite(self, node, file_name = None, filter_by_machine = False):
        self.showControlInterface()

    def _setEndstopState(self, endstop_key, value):
        if endstop_key == b"x_min":
            if self._x_min_endstop_pressed != value:
                self.endstopStateChanged.emit("x_min", value)
            self._x_min_endstop_pressed = value
        elif endstop_key == b"y_min":
            if self._y_min_endstop_pressed != value:
                self.endstopStateChanged.emit("y_min", value)
            self._y_min_endstop_pressed = value
        elif endstop_key == b"z_min":
            if self._z_min_endstop_pressed != value:
                self.endstopStateChanged.emit("z_min", value)
            self._z_min_endstop_pressed = value

    ##  Listen thread function. 
    def _listen(self):
        Logger.log("i", "Printer connection listen thread started for %s" % self._serial_port)
        temperature_request_timeout = time.time()
        ok_timeout = time.time()
        while self._is_connected:
            line = self._readline()

            if line is None: 
                break # None is only returned when something went wrong. Stop listening

            if time.time() > temperature_request_timeout:
                if self._extruder_count > 0:
                    self._temperature_requested_extruder_index = (self._temperature_requested_extruder_index + 1) % self._extruder_count
                    self.sendCommand("M105 T%d" % (self._temperature_requested_extruder_index))
                else:
                    self.sendCommand("M105")
                temperature_request_timeout = time.time() + 5

            if line.startswith(b"Error:"):
                # Oh YEAH, consistency.
                # Marlin reports an MIN/MAX temp error as "Error:x\n: Extruder switched off. MAXTEMP triggered !\n"
                #       But a bed temp error is reported as "Error: Temperature heated bed switched off. MAXTEMP triggered !!"
                #       So we can have an extra newline in the most common case. Awesome work people.
                if re.match(b"Error:[0-9]\n", line):
                    line = line.rstrip() + self._readline()

                # Skip the communication errors, as those get corrected.
                if b"Extruder switched off" in line or b"Temperature heated bed switched off" in line or b"Something is wrong, please turn off the printer." in line:
                    if not self.hasError():
                        self._setErrorState(line[6:])

            elif b" T:" in line or line.startswith(b"T:"): #Temperature message
                try: 
                    self._setExtruderTemperature(self._temperature_requested_extruder_index,float(re.search(b"T: *([0-9\.]*)", line).group(1)))
                except:
                    pass
                if b"B:" in line: # Check if it"s a bed temperature
                    try:
                        self._setBedTemperature(float(re.search(b"B: *([0-9\.]*)", line).group(1)))
                    except Exception as e:
                        pass
                #TODO: temperature changed callback
            elif b"_min" in line or b"_max" in line:
                tag, value = line.split(b":", 1)
                self._setEndstopState(tag,(b"H" in value or b"TRIGGERED" in value))

            if self._is_printing:
                if line == b"" and time.time() > ok_timeout:
                    line = b"ok" # Force a timeout (basicly, send next command)

                if b"ok" in line:
                    ok_timeout = time.time() + 5
                    if not self._command_queue.empty():
                        self._sendCommand(self._command_queue.get())
                    else:
                        self._sendNextGcodeLine()
                elif b"resend" in line.lower() or b"rs" in line: # Because a resend can be asked with "resend" and "rs"
                    try:
                        self._gcode_position = int(line.replace(b"N:",b" ").replace(b"N",b" ").replace(b":",b" ").split()[-1])
                    except:
                        if b"rs" in line:
                            self._gcode_position = int(line.split()[1])

            else: # Request the temperature on comm timeout (every 2 seconds) when we are not printing.)
                if line == b"":
                    if self._extruder_count > 0:
                        self._temperature_requested_extruder_index = (self._temperature_requested_extruder_index + 1) % self._extruder_count
                        self.sendCommand("M105 T%d" % self._temperature_requested_extruder_index)
                    else:
                        self.sendCommand("M105")
        Logger.log("i", "Printer connection listen thread stopped for %s" % self._serial_port)

    ##  Send next Gcode in the gcode list
    def _sendNextGcodeLine(self):
        if self._gcode_position >= len(self._gcode):
            return
        if self._gcode_position == 100:
            self._print_start_time_100 = time.time()
        line = self._gcode[self._gcode_position]

        if ";" in line:
            line = line[:line.find(";")]
        line = line.strip()
        try:
            if line == "M0" or line == "M1":
                line = "M105"   #Don"t send the M0 or M1 to the machine, as M0 and M1 are handled as an LCD menu pause.
            if ("G0" in line or "G1" in line) and "Z" in line:
                z = float(re.search("Z([0-9\.]*)", line).group(1))
                if self._current_z != z:
                    self._current_z = z
        except Exception as e:
            Logger.log("e", "Unexpected error with printer connection: %s" % e)
            self._setErrorState("Unexpected error: %s" %e)
        checksum = functools.reduce(lambda x,y: x^y, map(ord, "N%d%s" % (self._gcode_position, line)))

        self._sendCommand("N%d%s*%d" % (self._gcode_position, line, checksum))
        self._gcode_position += 1 
        self.setProgress(( self._gcode_position / len(self._gcode)) * 100)
        self.progressChanged.emit()

    ##  Set the progress of the print. 
    #   It will be normalized (based on max_progress) to range 0 - 100
    def setProgress(self, progress, max_progress = 100):
        self._progress  = (progress / max_progress) * 100 #Convert to scale of 0-100
        self.progressChanged.emit()

    ##  Cancel the current print. Printer connection wil continue to listen.
    @pyqtSlot()
    def cancelPrint(self):
        self._gcode_position = 0
        self.setProgress(0)
        self._gcode = []

        # Turn of temperatures
        self._sendCommand("M140 S0")
        self._sendCommand("M104 S0")
        self._is_printing = False

    ##  Check if the process did not encounter an error yet.
    def hasError(self):
        return self._error_state != None

    ##  private read line used by printer connection to listen for data on serial port.
    def _readline(self):
        if self._serial is None:
            return None
        try:
            ret = self._serial.readline()
        except Exception as e:
            Logger.log("e","Unexpected error while reading serial port. %s" %e)
            self._setErrorState("Printer has been disconnected") 
            self.close()
            return None
        return ret

    ##  Create a list of baud rates at which we can communicate.
    #   \return list of int
    def _getBaudrateList(self):
        ret = [115200, 250000, 230400, 57600, 38400, 19200, 9600]
        return ret

    def _onFirmwareUpdateComplete(self):
        self._update_firmware_thread.join()
        self._update_firmware_thread = threading.Thread(target= self._updateFirmware)
        self._update_firmware_thread.daemon = True

        self.connect()
