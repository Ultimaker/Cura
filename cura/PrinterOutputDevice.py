# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.i18n import i18nCatalog
from UM.OutputDevice.OutputDevice import OutputDevice
from PyQt5.QtCore import pyqtProperty, pyqtSlot, QObject, QTimer, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
from enum import IntEnum  # For the connection state tracking.

from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Logger import Logger
from UM.Signal import signalemitter
from UM.Application import Application

i18n_catalog = i18nCatalog("cura")

##  Printer output device adds extra interface options on top of output device.
#
#   The assumption is made the printer is a FDM printer.
#
#   Note that a number of settings are marked as "final". This is because decorators
#   are not inherited by children. To fix this we use the private counter part of those
#   functions to actually have the implementation.
#
#   For all other uses it should be used in the same way as a "regular" OutputDevice.
@signalemitter
class PrinterOutputDevice(QObject, OutputDevice):
    def __init__(self, device_id, parent = None):
        super().__init__(device_id = device_id, parent = parent)

        self._container_registry = ContainerRegistry.getInstance()
        self._target_bed_temperature = 0
        self._bed_temperature = 0
        self._num_extruders = 1
        self._hotend_temperatures = [0] * self._num_extruders
        self._target_hotend_temperatures = [0] * self._num_extruders
        self._material_ids = [""] * self._num_extruders
        self._hotend_ids = [""] * self._num_extruders
        self._progress = 0
        self._head_x = 0
        self._head_y = 0
        self._head_z = 0
        self._connection_state = ConnectionState.closed
        self._connection_text = ""
        self._time_elapsed = 0
        self._time_total = 0
        self._job_state = ""
        self._job_name = ""
        self._error_text = ""
        self._accepts_commands = True
        self._preheat_bed_timeout = 900  # Default time-out for pre-heating the bed, in seconds.
        self._preheat_bed_timer = QTimer()  # Timer that tracks how long to preheat still.
        self._preheat_bed_timer.setSingleShot(True)
        self._preheat_bed_timer.timeout.connect(self.cancelPreheatBed)

        self._printer_state = ""
        self._printer_type = "unknown"

        self._camera_active = False

        self._monitor_view_qml_path = ""
        self._monitor_item = None

        self._control_view_qml_path = ""
        self._control_item = None

        self._qml_context = None
        self._can_pause = True
        self._can_abort = True
        self._can_pre_heat_bed = True
        self._can_control_manually = True

    def requestWrite(self, nodes, file_name = None, filter_by_machine = False, file_handler = None):
        raise NotImplementedError("requestWrite needs to be implemented")

    ## Signals

    # Signal to be emitted when bed temp is changed
    bedTemperatureChanged = pyqtSignal()

    # Signal to be emitted when target bed temp is changed
    targetBedTemperatureChanged = pyqtSignal()

    # Signal when the progress is changed (usually when this output device is printing / sending lots of data)
    progressChanged = pyqtSignal()

    # Signal to be emitted when hotend temp is changed
    hotendTemperaturesChanged = pyqtSignal()

    # Signal to be emitted when target hotend temp is changed
    targetHotendTemperaturesChanged = pyqtSignal()

    # Signal to be emitted when head position is changed (x,y,z)
    headPositionChanged = pyqtSignal()

    # Signal to be emitted when either of the material ids is changed
    materialIdChanged = pyqtSignal(int, str, arguments = ["index", "id"])

    # Signal to be emitted when either of the hotend ids is changed
    hotendIdChanged = pyqtSignal(int, str, arguments = ["index", "id"])

    # Signal that is emitted every time connection state is changed.
    # it also sends it's own device_id (for convenience sake)
    connectionStateChanged = pyqtSignal(str)

    connectionTextChanged = pyqtSignal()

    timeElapsedChanged = pyqtSignal()

    timeTotalChanged = pyqtSignal()

    jobStateChanged = pyqtSignal()

    jobNameChanged = pyqtSignal()

    errorTextChanged = pyqtSignal()

    acceptsCommandsChanged = pyqtSignal()

    printerStateChanged = pyqtSignal()

    printerTypeChanged = pyqtSignal()

    # Signal to be emitted when some drastic change occurs in the remaining time (not when the time just passes on normally).
    preheatBedRemainingTimeChanged = pyqtSignal()

    # Does the printer support pre-heating the bed at all
    @pyqtProperty(bool, constant=True)
    def canPreHeatBed(self):
        return self._can_pre_heat_bed

    # Does the printer support pause at all
    @pyqtProperty(bool,  constant=True)
    def canPause(self):
        return self._can_pause

    # Does the printer support abort at all
    @pyqtProperty(bool, constant=True)
    def canAbort(self):
        return self._can_abort

    # Does the printer support manual control at all
    @pyqtProperty(bool, constant=True)
    def canControlManually(self):
        return self._can_control_manually

    @pyqtProperty(QObject, constant=True)
    def monitorItem(self):
        # Note that we specifically only check if the monitor component is created.
        # It could be that it failed to actually create the qml item! If we check if the item was created, it will try to
        # create the item (and fail) every time.
        if not self._monitor_item:
            self._createMonitorViewFromQML()
        return self._monitor_item

    @pyqtProperty(QObject, constant=True)
    def controlItem(self):
        if not self._control_item:
            self._createControlViewFromQML()
        return self._control_item

    def _createControlViewFromQML(self):
        if not self._control_view_qml_path:
            return

        self._control_item = Application.getInstance().createQmlComponent(self._control_view_qml_path, {
            "OutputDevice": self
        })

    def _createMonitorViewFromQML(self):
        if not self._monitor_view_qml_path:
            return

        self._monitor_item = Application.getInstance().createQmlComponent(self._monitor_view_qml_path, {
            "OutputDevice": self
        })

    @pyqtProperty(str, notify=printerTypeChanged)
    def printerType(self):
        return self._printer_type

    @pyqtProperty(str, notify=printerStateChanged)
    def printerState(self):
        return self._printer_state

    @pyqtProperty(str, notify = jobStateChanged)
    def jobState(self):
        return self._job_state

    def _updatePrinterType(self, printer_type):
        if self._printer_type != printer_type:
            self._printer_type = printer_type
            self.printerTypeChanged.emit()

    def _updatePrinterState(self, printer_state):
        if self._printer_state != printer_state:
            self._printer_state = printer_state
            self.printerStateChanged.emit()

    def _updateJobState(self, job_state):
        if self._job_state != job_state:
            self._job_state = job_state
            self.jobStateChanged.emit()

    @pyqtSlot(str)
    def setJobState(self, job_state):
        self._setJobState(job_state)

    def _setJobState(self, job_state):
        Logger.log("w", "_setJobState is not implemented by this output device")

    @pyqtSlot()
    def startCamera(self):
        self._camera_active = True
        self._startCamera()

    def _startCamera(self):
        Logger.log("w", "_startCamera is not implemented by this output device")

    @pyqtSlot()
    def stopCamera(self):
        self._camera_active = False
        self._stopCamera()

    def _stopCamera(self):
        Logger.log("w", "_stopCamera is not implemented by this output device")

    @pyqtProperty(str, notify = jobNameChanged)
    def jobName(self):
        return self._job_name

    def setJobName(self, name):
        if self._job_name != name:
            self._job_name = name
            self.jobNameChanged.emit()

    ##  Gives a human-readable address where the device can be found.
    @pyqtProperty(str, constant = True)
    def address(self):
        Logger.log("w", "address is not implemented by this output device.")

    ##  A human-readable name for the device.
    @pyqtProperty(str, constant = True)
    def name(self):
        Logger.log("w", "name is not implemented by this output device.")
        return ""

    @pyqtProperty(str, notify = errorTextChanged)
    def errorText(self):
        return self._error_text

    ##  Set the error-text that is shown in the print monitor in case of an error
    def setErrorText(self, error_text):
        if self._error_text != error_text:
            self._error_text = error_text
            self.errorTextChanged.emit()

    @pyqtProperty(bool, notify = acceptsCommandsChanged)
    def acceptsCommands(self):
        return self._accepts_commands

    ##  Set a flag to signal the UI that the printer is not (yet) ready to receive commands
    def setAcceptsCommands(self, accepts_commands):
        if self._accepts_commands != accepts_commands:
            self._accepts_commands = accepts_commands
            self.acceptsCommandsChanged.emit()

    ##  Get the bed temperature of the bed (if any)
    #   This function is "final" (do not re-implement)
    #   /sa _getBedTemperature implementation function
    @pyqtProperty(float, notify = bedTemperatureChanged)
    def bedTemperature(self):
        return self._bed_temperature

    ##  Set the (target) bed temperature
    #   This function is "final" (do not re-implement)
    #   /param temperature new target temperature of the bed (in deg C)
    #   /sa _setTargetBedTemperature implementation function
    @pyqtSlot(int)
    def setTargetBedTemperature(self, temperature):
        self._setTargetBedTemperature(temperature)
        if self._target_bed_temperature != temperature:
            self._target_bed_temperature = temperature
            self.targetBedTemperatureChanged.emit()

    ##  The total duration of the time-out to pre-heat the bed, in seconds.
    #
    #   \return The duration of the time-out to pre-heat the bed, in seconds.
    @pyqtProperty(int, constant = True)
    def preheatBedTimeout(self):
        return self._preheat_bed_timeout

    ##  The remaining duration of the pre-heating of the bed.
    #
    #   This is formatted in M:SS format.
    #   \return The duration of the time-out to pre-heat the bed, formatted.
    @pyqtProperty(str, notify = preheatBedRemainingTimeChanged)
    def preheatBedRemainingTime(self):
        if not self._preheat_bed_timer.isActive():
            return ""
        period = self._preheat_bed_timer.remainingTime()
        if period <= 0:
            return ""
        minutes, period = divmod(period, 60000) #60000 milliseconds in a minute.
        seconds, _ = divmod(period, 1000) #1000 milliseconds in a second.
        if minutes <= 0 and seconds <= 0:
            return ""
        return "%d:%02d" % (minutes, seconds)

    ## Time the print has been printing.
    #  Note that timeTotal - timeElapsed should give time remaining.
    @pyqtProperty(float, notify = timeElapsedChanged)
    def timeElapsed(self):
        return self._time_elapsed

    ## Total time of the print
    #  Note that timeTotal - timeElapsed should give time remaining.
    @pyqtProperty(float, notify=timeTotalChanged)
    def timeTotal(self):
        return self._time_total

    @pyqtSlot(float)
    def setTimeTotal(self, new_total):
        if self._time_total != new_total:
            self._time_total = new_total
            self.timeTotalChanged.emit()

    @pyqtSlot(float)
    def setTimeElapsed(self, time_elapsed):
        if self._time_elapsed != time_elapsed:
            self._time_elapsed = time_elapsed
            self.timeElapsedChanged.emit()

    ##  Home the head of the connected printer
    #   This function is "final" (do not re-implement)
    #   /sa _homeHead implementation function
    @pyqtSlot()
    def homeHead(self):
        self._homeHead()

    ##  Home the head of the connected printer
    #   This is an implementation function and should be overriden by children.
    def _homeHead(self):
        Logger.log("w", "_homeHead is not implemented by this output device")

    ##  Home the bed of the connected printer
    #   This function is "final" (do not re-implement)
    #   /sa _homeBed implementation function
    @pyqtSlot()
    def homeBed(self):
        self._homeBed()

    ##  Home the bed of the connected printer
    #   This is an implementation function and should be overriden by children.
    #   /sa homeBed
    def _homeBed(self):
        Logger.log("w", "_homeBed is not implemented by this output device")

    ##  Protected setter for the bed temperature of the connected printer (if any).
    #   /parameter temperature Temperature bed needs to go to (in deg celsius)
    #   /sa setTargetBedTemperature
    def _setTargetBedTemperature(self, temperature):
        Logger.log("w", "_setTargetBedTemperature is not implemented by this output device")

    ##  Pre-heats the heated bed of the printer.
    #
    #   \param temperature The temperature to heat the bed to, in degrees
    #   Celsius.
    #   \param duration How long the bed should stay warm, in seconds.
    @pyqtSlot(float, float)
    def preheatBed(self, temperature, duration):
        Logger.log("w", "preheatBed is not implemented by this output device.")

    ##  Cancels pre-heating the heated bed of the printer.
    #
    #   If the bed is not pre-heated, nothing happens.
    @pyqtSlot()
    def cancelPreheatBed(self):
        Logger.log("w", "cancelPreheatBed is not implemented by this output device.")

    ##  Protected setter for the current bed temperature.
    #   This simply sets the bed temperature, but ensures that a signal is emitted.
    #   /param temperature temperature of the bed.
    def _setBedTemperature(self, temperature):
        if self._bed_temperature != temperature:
            self._bed_temperature = temperature
            self.bedTemperatureChanged.emit()

    ##  Get the target bed temperature if connected printer (if any)
    @pyqtProperty(int, notify = targetBedTemperatureChanged)
    def targetBedTemperature(self):
        return self._target_bed_temperature

    ##  Set the (target) hotend temperature
    #   This function is "final" (do not re-implement)
    #   /param index the index of the hotend that needs to change temperature
    #   /param temperature The temperature it needs to change to (in deg celsius).
    #   /sa _setTargetHotendTemperature implementation function
    @pyqtSlot(int, int)
    def setTargetHotendTemperature(self, index, temperature):
        self._setTargetHotendTemperature(index, temperature)

        if self._target_hotend_temperatures[index] != temperature:
            self._target_hotend_temperatures[index] = temperature
            self.targetHotendTemperaturesChanged.emit()

    ##  Implementation function of setTargetHotendTemperature.
    #   /param index Index of the hotend to set the temperature of
    #   /param temperature Temperature to set the hotend to (in deg C)
    #   /sa setTargetHotendTemperature
    def _setTargetHotendTemperature(self, index, temperature):
        Logger.log("w", "_setTargetHotendTemperature is not implemented by this output device")

    @pyqtProperty("QVariantList", notify = targetHotendTemperaturesChanged)
    def targetHotendTemperatures(self):
        return self._target_hotend_temperatures

    @pyqtProperty("QVariantList", notify = hotendTemperaturesChanged)
    def hotendTemperatures(self):
        return self._hotend_temperatures

    ##  Protected setter for the current hotend temperature.
    #   This simply sets the hotend temperature, but ensures that a signal is emitted.
    #   /param index Index of the hotend
    #   /param temperature temperature of the hotend (in deg C)
    def _setHotendTemperature(self, index, temperature):
        if self._hotend_temperatures[index] != temperature:
            self._hotend_temperatures[index] = temperature
            self.hotendTemperaturesChanged.emit()

    @pyqtProperty("QVariantList", notify = materialIdChanged)
    def materialIds(self):
        return self._material_ids

    @pyqtProperty("QVariantList", notify = materialIdChanged)
    def materialNames(self):
        result = []
        for material_id in self._material_ids:
            if material_id is None:
                result.append(i18n_catalog.i18nc("@item:material", "No material loaded"))
                continue

            containers = self._container_registry.findInstanceContainers(type = "material", GUID = material_id)
            if containers:
                result.append(containers[0].getName())
            else:
                result.append(i18n_catalog.i18nc("@item:material", "Unknown material"))
        return result

    ##  List of the colours of the currently loaded materials.
    #
    #   The list is in order of extruders. If there is no material in an
    #   extruder, the colour is shown as transparent.
    #
    #   The colours are returned in hex-format AARRGGBB or RRGGBB
    #   (e.g. #800000ff for transparent blue or #00ff00 for pure green).
    @pyqtProperty("QVariantList", notify = materialIdChanged)
    def materialColors(self):
        result = []
        for material_id in self._material_ids:
            if material_id is None:
                result.append("#00000000") #No material.
                continue

            containers = self._container_registry.findInstanceContainers(type = "material", GUID = material_id)
            if containers:
                result.append(containers[0].getMetaDataEntry("color_code"))
            else:
                result.append("#00000000") #Unknown material.
        return result

    ##  Protected setter for the current material id.
    #   /param index Index of the extruder
    #   /param material_id id of the material
    def _setMaterialId(self, index, material_id):
        if material_id and material_id != "" and material_id != self._material_ids[index]:
            Logger.log("d", "Setting material id of hotend %d to %s" % (index, material_id))
            self._material_ids[index] = material_id
            self.materialIdChanged.emit(index, material_id)

    @pyqtProperty("QVariantList", notify = hotendIdChanged)
    def hotendIds(self):
        return self._hotend_ids

    ##  Protected setter for the current hotend id.
    #   /param index Index of the extruder
    #   /param hotend_id id of the hotend
    def _setHotendId(self, index, hotend_id):
        if hotend_id and hotend_id != self._hotend_ids[index]:
            Logger.log("d", "Setting hotend id of hotend %d to %s" % (index, hotend_id))
            self._hotend_ids[index] = hotend_id
            self.hotendIdChanged.emit(index, hotend_id)
        elif not hotend_id:
            Logger.log("d", "Removing hotend id of hotend %d.", index)
            self._hotend_ids[index] = None
            self.hotendIdChanged.emit(index, None)

    ##  Let the user decide if the hotends and/or material should be synced with the printer
    #   NB: the UX needs to be implemented by the plugin
    def materialHotendChangedMessage(self, callback):
        Logger.log("w", "materialHotendChangedMessage needs to be implemented, returning 'Yes'")
        callback(QMessageBox.Yes)

    ##  Attempt to establish connection
    def connect(self):
        raise NotImplementedError("connect needs to be implemented")

    ##  Attempt to close the connection
    def close(self):
        raise NotImplementedError("close needs to be implemented")

    @pyqtProperty(bool, notify = connectionStateChanged)
    def connectionState(self):
        return self._connection_state

    ##  Set the connection state of this output device.
    #   /param connection_state ConnectionState enum.
    def setConnectionState(self, connection_state):
        if self._connection_state != connection_state:
            self._connection_state = connection_state
            self.connectionStateChanged.emit(self._id)

    @pyqtProperty(str, notify = connectionTextChanged)
    def connectionText(self):
        return self._connection_text

    ##  Set a text that is shown on top of the print monitor tab
    def setConnectionText(self, connection_text):
        if self._connection_text != connection_text:
            self._connection_text = connection_text
            self.connectionTextChanged.emit()

    ##  Ensure that close gets called when object is destroyed
    def __del__(self):
        self.close()

    ##  Get the x position of the head.
    #   This function is "final" (do not re-implement)
    @pyqtProperty(float, notify = headPositionChanged)
    def headX(self):
        return self._head_x

    ##  Get the y position of the head.
    #   This function is "final" (do not re-implement)
    @pyqtProperty(float, notify = headPositionChanged)
    def headY(self):
        return self._head_y

    ##  Get the z position of the head.
    #   In some machines it's actually the bed that moves. For convenience sake we simply see it all as head movements.
    #   This function is "final" (do not re-implement)
    @pyqtProperty(float, notify = headPositionChanged)
    def headZ(self):
        return self._head_z

    ##  Update the saved position of the head
    #   This function should be called when a new position for the head is received.
    def _updateHeadPosition(self, x, y ,z):
        position_changed = False
        if self._head_x != x:
            self._head_x = x
            position_changed = True
        if self._head_y != y:
            self._head_y = y
            position_changed = True
        if self._head_z != z:
            self._head_z = z
            position_changed = True

        if position_changed:
            self.headPositionChanged.emit()

    ##  Set the position of the head.
    #   In some machines it's actually the bed that moves. For convenience sake we simply see it all as head movements.
    #   This function is "final" (do not re-implement)
    #   /param x new x location of the head.
    #   /param y new y location of the head.
    #   /param z new z location of the head.
    #   /param speed Speed by which it needs to move (in mm/minute)
    #   /sa _setHeadPosition implementation function
    @pyqtSlot("long", "long", "long")
    @pyqtSlot("long", "long", "long", "long")
    def setHeadPosition(self, x, y, z, speed = 3000):
        self._setHeadPosition(x, y , z, speed)

    ##  Set the X position of the head.
    #   This function is "final" (do not re-implement)
    #   /param x x position head needs to move to.
    #   /param speed Speed by which it needs to move (in mm/minute)
    #   /sa _setHeadx implementation function
    @pyqtSlot("long")
    @pyqtSlot("long", "long")
    def setHeadX(self, x, speed = 3000):
        self._setHeadX(x, speed)

    ##  Set the Y position of the head.
    #   This function is "final" (do not re-implement)
    #   /param y y position head needs to move to.
    #   /param speed Speed by which it needs to move (in mm/minute)
    #   /sa _setHeadY implementation function
    @pyqtSlot("long")
    @pyqtSlot("long", "long")
    def setHeadY(self, y, speed = 3000):
        self._setHeadY(y, speed)

    ##  Set the Z position of the head.
    #   In some machines it's actually the bed that moves. For convenience sake we simply see it all as head movements.
    #   This function is "final" (do not re-implement)
    #   /param z z position head needs to move to.
    #   /param speed Speed by which it needs to move (in mm/minute)
    #   /sa _setHeadZ implementation function
    @pyqtSlot("long")
    @pyqtSlot("long", "long")
    def setHeadZ(self, z, speed = 3000):
        self._setHeadZ(z, speed)

    ##  Move the head of the printer.
    #   Note that this is a relative move. If you want to move the head to a specific position you can use
    #   setHeadPosition
    #   This function is "final" (do not re-implement)
    #   /param x distance in x to move
    #   /param y distance in y to move
    #   /param z distance in z to move
    #   /param speed Speed by which it needs to move (in mm/minute)
    #   /sa _moveHead implementation function
    @pyqtSlot("long", "long", "long")
    @pyqtSlot("long", "long", "long", "long")
    def moveHead(self, x = 0, y = 0, z = 0, speed = 3000):
        self._moveHead(x, y, z, speed)

    ##  Implementation function of moveHead.
    #   /param x distance in x to move
    #   /param y distance in y to move
    #   /param z distance in z to move
    #   /param speed Speed by which it needs to move (in mm/minute)
    #   /sa moveHead
    def _moveHead(self, x, y, z, speed):
        Logger.log("w", "_moveHead is not implemented by this output device")

    ##  Implementation function of setHeadPosition.
    #   /param x new x location of the head.
    #   /param y new y location of the head.
    #   /param z new z location of the head.
    #   /param speed Speed by which it needs to move (in mm/minute)
    #   /sa setHeadPosition
    def _setHeadPosition(self, x, y, z, speed):
        Logger.log("w", "_setHeadPosition is not implemented by this output device")

    ##  Implementation function of setHeadX.
    #   /param x new x location of the head.
    #   /param speed Speed by which it needs to move (in mm/minute)
    #   /sa setHeadX
    def _setHeadX(self, x, speed):
        Logger.log("w", "_setHeadX is not implemented by this output device")

    ##  Implementation function of setHeadY.
    #   /param y new y location of the head.
    #   /param speed Speed by which it needs to move (in mm/minute)
    #   /sa _setHeadY
    def _setHeadY(self, y, speed):
        Logger.log("w", "_setHeadY is not implemented by this output device")

    ##  Implementation function of setHeadZ.
    #   /param z new z location of the head.
    #   /param speed Speed by which it needs to move (in mm/minute)
    #   /sa _setHeadZ
    def _setHeadZ(self, z, speed):
        Logger.log("w", "_setHeadZ is not implemented by this output device")

    ##  Get the progress of any currently active process.
    #   This function is "final" (do not re-implement)
    #   /sa _getProgress
    #   /returns float progress of the process. -1 indicates that there is no process.
    @pyqtProperty(float, notify = progressChanged)
    def progress(self):
        return self._progress

    ##  Set the progress of any currently active process
    #   /param progress Progress of the process.
    def setProgress(self, progress):
        if self._progress != progress:
            self._progress = progress
            self.progressChanged.emit()


##  The current processing state of the backend.
class ConnectionState(IntEnum):
    closed = 0
    connecting = 1
    connected = 2
    busy = 3
    error = 4