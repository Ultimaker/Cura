# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os

from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Mesh.MeshWriter import MeshWriter #To get the g-code output.
from UM.Message import Message #Show an error when already printing.
from UM.PluginRegistry import PluginRegistry #To get the g-code output.
from UM.Qt.Duration import DurationFormat

from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.PrinterOutputDevice import PrinterOutputDevice, ConnectionState, ConnectionType
from cura.PrinterOutput.Models.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.Models.PrintJobOutputModel import PrintJobOutputModel
from cura.PrinterOutput.GenericOutputController import GenericOutputController

from .AutoDetectBaudJob import AutoDetectBaudJob
from .AvrFirmwareUpdater import AvrFirmwareUpdater

from io import StringIO #To write the g-code output.
from queue import Queue
from serial import Serial, SerialException, SerialTimeoutException
from threading import Thread, Event
from time import time
from typing import Union, Optional, List, cast, TYPE_CHECKING

import re
import functools  # Used for reduce

if TYPE_CHECKING:
    from UM.FileHandler.FileHandler import FileHandler
    from UM.Scene.SceneNode import SceneNode

catalog = i18nCatalog("cura")


class USBPrinterOutputDevice(PrinterOutputDevice):
    def __init__(self, serial_port: str, baud_rate: Optional[int] = None) -> None:
        super().__init__(serial_port, connection_type = ConnectionType.UsbConnection)
        self.setName(catalog.i18nc("@item:inmenu", "USB printing"))
        self.setShortDescription(catalog.i18nc("@action:button Preceded by 'Ready to'.", "Print via USB"))
        self.setDescription(catalog.i18nc("@info:tooltip", "Print via USB"))
        self.setIconName("print")

        self._serial = None  # type: Optional[Serial]
        self._serial_port = serial_port
        self._address = serial_port

        self._timeout = 3

        # List of gcode lines to be printed
        self._gcode = [] # type: List[str]
        self._gcode_position = 0

        self._use_auto_detect = True

        self._baud_rate = baud_rate

        self._all_baud_rates = [115200, 250000, 500000, 230400, 57600, 38400, 19200, 9600]

        # Instead of using a timer, we really need the update to be as a thread, as reading from serial can block.
        self._update_thread = Thread(target = self._update, daemon = True, name = "USBPrinterUpdate")

        self._last_temperature_request = None  # type: Optional[int]
        self._firmware_idle_count = 0

        self._is_printing = False  # A print is being sent.

        ## Set when print is started in order to check running time.
        self._print_start_time = None  # type: Optional[float]
        self._print_estimated_time = None  # type: Optional[int]

        self._accepts_commands = True

        self._paused = False
        self._printer_busy = False  # When printer is preheating and waiting (M190/M109), or when waiting for action on the printer

        self.setConnectionText(catalog.i18nc("@info:status", "Connected via USB"))

        # Queue for commands that need to be sent.
        self._command_queue = Queue()   # type: Queue
        # Event to indicate that an "ok" was received from the printer after sending a command.
        self._command_received = Event()
        self._command_received.set()

        self._firmware_name_requested = False
        self._firmware_updater = AvrFirmwareUpdater(self)

        plugin_path = cast(str, PluginRegistry.getInstance().getPluginPath("USBPrinting"))
        self._monitor_view_qml_path = os.path.join(plugin_path, "MonitorItem.qml")

        CuraApplication.getInstance().getOnExitCallbackManager().addCallback(self._checkActivePrintingUponAppExit)

    # This is a callback function that checks if there is any printing in progress via USB when the application tries
    # to exit. If so, it will show a confirmation before
    def _checkActivePrintingUponAppExit(self) -> None:
        application = CuraApplication.getInstance()
        if not self._is_printing:
            # This USB printer is not printing, so we have nothing to do. Call the next callback if exists.
            application.triggerNextExitCheck()
            return

        application.setConfirmExitDialogCallback(self._onConfirmExitDialogResult)
        application.showConfirmExitDialog.emit(catalog.i18nc("@label", "A USB print is in progress, closing Cura will stop this print. Are you sure?"))

    def _onConfirmExitDialogResult(self, result: bool) -> None:
        if result:
            application = CuraApplication.getInstance()
            application.triggerNextExitCheck()

    def resetDeviceSettings(self) -> None:
        """Reset USB device settings"""

        self._firmware_name = None

    def requestWrite(self, nodes: List["SceneNode"], file_name: Optional[str] = None, limit_mimetypes: bool = False,
                     file_handler: Optional["FileHandler"] = None, filter_by_machine: bool = False, **kwargs) -> None:
        """Request the current scene to be sent to a USB-connected printer.
        
        :param nodes: A collection of scene nodes to send. This is ignored.
        :param file_name: A suggestion for a file name to write.
        :param filter_by_machine: Whether to filter MIME types by machine. This
               is ignored.
        :param kwargs: Keyword arguments.
        """

        if self._is_printing:
            message = Message(text = catalog.i18nc("@message", "A print is still in progress. Cura cannot start another print via USB until the previous print has completed."), title = catalog.i18nc("@message", "Print in Progress"))
            message.show()
            return  # Already printing
        self.writeStarted.emit(self)
        # cancel any ongoing preheat timer before starting a print
        controller = cast(GenericOutputController, self._printers[0].getController())
        controller.stopPreheatTimers()

        CuraApplication.getInstance().getController().setActiveStage("MonitorStage")

        #Find the g-code to print.
        gcode_textio = StringIO()
        gcode_writer = cast(MeshWriter, PluginRegistry.getInstance().getPluginObject("GCodeWriter"))
        success = gcode_writer.write(gcode_textio, None)
        if not success:
            return

        self._printGCode(gcode_textio.getvalue())

    def _printGCode(self, gcode: str):
        """Start a print based on a g-code.
        
        :param gcode: The g-code to print.
        """
        self._gcode.clear()
        self._paused = False

        self._gcode.extend(gcode.split("\n"))

        # Reset line number. If this is not done, first line is sometimes ignored
        self._gcode.insert(0, "M110")
        self._gcode_position = 0
        self._print_start_time = time()

        self._print_estimated_time = int(CuraApplication.getInstance().getPrintInformation().currentPrintTime.getDisplayString(DurationFormat.Format.Seconds))

        for i in range(0, 4):  # Push first 4 entries before accepting other inputs
            self._sendNextGcodeLine()

        self._is_printing = True
        self.writeFinished.emit(self)

    def _autoDetectFinished(self, job: AutoDetectBaudJob):
        result = job.getResult()
        if result is not None:
            self.setBaudRate(result)
            self.connect()  # Try to connect (actually create serial, etc)

    def setBaudRate(self, baud_rate: int):
        if baud_rate not in self._all_baud_rates:
            Logger.log("w", "Not updating baudrate to {baud_rate} as it's an unknown baudrate".format(baud_rate=baud_rate))
            return

        self._baud_rate = baud_rate

    def connect(self):
        self._firmware_name = None  # after each connection ensure that the firmware name is removed

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
                Logger.warning("An exception occurred while trying to create serial connection.")
                return
            except OSError as e:
                Logger.warning("The serial device is suddenly unavailable while trying to create a serial connection: {err}".format(err = str(e)))
                return
        CuraApplication.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerStackChanged)
        self._onGlobalContainerStackChanged()
        self.setConnectionState(ConnectionState.Connected)
        self._update_thread.start()

    def _onGlobalContainerStackChanged(self):
        container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        num_extruders = container_stack.getProperty("machine_extruder_count", "value")
        # Ensure that a printer is created.
        controller = GenericOutputController(self)
        controller.setCanUpdateFirmware(True)
        self._printers = [PrinterOutputModel(output_controller = controller, number_of_extruders = num_extruders)]
        self._printers[0].updateName(container_stack.getName())

    def close(self):
        super().close()
        if self._serial is not None:
            self._serial.close()

        # Re-create the thread so it can be started again later.
        self._update_thread = Thread(target=self._update, daemon=True, name = "USBPrinterUpdate")
        self._serial = None

    def sendCommand(self, command: Union[str, bytes]):
        """Send a command to printer."""

        if not self._command_received.is_set():
            self._command_queue.put(command)
        else:
            self._sendCommand(command)

    def _sendCommand(self, command: Union[str, bytes]):
        if self._serial is None or self._connection_state != ConnectionState.Connected:
            return

        new_command = cast(bytes, command) if type(command) is bytes else cast(str, command).encode() # type: bytes
        if not new_command.endswith(b"\n"):
            new_command += b"\n"
        try:
            self._command_received.clear()
            self._serial.write(new_command)
        except SerialTimeoutException:
            Logger.log("w", "Timeout when sending command to printer via USB.")
            self._command_received.set()
        except SerialException:
            Logger.logException("w", "An unexpected exception occurred while writing to the serial.")
            self.setConnectionState(ConnectionState.Error)

    def _update(self):
        while self._connection_state == ConnectionState.Connected and self._serial is not None:
            try:
                line = self._serial.readline()
            except:
                continue

            if not self._firmware_name_requested:
                self._firmware_name_requested = True
                self.sendCommand("M115")

            if b"FIRMWARE_NAME:" in line:
                self._setFirmwareName(line)

            if self._last_temperature_request is None or time() > self._last_temperature_request + self._timeout:
                # Timeout, or no request has been sent at all.
                if not self._printer_busy: # Don't flood the printer with temperature requests while it is busy
                    self.sendCommand("M105")
                    self._last_temperature_request = time()

            if re.search(b"[B|T\d*]: ?\d+\.?\d*", line):  # Temperature message. 'T:' for extruder and 'B:' for bed
                extruder_temperature_matches = re.findall(b"T(\d*): ?(\d+\.?\d*)\s*\/?(\d+\.?\d*)?", line)
                # Update all temperature values
                matched_extruder_nrs = []
                for match in extruder_temperature_matches:
                    extruder_nr = 0
                    if match[0] != b"":
                        extruder_nr = int(match[0])

                    if extruder_nr in matched_extruder_nrs:
                        continue
                    matched_extruder_nrs.append(extruder_nr)

                    if extruder_nr >= len(self._printers[0].extruders):
                        Logger.log("w", "Printer reports more temperatures than the number of configured extruders")
                        continue

                    extruder = self._printers[0].extruders[extruder_nr]
                    if match[1]:
                        extruder.updateHotendTemperature(float(match[1]))
                    if match[2]:
                        extruder.updateTargetHotendTemperature(float(match[2]))

                bed_temperature_matches = re.findall(b"B: ?(\d+\.?\d*)\s*\/?(\d+\.?\d*)?", line)
                if bed_temperature_matches:
                    match = bed_temperature_matches[0]
                    if match[0]:
                        self._printers[0].updateBedTemperature(float(match[0]))
                    if match[1]:
                        self._printers[0].updateTargetBedTemperature(float(match[1]))

            if line == b"":
                # An empty line means that the firmware is idle
                # Multiple empty lines probably means that the firmware and Cura are waiting
                # for eachother due to a missed "ok", so we keep track of empty lines
                self._firmware_idle_count += 1
            else:
                self._firmware_idle_count = 0

            if line.startswith(b"ok") or self._firmware_idle_count > 1:
                self._printer_busy = False

                self._command_received.set()
                if not self._command_queue.empty():
                    self._sendCommand(self._command_queue.get())
                elif self._is_printing:
                    if self._paused:
                        pass  # Nothing to do!
                    else:
                        self._sendNextGcodeLine()

            if line.startswith(b"echo:busy:"):
                self._printer_busy = True

            if self._is_printing:
                if line.startswith(b'!!'):
                    Logger.log('e', "Printer signals fatal error. Cancelling print. {}".format(line))
                    self.cancelPrint()
                elif line.lower().startswith(b"resend") or line.startswith(b"rs"):
                    # A resend can be requested either by Resend, resend or rs.
                    try:
                        self._gcode_position = int(line.replace(b"N:", b" ").replace(b"N", b" ").replace(b":", b" ").split()[-1])
                    except:
                        if line.startswith(b"rs"):
                            # In some cases of the RS command it needs to be handled differently.
                            self._gcode_position = int(line.split()[1])

    def _setFirmwareName(self, name):
        new_name = re.findall(r"FIRMWARE_NAME:(.*);", str(name))
        if new_name:
            self._firmware_name = new_name[0]
            Logger.log("i", "USB output device Firmware name: %s", self._firmware_name)
        else:
            self._firmware_name = "Unknown"
            Logger.log("i", "Unknown USB output device Firmware name: %s", str(name))

    def getFirmwareName(self):
        return self._firmware_name

    def pausePrint(self):
        self._paused = True

    def resumePrint(self):
        self._paused = False
        self._sendNextGcodeLine() #Send one line of g-code next so that we'll trigger an "ok" response loop even if we're not polling temperatures.

    def cancelPrint(self):
        self._gcode_position = 0
        self._gcode.clear()
        self._printers[0].updateActivePrintJob(None)
        self._is_printing = False
        self._paused = False

        # Turn off temperatures, fan and steppers
        self._sendCommand("M140 S0")
        self._sendCommand("M104 S0")
        self._sendCommand("M107")

        # Home XY to prevent nozzle resting on aborted print
        # Don't home bed because it may crash the printhead into the print on printers that home on the bottom
        self.printers[0].homeHead()
        self._sendCommand("M84")

    def _sendNextGcodeLine(self):
        """
        Send the next line of g-code, at the current `_gcode_position`, via a
        serial port to the printer.

        If the print is done, this sets `_is_printing` to `False` as well.
        """
        try:
            line = self._gcode[self._gcode_position]
        except IndexError:  # End of print, or print got cancelled.
            self._printers[0].updateActivePrintJob(None)
            self._is_printing = False
            return

        if ";" in line:
            line = line[:line.find(";")]

        line = line.strip()

        # Don't send empty lines. But we do have to send something, so send M105 instead.
        # Don't send the M0 or M1 to the machine, as M0 and M1 are handled as an LCD menu pause.
        if line == "" or line == "M0" or line == "M1":
            line = "M105"

        checksum = functools.reduce(lambda x, y: x ^ y, map(ord, "N%d%s" % (self._gcode_position, line)))

        self._sendCommand("N%d%s*%d" % (self._gcode_position, line, checksum))

        print_job = self._printers[0].activePrintJob
        try:
            progress = self._gcode_position / len(self._gcode)
        except ZeroDivisionError:
            # There is nothing to send!
            if print_job is not None:
                print_job.updateState("error")
            return

        elapsed_time = int(time() - self._print_start_time)

        if print_job is None:
            controller = GenericOutputController(self)
            controller.setCanUpdateFirmware(True)
            print_job = PrintJobOutputModel(output_controller = controller, name = CuraApplication.getInstance().getPrintInformation().jobName)
            print_job.updateState("printing")
            self._printers[0].updateActivePrintJob(print_job)

        print_job.updateTimeElapsed(elapsed_time)
        estimated_time = self._print_estimated_time
        if progress > .1:
            estimated_time = self._print_estimated_time * (1 - progress) + elapsed_time
        print_job.updateTimeTotal(estimated_time)

        self._gcode_position += 1
