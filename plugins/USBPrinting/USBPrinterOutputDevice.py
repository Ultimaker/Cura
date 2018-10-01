# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Logger import Logger
from UM.i18n import i18nCatalog
from UM.Qt.Duration import DurationFormat
from UM.PluginRegistry import PluginRegistry

from cura.CuraApplication import CuraApplication
from cura.PrinterOutputDevice import PrinterOutputDevice, ConnectionState
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel
from cura.PrinterOutput.GenericOutputController import GenericOutputController

from .AutoDetectBaudJob import AutoDetectBaudJob
from .avr_isp import stk500v2, intelHex

from PyQt5.QtCore import pyqtSlot, pyqtSignal, pyqtProperty, QUrl

from serial import Serial, SerialException, SerialTimeoutException
from threading import Thread, Event
from time import time, sleep
from queue import Queue
from enum import IntEnum
from typing import Union, Optional, List, cast

import re
import functools  # Used for reduce
import os

catalog = i18nCatalog("cura")


class USBPrinterOutputDevice(PrinterOutputDevice):
    firmwareProgressChanged = pyqtSignal()
    firmwareUpdateStateChanged = pyqtSignal()

    def __init__(self, serial_port: str, baud_rate: Optional[int] = None) -> None:
        super().__init__(serial_port)
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

        self._all_baud_rates = [115200, 250000, 230400, 57600, 38400, 19200, 9600]

        # Instead of using a timer, we really need the update to be as a thread, as reading from serial can block.
        self._update_thread = Thread(target=self._update, daemon = True)

        self._update_firmware_thread = Thread(target=self._updateFirmware, daemon = True)

        self._last_temperature_request = None  # type: Optional[int]

        self._is_printing = False  # A print is being sent.

        ## Set when print is started in order to check running time.
        self._print_start_time = None  # type: Optional[float]
        self._print_estimated_time = None  # type: Optional[int]

        self._accepts_commands = True

        self._paused = False

        self._firmware_view = None
        self._firmware_location = None
        self._firmware_progress = 0
        self._firmware_update_state = FirmwareUpdateState.idle

        self.setConnectionText(catalog.i18nc("@info:status", "Connected via USB"))

        # Queue for commands that need to be sent.
        self._command_queue = Queue()   # type: Queue
        # Event to indicate that an "ok" was received from the printer after sending a command.
        self._command_received = Event()
        self._command_received.set()

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

    ## Reset USB device settings
    #
    def resetDeviceSettings(self):
        self._firmware_name = None

    ##  Request the current scene to be sent to a USB-connected printer.
    #
    #   \param nodes A collection of scene nodes to send. This is ignored.
    #   \param file_name \type{string} A suggestion for a file name to write.
    #   \param filter_by_machine Whether to filter MIME types by machine. This
    #   is ignored.
    #   \param kwargs Keyword arguments.
    def requestWrite(self, nodes, file_name = None, filter_by_machine = False, file_handler = None, **kwargs):
        if self._is_printing:
            return  # Aleady printing

        # cancel any ongoing preheat timer before starting a print
        self._printers[0].getController().stopPreheatTimers()

        CuraApplication.getInstance().getController().setActiveStage("MonitorStage")

        # find the G-code for the active build plate to print
        active_build_plate_id = CuraApplication.getInstance().getMultiBuildPlateModel().activeBuildPlate
        gcode_dict = getattr(CuraApplication.getInstance().getController().getScene(), "gcode_dict")
        gcode_list = gcode_dict[active_build_plate_id]

        self._printGCode(gcode_list)

    ##  Show firmware interface.
    #   This will create the view if its not already created.
    def showFirmwareInterface(self):
        if self._firmware_view is None:
            path = os.path.join(PluginRegistry.getInstance().getPluginPath("USBPrinting"), "FirmwareUpdateWindow.qml")
            self._firmware_view = CuraApplication.getInstance().createQmlComponent(path, {"manager": self})

        self._firmware_view.show()

    @pyqtSlot(str)
    def updateFirmware(self, file):
        # the file path could be url-encoded.
        if file.startswith("file://"):
            self._firmware_location = QUrl(file).toLocalFile()
        else:
            self._firmware_location = file
        self.showFirmwareInterface()
        self.setFirmwareUpdateState(FirmwareUpdateState.updating)
        self._update_firmware_thread.start()

    def _updateFirmware(self):
        # Ensure that other connections are closed.
        if self._connection_state != ConnectionState.closed:
            self.close()

        try:
            hex_file = intelHex.readHex(self._firmware_location)
            assert len(hex_file) > 0
        except (FileNotFoundError, AssertionError):
            Logger.log("e", "Unable to read provided hex file. Could not update firmware.")
            self.setFirmwareUpdateState(FirmwareUpdateState.firmware_not_found_error)
            return

        programmer = stk500v2.Stk500v2()
        programmer.progress_callback = self._onFirmwareProgress

        try:
            programmer.connect(self._serial_port)
        except:
            programmer.close()
            Logger.logException("e", "Failed to update firmware")
            self.setFirmwareUpdateState(FirmwareUpdateState.communication_error)
            return

        # Give programmer some time to connect. Might need more in some cases, but this worked in all tested cases.
        sleep(1)
        if not programmer.isConnected():
            Logger.log("e", "Unable to connect with serial. Could not update firmware")
            self.setFirmwareUpdateState(FirmwareUpdateState.communication_error)
        try:
            programmer.programChip(hex_file)
        except SerialException:
            self.setFirmwareUpdateState(FirmwareUpdateState.io_error)
            return
        except:
            self.setFirmwareUpdateState(FirmwareUpdateState.unknown_error)
            return

        programmer.close()

        # Clean up for next attempt.
        self._update_firmware_thread = Thread(target=self._updateFirmware, daemon=True)
        self._firmware_location = ""
        self._onFirmwareProgress(100)
        self.setFirmwareUpdateState(FirmwareUpdateState.completed)

        # Try to re-connect with the machine again, which must be done on the Qt thread, so we use call later.
        CuraApplication.getInstance().callLater(self.connect)

    @pyqtProperty(float, notify = firmwareProgressChanged)
    def firmwareProgress(self):
        return self._firmware_progress

    @pyqtProperty(int, notify=firmwareUpdateStateChanged)
    def firmwareUpdateState(self):
        return self._firmware_update_state

    def setFirmwareUpdateState(self, state):
        if self._firmware_update_state != state:
            self._firmware_update_state = state
            self.firmwareUpdateStateChanged.emit()

    # Callback function for firmware update progress.
    def _onFirmwareProgress(self, progress, max_progress = 100):
        self._firmware_progress = (progress / max_progress) * 100  # Convert to scale of 0-100
        self.firmwareProgressChanged.emit()

    ##  Start a print based on a g-code.
    #   \param gcode_list List with gcode (strings).
    def _printGCode(self, gcode_list: List[str]):
        self._gcode.clear()
        self._paused = False

        for layer in gcode_list:
            self._gcode.extend(layer.split("\n"))

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
        self._firmware_name = None # after each connection ensure that the firmware name is removed

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
                Logger.log("w", "An exception occured while trying to create serial connection")
                return
        container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        num_extruders = container_stack.getProperty("machine_extruder_count", "value")
        # Ensure that a printer is created.
        self._printers = [PrinterOutputModel(output_controller=GenericOutputController(self), number_of_extruders=num_extruders)]
        self._printers[0].updateName(container_stack.getName())
        self.setConnectionState(ConnectionState.connected)
        self._update_thread.start()

    def close(self):
        super().close()
        if self._serial is not None:
            self._serial.close()

        # Re-create the thread so it can be started again later.
        self._update_thread = Thread(target=self._update, daemon=True)
        self._serial = None

    ##  Send a command to printer.
    def sendCommand(self, command: Union[str, bytes]):
        if not self._command_received.is_set():
            self._command_queue.put(command)
        else:
            self._sendCommand(command)
    def _sendCommand(self, command: Union[str, bytes]):
        if self._serial is None or self._connection_state != ConnectionState.connected:
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

    def _update(self):
        while self._connection_state == ConnectionState.connected and self._serial is not None:
            try:
                line = self._serial.readline()
            except:
                continue

            if self._last_temperature_request is None or time() > self._last_temperature_request + self._timeout:
                # Timeout, or no request has been sent at all.
                self._command_received.set() # We haven't really received the ok, but we need to send a new command

                self.sendCommand("M105")
                self._last_temperature_request = time()

                if self._firmware_name is None:
                    self.sendCommand("M115")

            if (b"ok " in line and b"T:" in line) or line.startswith(b"T:") or b"ok B:" in line or line.startswith(b"B:"):  # Temperature message. 'T:' for extruder and 'B:' for bed
                extruder_temperature_matches = re.findall(b"T(\d*): ?([\d\.]+) ?\/?([\d\.]+)?", line)
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

                bed_temperature_matches = re.findall(b"B: ?([\d\.]+) ?\/?([\d\.]+)?", line)
                if bed_temperature_matches:
                    match = bed_temperature_matches[0]
                    if match[0]:
                        self._printers[0].updateBedTemperature(float(match[0]))
                    if match[1]:
                        self._printers[0].updateTargetBedTemperature(float(match[1]))

            if b"FIRMWARE_NAME:" in line:
                self._setFirmwareName(line)

            if b"ok" in line:
                self._command_received.set()
                if not self._command_queue.empty():
                    self._sendCommand(self._command_queue.get())
                if self._is_printing:
                    if self._paused:
                        pass  # Nothing to do!
                    else:
                        self._sendNextGcodeLine()

            if self._is_printing:
                if line.startswith(b'!!'):
                    Logger.log('e', "Printer signals fatal error. Cancelling print. {}".format(line))
                    self.cancelPrint()
                elif b"resend" in line.lower() or b"rs" in line:
                    # A resend can be requested either by Resend, resend or rs.
                    try:
                        self._gcode_position = int(line.replace(b"N:", b" ").replace(b"N", b" ").replace(b":", b" ").split()[-1])
                    except:
                        if b"rs" in line:
                            # In some cases of the RS command it needs to be handled differently.
                            self._gcode_position = int(line.split()[1])

    def _setFirmwareName(self, name):
        new_name = re.findall(r"FIRMWARE_NAME:(.*);", str(name))
        if  new_name:
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
        if self._gcode_position >= len(self._gcode):
            self._printers[0].updateActivePrintJob(None)
            self._is_printing = False
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
            print_job = PrintJobOutputModel(output_controller = GenericOutputController(self), name= CuraApplication.getInstance().getPrintInformation().jobName)
            print_job.updateState("printing")
            self._printers[0].updateActivePrintJob(print_job)

        print_job.updateTimeElapsed(elapsed_time)
        estimated_time = self._print_estimated_time
        if progress > .1:
            estimated_time = self._print_estimated_time * (1 - progress) + elapsed_time
        print_job.updateTimeTotal(estimated_time)

        self._gcode_position += 1


class FirmwareUpdateState(IntEnum):
    idle = 0
    updating = 1
    completed = 2
    unknown_error = 3
    communication_error = 4
    io_error = 5
    firmware_not_found_error = 6
