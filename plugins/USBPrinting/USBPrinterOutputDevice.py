# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Logger import Logger
from UM.i18n import i18nCatalog
from UM.Application import Application
from UM.Qt.Duration import DurationFormat

from cura.PrinterOutputDevice import PrinterOutputDevice, ConnectionState
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel

from .AutoDetectBaudJob import AutoDetectBaudJob

from serial import Serial, SerialException
from threading import Thread
from time import time
from queue import Queue

import re
import functools  # Used for reduce

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

        # List of gcode lines to be printed
        self._gcode = []
        self._gcode_position = 0

        self._use_auto_detect = True

        self._baud_rate = baud_rate


        self._all_baud_rates = [115200, 250000, 230400, 57600, 38400, 19200, 9600]

        # Instead of using a timer, we really need the update to be as a thread, as reading from serial can block.
        self._update_thread = Thread(target=self._update, daemon = True)

        self._last_temperature_request = None

        self._is_printing = False  # A print is being sent.

        ## Set when print is started in order to check running time.
        self._print_start_time = None
        self._print_estimated_time = None

        # Queue for commands that need to be send. Used when command is sent when a print is active.
        self._command_queue = Queue()

    ##  Request the current scene to be sent to a USB-connected printer.
    #
    #   \param nodes A collection of scene nodes to send. This is ignored.
    #   \param file_name \type{string} A suggestion for a file name to write.
    #   \param filter_by_machine Whether to filter MIME types by machine. This
    #   is ignored.
    #   \param kwargs Keyword arguments.
    def requestWrite(self, nodes, file_name = None, filter_by_machine = False, file_handler = None, **kwargs):
        gcode_list = getattr(Application.getInstance().getController().getScene(), "gcode_list")
        self._printGCode(gcode_list)

    ##  Start a print based on a g-code.
    #   \param gcode_list List with gcode (strings).
    def _printGCode(self, gcode_list):
        self._gcode.clear()

        for layer in gcode_list:
            self._gcode.extend(layer.split("\n"))

        # Reset line number. If this is not done, first line is sometimes ignored
        self._gcode.insert(0, "M110")
        self._gcode_position = 0
        self._is_printing = True
        self._print_start_time = time()

        self._print_estimated_time = int(Application.getInstance().getPrintInformation().currentPrintTime.getDisplayString(DurationFormat.Format.Seconds))

        for i in range(0, 4):  # Push first 4 entries before accepting other inputs
            self._sendNextGcodeLine()

        self.writeFinished.emit(self)


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
        if self._is_printing:
            self._command_queue.put(command)
        elif self._connection_state == ConnectionState.connected:
            self._sendCommand(command)

    def _sendCommand(self, command):
        if self._serial is None:
            return

        if type(command == str):
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
                    if match[1]:
                        extruder.updateHotendTemperature(float(match[1]))
                    if match[2]:
                        extruder.updateTargetHotendTemperature(float(match[2]))

                bed_temperature_matches = re.findall(b"B: ?([\d\.]+) ?\/?([\d\.]+)?", line)
                if bed_temperature_matches:
                    match = bed_temperature_matches[0]
                    if match[0]:
                        self._printers[0].updateBedTemperature(float(match[0]))
                    if match[1]:
                        self._printers[0].updateTargetBedTemperature(float(match[1]))

            if self._is_printing:
                if b"ok" in line:
                    if not self._command_queue.empty():
                        self._sendCommand(self._command_queue.get())
                    else:
                        self._sendNextGcodeLine()
                elif b"resend" in line.lower() or b"rs" in line:
                    # A resend can be requested either by Resend, resend or rs.
                    try:
                        self._gcode_position = int(line.replace(b"N:", b" ").replace(b"N", b" ").replace(b":", b" ").split()[-1])
                    except:
                        if b"rs" in line:
                            # In some cases of the RS command it needs to be handled differently.
                            self._gcode_position = int(line.split()[1])

    def _sendNextGcodeLine(self):
        if self._gcode_position >= len(self._gcode):
            return
        line = self._gcode[self._gcode_position]

        if ";" in line:
            line = line[:line.find(";")]

        line = line.strip()

        # Don't send empty lines. But we do have to send something, so send M105 instead.
        # Don't send the M0 or M1 to the machine, as M0 and M1 are handled as an LCD menu pause.
        if line == "" or line == "M0" or line == "M1":
            line = "M105"

        checksum = functools.reduce(lambda x, y: x ^ y, map(ord, "N%d%s" % (self._gcode_position, line)))

        self._sendCommand("N%d%s*%d" % (self._gcode_position, line, checksum))

        progress = (self._gcode_position / len(self._gcode))

        elapsed_time = int(time() - self._print_start_time)
        print_job = self._printers[0].activePrintJob
        if print_job is None:
            print_job = PrintJobOutputModel(output_controller = None)
            self._printers[0].updateActivePrintJob(print_job)

        print_job.updateTimeElapsed(elapsed_time)
        estimated_time = self._print_estimated_time
        if progress > .1:
            estimated_time = self._print_estimated_time * (1 - progress) + elapsed_time
        print_job.updateTimeTotal(estimated_time)

        self._gcode_position += 1
