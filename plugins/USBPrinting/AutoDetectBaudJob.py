# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Job import Job
from UM.Logger import Logger

from time import time
from serial import Serial, SerialException

class AutoDetectBaudJob(Job):
    def __init__(self, serial_port):
        super().__init__()
        self._serial_port = serial_port
        self._all_baud_rates = [115200, 250000, 230400, 57600, 38400, 19200, 9600]

    def run(self):
        Logger.log("d", "Auto detect baud rate started.")
        timeout = 3

        for baud_rate in self._all_baud_rates:
            Logger.log("d", "Checking {serial} if baud rate {baud_rate} works".format(serial= self._serial_port, baud_rate = baud_rate))
            try:
                serial = Serial(str(self._serial_port), baud_rate, timeout = timeout, writeTimeout = timeout)
            except SerialException as e:
                Logger.logException("w", "Unable to create serial")
                continue

            successful_responses = 0

            serial.write(b"\n")  # Ensure we clear out previous responses
            serial.write(b"M105\n")

            timeout_time = time() + timeout

            while timeout_time > time():
                line = serial.readline()
                if b"ok T:" in line:
                    successful_responses += 1
                    if successful_responses >= 3:
                        self.setResult(baud_rate)
                        return

                serial.write(b"M105\n")
        self.setResult(None)  # Unable to detect the correct baudrate.