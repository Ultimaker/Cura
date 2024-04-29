# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Job import Job
from UM.Logger import Logger

from time import time, sleep
from serial import Serial, SerialException


#   An async job that attempts to find the correct baud rate for a USB printer.
#   It tries a pre-set list of baud rates. All these baud rates are validated by requesting the temperature a few times
#   and checking if the results make sense. If getResult() is not None, it was able to find a correct baud rate.
class AutoDetectBaudJob(Job):
    def __init__(self, serial_port: int) -> None:
        super().__init__()
        self._serial_port = serial_port
        self._all_baud_rates = [115200, 250000, 500000, 230400, 76800, 57600, 38400, 19200, 9600]

    def run(self) -> None:
        Logger.debug(f"Auto detect baud rate started for {self._serial_port}")
        wait_response_timeouts = [3, 15, 30]
        wait_bootloader_times = [1.5, 5, 15]
        write_timeout = 3
        read_timeout = 3
        tries = 2
        serial = None

        for retry in range(tries):
            for baud_rate in self._all_baud_rates:
                if retry < len(wait_response_timeouts):
                    wait_response_timeout = wait_response_timeouts[retry]
                else:
                    wait_response_timeout = wait_response_timeouts[-1]
                if retry < len(wait_bootloader_times):
                    wait_bootloader = wait_bootloader_times[retry]
                else:
                    wait_bootloader = wait_bootloader_times[-1]
                Logger.debug(f"Checking {self._serial_port} if baud rate {baud_rate} works. Retry nr: {retry}. Wait timeout: {wait_response_timeout}")

                if serial is None:
                    try:
                        serial = Serial(str(self._serial_port), baud_rate, timeout = read_timeout, writeTimeout = write_timeout)
                    except SerialException:
                        Logger.warning(f"Unable to create serial connection to {serial} with baud rate {baud_rate}")
                        continue
                else:
                    # We already have a serial connection, just change the baud rate.
                    try:
                        serial.baudrate = baud_rate
                    except ValueError:
                        continue

                # Ensure that we are not talking to the boot loader. 1.5 seconds seems to be the magic number
                sleep(wait_bootloader)

                serial.write(b"\n")  # Ensure we clear out previous responses
                serial.write(b"M105\n")

                start_timeout_time = time()
                timeout_time = time() + wait_response_timeout

                while timeout_time > time():
                    # If baudrate is wrong, then readline() might never
                    # return, even with timeouts set. Using read_until
                    # with size limit seems to fix this.
                    line = serial.read_until(size = 100)
                    if b"ok" in line and b"T:" in line:
                        self.setResult(baud_rate)
                        Logger.log("d", "Detected baud rate {baud_rate} on serial {serial} on retry {retry} with after {time_elapsed:0.2f} seconds.".format(
                            serial = self._serial_port, baud_rate = baud_rate, retry = retry, time_elapsed = time() - start_timeout_time))
                        serial.close() # close serial port so it can be opened by the USBPrinterOutputDevice
                        return

                    serial.write(b"M105\n")
            sleep(15)  # Give the printer some time to init and try again.
        Logger.debug(f"Unable to find a working baudrate for {serial}")
        self.setResult(None)  # Unable to detect the correct baudrate.
