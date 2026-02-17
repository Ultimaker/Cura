import time
import serial
import serial.tools.list_ports
from UM.Logger import Logger
from PyQt6.QtCore import QObject, pyqtSignal

class GrblController(QObject):
    connection_status_changed = pyqtSignal(bool)
    data_received = pyqtSignal(str)

    MAX_BUFFER_SIZE = 20
    SERIAL_TIMEOUT = 5  # seconds
    MAX_TEMP_OFFSET = 5  # degrees Celsius
    JOG_DISTANCE = 40  # mm
    RECONNECT_INTERVAL = 5 # seconds

    def __init__(self): # No printer_output_device
        super().__init__()
        self._serial_port = None # New: Serial port object
        self.is_connected = False
        self.last_reconnect_attempt = 0
        self._received_data_buffer = []
        self.target_temperatures = {"T0": 20, "T1": 20}
        self.current_temperatures = {"T0": 0.0, "T1": 0.0}
        Logger.log("d", "GrblController initialized.")

    def connect(self):
        Logger.log("d", "Attempting to connect to GRBL device via serial port.")
        if self._serial_port and self._serial_port.is_open:
            Logger.log("d", "Already connected to a serial port.")
            self.is_connected = True
            self.connection_status_changed.emit(self.is_connected)
            return

        ports = serial.tools.list_ports.comports()
        if not ports:
            Logger.log("w", "No serial ports found.")
            self.is_connected = False
            self.connection_status_changed.emit(self.is_connected)
            return

        for p in ports:
            Logger.log("d", f"Found port: {p.device}")
            try:
                self._serial_port = serial.Serial(p.device, 115200, timeout=1) # 115200 baud rate, 1 second timeout
                time.sleep(2) # Wait for GRBL to initialize
                self._serial_port.flushInput() # Clear input buffer
                Logger.log("d", f"Successfully connected to {p.device}")
                self.is_connected = True
                break
            except serial.SerialException as e:
                Logger.log("e", f"Failed to connect to {p.device}: {e}")
                self.is_connected = False
        
        if self.is_connected:
            Logger.log("d", "GrblController connected.")
            # Send GRBL initialization commands and wait for 'ok'
            self.send_gcode("$22=0")  # disable homing
            self.wait_for_ok()
            self.send_gcode("$X")
            self.wait_for_ok()
            self.send_gcode("$21=0")
            self.wait_for_ok()
            self.send_gcode("$3=4")  # invert Z axis
            self.wait_for_ok()
            self.send_gcode("G21")  # mm
            self.wait_for_ok()
            self.send_gcode("G90")  # absolute coords
            self.wait_for_ok()
        else:
            Logger.log("w", "Could not establish a serial connection to any GRBL device.")

        self.connection_status_changed.emit(self.is_connected)

    def send_gcode(self, command):
        if self.is_connected and self._serial_port and self._serial_port.is_open:
            Logger.log("d", f"Sending G-code: {command.strip()}")
            try:
                self._serial_port.write(f"{command.strip()}\r\n".encode('utf-8'))
            except serial.SerialException as e:
                Logger.log("e", f"Failed to send G-code: {e}")
                self.is_connected = False
                self.connection_status_changed.emit(self.is_connected)
        else:
            Logger.log("w", f"Cannot send G-code, GrblController not connected: {command.strip()}")

    def get_connection_status(self):
        return self.is_connected

    def wait_for_ok(self):
        Logger.log("d", "Waiting for 'ok' from printer...")
        t_0 = time.time()
        while time.time() - t_0 < self.SERIAL_TIMEOUT:
            # Read new data from serial port
            try:
                while self._serial_port and self._serial_port.in_waiting:
                    line = self._serial_port.readline().decode('utf-8').strip()
                    if line:
                        Logger.log("d", f"Data received from serial: {line}")
                        self._received_data_buffer.append(line)
                        self.data_received.emit(line)
            except serial.SerialException as e:
                Logger.log("e", f"Error reading from serial port: {e}")
                self.is_connected = False
                self.connection_status_changed.emit(self.is_connected)
                return False

            # Check buffer for 'ok'
            for i, line in enumerate(self._received_data_buffer):
                if "ok" in line:
                    del self._received_data_buffer[:i+1] # Clear processed data
                    Logger.log("d", "Received 'ok'.")
                    return True
            time.sleep(0.01) # Small delay to prevent busy-waiting
        Logger.log("w", "Timeout waiting for 'ok'.")
        return False

    def update(self):
        if not self.is_connected:
            if time.time() - self.last_reconnect_attempt > self.RECONNECT_INTERVAL:
                self.last_reconnect_attempt = time.time()
                self.connect()
            return

        # Read data from serial port
        try:
            while self._serial_port and self._serial_port.in_waiting:
                line = self._serial_port.readline().decode('utf-8').strip()
                if line:
                    Logger.log("d", f"Data received from serial: {line}")
                    self._received_data_buffer.append(line)
                    self.data_received.emit(line)
        except serial.SerialException as e:
            Logger.log("e", f"Error reading from serial port: {e}")
            self.is_connected = False
            self.connection_status_changed.emit(self.is_connected)
            return

        # Process received data for 'ok' and temperature
        # This part remains largely the same, but now it's processing data from the serial port directly.
        # Request temperatures
        self.send_gcode("M105")

        t_0 = time.time()
        while time.time() - t_0 < self.SERIAL_TIMEOUT:
            for i, line in enumerate(self._received_data_buffer):
                if "ok" in line: # Check for 'ok' in the buffer
                    del self._received_data_buffer[:i+1]
                    Logger.log("d", "Received 'ok'.")
                    # If 'ok' is received, we can proceed with other commands or just return
                    # For now, we'll continue to check for M105 response in the same loop
                    pass
                if "$M105=" in line:
                    # Parse tuple response: $M105=T0:200.000,T1:180.000
                    payload = line.split("=")[-1].strip()
                    pairs = payload.split(",")
                    for pair in pairs:
                        tool, val = pair.split(":")
                        self.current_temperatures[tool] = float(val)
                    del self._received_data_buffer[:i+1]
                    Logger.log("d", f"Received temperature data: {payload}")
                    return
            time.sleep(0.01)
        Logger.log("w", "Timeout waiting for M105 response.")

    def set_heating(self, tool: str, temperature: int):
        """Set target temperature for a specific tool (e.g., T0, T1)."""
        self.target_temperatures[tool] = temperature
        # Send full tuple (all tools), so firmware always has consistent state
        cmd_parts = [f"{t}:{temp}" for t, temp in self.target_temperatures.items()]
        cmd = ",".join(cmd_parts)
        self.send_gcode(f"M104 {cmd}")
        self.wait_for_ok()

    def handle(self, event):
        if not self.is_connected:
             return
        try:
            # Placeholder for event classes
            class UpdateTargetTemperature:
                def __init__(self, tool, temperature):
                    self.tool = tool
                    self.temperature = temperature
            class PlayGcode: pass
            class PauseGcode: pass
            class Home: pass
            class NewGcodeFile:
                def __init__(self, filename):
                    self.filename = filename
            class Jog:
                def __init__(self, movement):
                    self.movement = movement

            if isinstance(event, UpdateTargetTemperature):
                self.set_heating(event.tool, event.temperature)
            elif isinstance(event, PlayGcode):
                # self.gcode_handler.play() # GcodeHandler not yet implemented
                Logger.log("w", "PlayGcode event received, but GcodeHandler is not implemented.")
            elif isinstance(event, PauseGcode):
                # self.gcode_handler.pause() # GcodeHandler not yet implemented
                Logger.log("w", "PauseGcode event received, but GcodeHandler is not implemented.")
            elif isinstance(event, Home):
                self.send_gcode("$H")
                self.wait_for_ok()
            elif isinstance(event, NewGcodeFile):
                # self.set_gcode_file(event.filename) # set_gcode_file not yet fully implemented
                Logger.log("w", f"NewGcodeFile event received for {event.filename}, but set_gcode_file is not fully implemented.")
            elif isinstance(event, Jog):
                self.send_gcode("G91")  # relative coords
                self.wait_for_ok()
                movement = event.movement
                command = (
                    f"G1 X{movement[0]*self.JOG_DISTANCE} "
                    f"Y{movement[1]*self.JOG_DISTANCE} "
                    f"Z{movement[2]*self.JOG_DISTANCE} "
                    f"E{movement[3]*self.JOG_DISTANCE + 7} "
                    f"B{movement[3]*self.JOG_DISTANCE + 7} "
                    "F200"
                )
                self.send_gcode(command)
                self.wait_for_ok()
                self.send_gcode("G90")  # absolute coords
                self.wait_for_ok()
            else:
                Logger.log("w", "Event not caught: " + str(event))
        except Exception as e: # Catch all exceptions for now
            Logger.log("e", f"Error handling event: {e}")
            self.is_connected = False
            # self.register_event(events.ArduinoDisconnected()) # events not implemented
            self.connection_status_changed.emit(self.is_connected)

    def get_aprox_buffer(self):
        Logger.log("w", "get_aprox_buffer method is a placeholder and not fully implemented for Cura's active printer.")
        # In a real implementation, this would send a command and parse the response
        # For now, return a default value
        return 10 # A reasonable default buffer size

    def set_gcode_file(self, filename: str):
        Logger.log("w", f"set_gcode_file method is a placeholder and not fully implemented for Cura's active printer. Filename: {filename}")
        # This would typically involve loading a G-code file and preparing it for printing
        pass