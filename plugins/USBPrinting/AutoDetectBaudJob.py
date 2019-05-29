# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Job import Job
from UM.Logger import Logger

from .avr_isp import ispBase
from .avr_isp.stk500v2 import Stk500v2

from time import time, sleep
from serial import Serial, SerialException


#   An async job that attempts to find the correct baud rate for a USB printer.
#   It tries a pre-set list of baud rates. All these baud rates are validated by requesting the temperature a few times
#   and checking if the results make sense. If getResult() is not None, it was able to find a correct baud rate.
class AutoDetectBaudJob(Job):
    def __init__(self, serial_port: int) -> None:
        super().__init__()
        self._serial_port = serial_port
        self._all_baud_rates = [115200, 250000, 500000, 230400, 57600, 38400, 19200, 9600]

    def run(self) -> None:
        Logger.log("d", "Auto detect baud rate started.")
        read_timeouts = [2, 5, 15, 30]
        wait_bootloader_times = [5, 10, 15]
        write_timeout = 3
        read_timeout = 3
        tries = 2

        programmer = Stk500v2()
        serial = None
        try:
            programmer.connect(self._serial_port)
            serial = programmer.leaveISP()
        except ispBase.IspError:
            programmer.close()

        for retry in range(tries):
            for baud_rate in self._all_baud_rates:
                if retry < len(read_timeouts):
                    read_timeout = read_timeouts[retry]
                else:
                    read_timeout = read_timeouts[-1]
                if retry < len(wait_bootloader_times):
                    wait_bootloader = wait_bootloader_times[retry]
                else:
                    wait_bootloader = wait_bootloader_times[-1]
                Logger.log("d", "Checking {serial} if baud rate {baud_rate} works. Retry nr: {retry}. Wait timeout: {timeout}".format(
                    serial = self._serial_port, baud_rate = baud_rate, retry = retry, timeout = read_timeout))

                if serial is None:
                    try:
                        serial = Serial(str(self._serial_port), baud_rate, timeout = read_timeout, writeTimeout = write_timeout)
                    except SerialException:
                        Logger.logException("w", "Unable to create serial")
                        continue
                    else:
                        Logger.logException("w", "Unable to create serial: Unknown exception")
                        continue
                else:
                    # We already have a serial connection, just change the baud rate.
                    try:
                        serial.baudrate = baud_rate
                        serial.timeout = read_timeout
                        serial.write_timeout = write_timeout
                    except:
                        Logger.logException("w", "Setting baud rate: Exception")
                        continue
                sleep(wait_bootloader)  # Ensure that we are not talking to the boot loader. 5 seconds seems to be the magic number
                successful_responses = 0

                readBack = serial.read(10000).decode("ASCII")
                # Include the startup log from printer in log
                Logger.log("d", "Printer Init Info\n{ts}".format( ts = readBack ))
                start_timeout_time = time()
                serial.write( b"\nM105\n" )
                readBack = serial.read(10000).decode("ASCII")
                # Clearing the inputbuffer before the command should leave us with the correct reply in place
                if readBack.startswith("ok T:"):
                    self.setResult(baud_rate)
                    Logger.log("d", "Detected baud rate {baud_rate} on serial {serial} on retry {retry} with after {time_elapsed:0.2f} seconds.".format(
                        serial = self._serial_port, baud_rate = baud_rate, retry = retry, time_elapsed = time() - start_timeout_time))
                    serial.close() # close serial port so it can be opened by the USBPrinterOutputDevice
                    return
            sleep(15)  # Give the printer some time to init and try again.
        self.setResult(None)  # Unable to detect the correct baudrate.
