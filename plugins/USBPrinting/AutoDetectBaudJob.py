# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Job import Job
from UM.Logger import Logger

from .avr_isp.stk500v2 import Stk500v2

from time import time, sleep
from serial import Serial, SerialException


#   An async job that attempts to find the correct baud rate for a USB printer.
#   It tries a pre-set list of baud rates. All these baud rates are validated by requesting the temperature a few times
#   and checking if the results make sense. If getResult() is not None, it was able to find a correct baud rate.
class AutoDetectBaudJob(Job):
    def __init__(self, serial_port):
        super().__init__()
        self._serial_port = serial_port
        self._all_baud_rates = [115200, 250000, 230400, 57600, 38400, 19200, 9600]

    def run(self):
        Logger.log("d", "Auto detect baud rate started.")
        timeout = 3

        programmer = Stk500v2()
        serial = None
        try:
            programmer.connect(self._serial_port)
            serial = programmer.leaveISP()
        except:
            programmer.close()

        for baud_rate in self._all_baud_rates:
            Logger.log("d", "Checking {serial} if baud rate {baud_rate} works".format(serial= self._serial_port, baud_rate = baud_rate))

            if serial is None:
                try:
                    serial = Serial(str(self._serial_port), baud_rate, timeout = timeout, writeTimeout = timeout)
                except SerialException as e:
                    Logger.logException("w", "Unable to create serial")
                    continue
            else:
                # We already have a serial connection, just change the baud rate.
                try:
                    serial.baudrate = baud_rate
                except:
                    continue
            sleep(1.5)  # Ensure that we are not talking to the boot loader. 1.5 seconds seems to be the magic number
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
