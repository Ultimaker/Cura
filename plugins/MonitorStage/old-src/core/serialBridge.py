import serial
from serial.serialutil import SerialException

SERIAL_PORT = "COM5"

class SerialBridge:
    def __init__(self):
        self.ser = None
        
    def connect(self):
        self.ser = serial.Serial(
            SERIAL_PORT,
            baudrate=115200,
            timeout=1
        )
        self._buffer = ""
    
    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    def read(self):
        if not self.ser:
            raise SerialException("Not connected")
        return self.ser.read()
        
    def write(self, data):
        if not self.ser:
            raise SerialException("Not connected")
        print(f"> {data.strip()}")
        return self.ser.write(data.encode("utf-8"))

    def readline(self) -> str:
        char = True
        while char:
            char = self.read()
            if char:
                # print(char)
                try:
                    char = char.decode("utf-8")
                except UnicodeDecodeError:
                    continue # Ignore non-utf8 characters
                self._buffer += char
                
                if char == '\n':
                    cpy = self._buffer
                    print(f"< {cpy.strip()}")
                    self._buffer = "" # clear buffer
                    return cpy
        return ""

    def flush(self):
        if self.ser:
            self.ser.flush()

