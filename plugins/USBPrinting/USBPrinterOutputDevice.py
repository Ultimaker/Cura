# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Logger import Logger
from UM.i18n import i18nCatalog
from UM.Application import Application

from cura.PrinterOutputDevice import PrinterOutputDevice, ConnectionState
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel

from .AutoDetectBaudJob import AutoDetectBaudJob

from serial import Serial, SerialException
from threading import Thread
from time import time

import re

catalog = i18nCatalog("cura")


class USBPrinterOutputDevice(PrinterOutputDevice):
    def __init__(self, serial_port, baud_rate = None):
        super().__init__(serial_port)
        self.setName(catalog.i18nc("@item:inmenu", "USB printing"))
        self.setShortDescription(catalog.i18nc("@action:button Preceded by 'Ready to'.", "Print via USB"))
        self.setDescription(catalog.i18nc("@info:tooltip", "Print via USB"))
        self.setIconName("print")

        self._serial = None
        self._serial_port = serial_port

        self._timeout = 3

        self._use_auto_detect = True

        self._baud_rate = baud_rate
        self._all_baud_rates = [115200, 250000, 230400, 57600, 38400, 19200, 9600]

        # Instead of using a timer, we really need the update to be as a thread, as reading from serial can block.
        self._update_thread = Thread(target=self._update, daemon = True)

        self._last_temperature_request = None

    def _autoDetectFinished(self, job):
        result = job.getResult()
        if result is not None:
            self.setBaudRate(result)
            self.connect()  # Try to connect (actually create serial, etc)

    def setBaudRate(self, baud_rate):
        if baud_rate not in self._all_baud_rates:
            Logger.log("w", "Not updating baudrate to {baud_rate} as it's an unknown baudrate".format(baud_rate=baud_rate))
            return

        self._baud_rate = baud_rate

    def connect(self):
        if self._baud_rate is None:
            if self._use_auto_detect:
                auto_detect_job = AutoDetectBaudJob(self._serial_port)
                auto_detect_job.start()
                auto_detect_job.finished.connect(self._autoDetectFinished)
            return
        if self._serial is None:
            try:
                self._serial = Serial(str(self._serial_port), self._baud_rate, timeout=self._timeout, writeTimeout=self._timeout)
            except SerialException:
                return
        container_stack = Application.getInstance().getGlobalContainerStack()
        num_extruders = container_stack.getProperty("machine_extruder_count", "value")

        # Ensure that a printer is created.
        self._printers = [PrinterOutputModel(output_controller=None, number_of_extruders=num_extruders)]
        self.setConnectionState(ConnectionState.connected)
        self._update_thread.start()

    def sendCommand(self, command):
        if self._connection_state == ConnectionState.connected:
            self._sendCommand(command)

    def _sendCommand(self, command):
        if self._serial is None:
            return

        if type(command == str):q
            command = (command + "\n").encode()
        if not command.endswith(b"\n"):
            command += b"\n"

        self._serial.write(b"\n")
        self._serial.write(command)

    def _update(self):
        while self._connection_state == ConnectionState.connected and self._serial is not None:
            line = self._serial.readline()
            if self._last_temperature_request is None or time() > self._last_temperature_request + self._timeout:
                # Timeout, or no request has been sent at all.
                self.sendCommand("M105")
                self._last_temperature_request = time()

            if b"ok T:" in line or line.startswith(b"T:"):  # Temperature message
                extruder_temperature_matches = re.findall(b"T(\d*): ?([\d\.]+) ?\/?([\d\.]+)?", line)
                # Update all temperature values
                for match, extruder in zip(extruder_temperature_matches, self._printers[0].extruders):
                    extruder.updateHotendTemperature(float(match[1]))
                    extruder.updateTargetHotendTemperature(float(match[2]))

                bed_temperature_matches = re.findall(b"B: ?([\d\.]+) ?\/?([\d\.]+)?", line)
                match = bed_temperature_matches[0]
                if match[0]:
                    self._printers[0].updateBedTemperature(float(match[0]))
                if match[1]:
                    self._printers[0].updateTargetBedTemperature(float(match[1]))
