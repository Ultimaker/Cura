from UM.i18n import i18nCatalog
from UM.OutputDevice.OutputDevice import OutputDevice
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtWidgets import QMessageBox

from enum import IntEnum  # For the connection state tracking.
from UM.Logger import Logger
from UM.Application import Application
from UM.Signal import signalemitter

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

    def requestWrite(self, node, file_name = None, filter_by_machine = False):
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

    @pyqtProperty(str, notify = jobStateChanged)
    def jobState(self):
        return self._job_state

    def _updateJobState(self, job_state):
        if self._job_state != job_state:
            self._job_state = job_state
            self.jobStateChanged.emit()

    @pyqtSlot(str)
    def setJobState(self, job_state):
        self._setJobState(job_state)

    def _setJobState(self, job_state):
        Logger.log("w", "_setJobState is not implemented by this output device")

    @pyqtProperty(str, notify = jobNameChanged)
    def jobName(self):
        return self._job_name

    def setJobName(self, name):
        if self._job_name != name:
            self._job_name = name
            self.jobNameChanged.emit()

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
        self._target_bed_temperature = temperature
        self.targetBedTemperatureChanged.emit()

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

    ##  Protected setter for the current bed temperature.
    #   This simply sets the bed temperature, but ensures that a signal is emitted.
    #   /param temperature temperature of the bed.
    def _setBedTemperature(self, temperature):
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
        self._hotend_temperatures[index] = temperature
        self.hotendTemperaturesChanged.emit()

    @pyqtProperty("QVariantList", notify = materialIdChanged)
    def materialIds(self):
        return self._material_ids

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
        if hotend_id and hotend_id != "" and hotend_id != self._hotend_ids[index]:
            Logger.log("d", "Setting hotend id of hotend %d to %s" % (index, hotend_id))
            self._hotend_ids[index] = hotend_id
            self.hotendIdChanged.emit(index, hotend_id)

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
        self._setHeadY(z, speed)

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