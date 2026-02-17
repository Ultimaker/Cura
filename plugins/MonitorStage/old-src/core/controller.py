import time
from .serialBridge import SerialBridge
from .filehandler import GcodeHandler
import events
from logger import NozzleTemperatureWarning
from serial.serialutil import SerialException

class Controller:
    MAX_BUFFER_SIZE = 20
    SERIAL_TIMEOUT = 5  # seconds
    MAX_TEMP_OFFSET = 5  # degrees Celsius
    JOG_DISTANCE = 40  # mm
    RECONNECT_INTERVAL = 5 # seconds

    def __init__(self, logger):
        self.logger = logger
        self.registered_events = []

        self.set_gcode_file("3d files/hart/hart.gcode")
        self.serialBridge = SerialBridge()
        self.is_connected = False
        self.last_reconnect_attempt = 0

        # Track per-tool target & current temperatures
        self.target_temperatures = {"T0": 20, "T1": 20}
        self.current_temperatures = {"T0": 0.0, "T1": 0.0}

    def connect(self):
        try:
            self.serialBridge.connect()
            t_0 = time.time()
            while "Grbl" not in self.serialBridge.readline():
                if time.time() - t_0 > Controller.SERIAL_TIMEOUT:
                    raise RuntimeError("Timeout")

            self.serialBridge.write("$22=0\r\n")  # disable homing

            self.wait_for_ok()

            self.serialBridge.write("$X\r\n")
            self.wait_for_ok()

            self.serialBridge.write("$21=0\r\n")
            self.wait_for_ok()

            self.serialBridge.write("$3=4\r\n")  # invert Z axis
            self.wait_for_ok()

            self.serialBridge.write("G21\r\n")  # mm
            self.wait_for_ok()
            self.serialBridge.write("G90\r\n")  # absolute coords
            self.wait_for_ok()


            self.wait_for_ok()
            self.is_connected = True
            self.serialBridge.is_connected = True
            self.register_event(events.ArduinoConnected())
        except (RuntimeError, SerialException):
            self.is_connected = False
            self.serialBridge.is_connected = False
            self.register_event(events.ArduinoDisconnected())

    def set_heating(self, tool: str, temperature: int):
        """Set target temperature for a specific tool (e.g., T0, T1)."""
        self.target_temperatures[tool] = temperature
        # Send full tuple (all tools), so firmware always has consistent state
        cmd_parts = [f"{t}:{temp}" for t, temp in self.target_temperatures.items()]
        cmd = ",".join(cmd_parts)
        self.serialBridge.write(f"M104 {cmd}\r\n")
        self.wait_for_ok()

    def update(self):
        if not self.is_connected:
            if time.time() - self.last_reconnect_attempt > self.RECONNECT_INTERVAL:
                self.last_reconnect_attempt = time.time()
                self.connect()
            return [] # No updates if not connected

        try:
            self.serialBridge.flush()

            # Update buffer size bookkeeping
            if self.gcode_handler.aprox_buffer >= Controller.MAX_BUFFER_SIZE:
                cpy = self.gcode_handler.aprox_buffer
                self.gcode_handler.aprox_buffer = self.get_aprox_buffer()
                self.gcode_handler.execution_line += max(0, cpy - self.gcode_handler.aprox_buffer)
                self.register_event(events.SetGcodeLine(self.gcode_handler.execution_line))

            # Feed commands
            if self.gcode_handler and self.gcode_handler.playing:
                if self.gcode_handler.com_line < self.gcode_handler.get_size():
                    t_0 = time.time()
                    while self.gcode_handler.aprox_buffer < Controller.MAX_BUFFER_SIZE:
                        if time.time() - t_0 > Controller.SERIAL_TIMEOUT:
                            raise RuntimeError("Timeout")
                        if self.gcode_handler.com_line >= self.gcode_handler.get_size():
                            break
                        else:
                            command = self.gcode_handler.get_line(self.gcode_handler.com_line)
                            if (
                                len(command) == 0
                                or command[0] == ";"
                                or command[0] == "M"
                                or command[0:3] == "G92"
                            ):
                                self.gcode_handler.execution_line += 1
                            else:
                                self.serialBridge.write(command + "\r\n")
                                self.wait_for_ok()
                                self.gcode_handler.aprox_buffer += 1
                            self.gcode_handler.com_line += 1

            # Request temperatures
            self.serialBridge.write("M105\r\n")
            t_0 = time.time()
            while True:
                if time.time() - t_0 > Controller.SERIAL_TIMEOUT:
                    raise RuntimeError("Timeout")
                line = self.serialBridge.readline()
                if "ok\r\n" == line:
                    continue
                elif "$M105=" in line:
                    # Parse tuple response: $M105=T0:200.000,T1:180.000
                    payload = line.split("=")[-1].strip()
                    pairs = payload.split(",")
                    for pair in pairs:
                        tool, val = pair.split(":")
                        self.current_temperatures[tool] = float(val)
                    break

            # Safety check for each tool
            for tool, target in self.target_temperatures.items():
                current = self.current_temperatures.get(tool, 0.0)
                if abs(target - current) > Controller.MAX_TEMP_OFFSET:
                    self.logger.show_message(NozzleTemperatureWarning(tool))
                self.register_event(events.UpdateNozzleTemperature(tool, current))

            self.serialBridge.flush()

        except (SerialException, RuntimeError) as e:
            print(f"Error: {e}")
            self.is_connected = False
            self.serialBridge.is_connected = False
            self.register_event(events.ArduinoDisconnected())

        cpy = self.registered_events
        self.registered_events = []
        return cpy

    def register_event(self, event: events.Event):
        self.registered_events.append(event)

    def handle(self, event: events.Event):
        if not self.is_connected:
             return
        try:
            match event:
                case events.UpdateTargetTemperature(tool=tool, temperature=temp):
                    self.set_heating(tool, temp)
                case events.PlayGcode:
                    self.gcode_handler.play()
                case events.PauseGcode:
                    self.gcode_handler.pause()
                case events.Home:
                    self.serialBridge.write("$H\r\n")
                    self.wait_for_ok()
                case events.NewGcodeFile(filename):
                    self.set_gcode_file(filename)
                case events.Jog(movement):
                    self.serialBridge.write("G91\r\n")  # relative coords
                    self.wait_for_ok()
                    command = (
                        f"G1 X{movement[0]*Controller.JOG_DISTANCE} "
                        f"Y{movement[1]*Controller.JOG_DISTANCE} "
                        f"Z{movement[2]*Controller.JOG_DISTANCE} "
                        f"E{movement[3]*Controller.JOG_DISTANCE + 7} "
                        f"B{movement[3]*Controller.JOG_DISTANCE + 7} "
                        "F200\r\n"
                    )
                    self.serialBridge.write(command)
                    self.wait_for_ok()
                    self.serialBridge.write("G90\r\n")  # absolute coords
                    self.wait_for_ok()
                case _:
                    raise NotImplementedError("Event not caught: " + str(event))
        except (SerialException, RuntimeError):
            self.is_connected = False
            self.serialBridge.is_connected = False
            self.register_event(events.ArduinoDisconnected())

    def wait_for_ok(self):
        t_0 = time.time()
        while "ok\r\n" not in self.serialBridge.readline():
            if time.time() - t_0 > Controller.SERIAL_TIMEOUT:
                raise RuntimeError("Timeout")

    def get_aprox_buffer(self):
        self.serialBridge.flush()
        self.serialBridge.write("G200\r\n")  # custom command
        t_0 = time.time()
        while True:
            if time.time() - t_0 > Controller.SERIAL_TIMEOUT:
                raise RuntimeError("Timeout")
            line = self.serialBridge.readline()
            if "ok\r\n" == line:
                continue
            elif "$G200=" in line:
                return int(line.split("=")[-1][:-2])

    def set_gcode_file(self, filename: str):
        self.gcode_handler = GcodeHandler(filename)
        self.register_event(events.NewGcodeFileHandler(self.gcode_handler))
