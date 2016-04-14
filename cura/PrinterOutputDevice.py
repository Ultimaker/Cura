from UM.OutputDevice.OutputDevice import OutputDevice
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject
from enum import IntEnum  # For the connection state tracking.
from UM.Logger import Logger


##  Printer output device adds extra interface options on top of output device.
#
#   The assumption is made the printer is a FDM printer.
#
#   Note that a number of settings are marked as "final". This is because decorators
#   are not inherited by children. To fix this we use the private counter part of those
#   functions to actually have the implementation.
#
#   For all other uses it should be used in the same way as a "regular" OutputDevice.
class PrinterOutputDevice(OutputDevice, QObject):
    def __init__(self, device_id, parent = None):
        QObject.__init__(self, parent)
        OutputDevice.__init__(self, device_id)

        self._target_bed_temperature = 0
        self._bed_temperature = 0
        self._num_extruders = 1
        self._hotend_temperatures = [0] * self._num_extruders
        self._target_hotend_temperatures = [0] * self._num_extruders
        self._progress = 0
        self._head_x = 0
        self._head_y = 0
        self._head_z = 0
        self._connection_state = ConnectionState.CLOSED

    def requestWrite(self, node, file_name = None, filter_by_machine = False):
        raise NotImplementedError("requestWrite needs to be implemented")

    # Signals:
    bedTemperatureChanged = pyqtSignal()
    targetBedTemperatureChanged = pyqtSignal()

    progressChanged = pyqtSignal()

    hotendTemperaturesChanged = pyqtSignal()
    targetHotendTemperaturesChanged = pyqtSignal()

    headPositionChanged = pyqtSignal()

    connectionStateChanged = pyqtSignal(str)

    ##  Get the bed temperature of the bed (if any)
    #   This function is "final" (do not re-implement)
    #   /sa _getBedTemperature
    @pyqtProperty(float, notify = bedTemperatureChanged)
    def bedTemperature(self):
        return self._bed_temperature

    ##  Set the (target) bed temperature
    #   This function is "final" (do not re-implement)
    #   /sa _setTargetBedTemperature
    @pyqtSlot(int)
    def setTargetBedTemperature(self, temperature):
        self._setTargetBedTemperature(temperature)
        self._target_bed_temperature = temperature
        self.targetBedTemperatureChanged.emit()

    ##  Home the head of the connected printer
    #   This function is "final" (do not re-implement)
    @pyqtSlot()
    def homeHead(self):
        self._homeHead()

    ##  Home the head of the connected printer
    #   This is an implementation function and should be overriden by children.
    def _homeHead(self):
        Logger.log("w", "_homeHead is not implemented by this output device")

    ##  Home the bed of the connected printer
    #   This function is "final" (do not re-implement)
    @pyqtSlot()
    def homeBed(self):
        self._homeBed()

    ##  Home the bed of the connected printer
    #   This is an implementation function and should be overriden by children..
    def _homeBed(self):
        Logger.log("w", "_homeBed is not implemented by this output device")

    ##  Set the bed temperature of the connected printer (if any).
    #   /parameter temperature Temperature bed needs to go to (in deg celsius)
    def _setTargetBedTemperature(self, temperature):
        Logger.log("w", "_setTargetBedTemperature is not implemented by this output device")

    def _setBedTemperature(self, temperature):
        self._bed_temperature = temperature
        self.bedTemperatureChanged.emit()

    ##  Get the bed temperature if connected printer (if any)
    @pyqtProperty(int, notify = bedTemperatureChanged)
    def bedTemperature(self):
        return self._bed_temperature

    ##  Get the target bed temperature if connected printer (if any)
    @pyqtProperty(int, notify = targetBedTemperatureChanged)
    def targetBedTemperature(self):
        return self._target_bed_temperature

    ##  Set the (target) hotend temperature
    #   This function is "final" (do not re-implement)
    #   /param index the index of the hotend that needs to change temperature
    #   /param temperature The temperature it needs to change to (in deg celsius).
    #   /sa _setTargetHotendTemperature
    @pyqtSlot(int, int)
    def setTargetHotendTemperature(self, index, temperature):
        self._setTargetHotendTemperature(index, temperature)
        self._target_hotend_temperatures[index] = temperature
        self.targetHotendTemperaturesChanged.emit()

    def _setTargetHotendTemperature(self, index, temperature):
        Logger.log("w", "_setTargetHotendTemperature is not implemented by this output device")

    @pyqtProperty("QVariantList", notify = targetHotendTemperaturesChanged)
    def targetHotendTemperatures(self):
        return self._target_hotend_temperatures

    @pyqtProperty("QVariantList", notify = hotendTemperaturesChanged)
    def hotendTemperatures(self):
        return self._hotend_temperatures

    def _setHotendTemperature(self, index, temperature):
        self._hotend_temperatures[index] = temperature
        self.hotendTemperaturesChanged.emit()

    ##  Attempt to establish connection
    def connect(self):
        pass

    def close(self):
        pass

    @pyqtProperty(bool, notify = connectionStateChanged)
    def connectionState(self):
        return self._connection_state

    def setConnectionState(self, connection_state):
        self._connection_state = connection_state
        self.connectionStateChanged.emit(self._id)

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

    ##  Set the position of the head.
    #   In some machines it's actually the bed that moves. For convenience sake we simply see it all as head movements.
    #   This function is "final" (do not re-implement)
    #   /param speed Speed by which it needs to move (in mm/minute)
    @pyqtSlot("long", "long", "long")
    @pyqtSlot("long", "long", "long", "long")
    def setHeadPosition(self, x, y, z, speed = 3000):
        self._setHeadPosition(x, y , z, speed)

    ##  Set the X position of the head.
    #   This function is "final" (do not re-implement)
    #   /param x x position head needs to move to.
    #   /param speed Speed by which it needs to move (in mm/minute)
    @pyqtSlot("long")
    @pyqtSlot("long", "long")
    def setHeadX(self, x, speed = 3000):
        self._setHeadX(x, speed)

    ##  Set the Y position of the head.
    #   This function is "final" (do not re-implement)
    #   /param y y position head needs to move to.
    #   /param speed Speed by which it needs to move (in mm/minute)
    @pyqtSlot("long")
    @pyqtSlot("long", "long")
    def setHeadY(self, y, speed = 3000):
        self._setHeadY(y, speed)

    ##  Set the Z position of the head.
    #   In some machines it's actually the bed that moves. For convenience sake we simply see it all as head movements.
    #   This function is "final" (do not re-implement)
    #   /param z z position head needs to move to.
    #   /param speed Speed by which it needs to move (in mm/minute)
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
    @pyqtSlot("long", "long", "long")
    @pyqtSlot("long", "long", "long", "long")
    def moveHead(self, x = 0, y = 0, z = 0, speed = 3000):
        self._moveHead(x, y, z, speed)

    def _moveHead(self, x, y, z, speed):
        Logger.log("w", "_moveHead is not implemented by this output device")

    def _setHeadPosition(self, x, y, z, speed):
        Logger.log("w", "_setHeadPosition is not implemented by this output device")

    def _setHeadX(self, x, speed):
        Logger.log("w", "_setHeadX is not implemented by this output device")

    def _setHeadY(self, y, speed):
        Logger.log("w", "_setHeadY is not implemented by this output device")

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
    def setProgress(self, progress):
        self._progress = progress
        self.progressChanged.emit()

##  The current processing state of the backend.
class ConnectionState(IntEnum):
    CLOSED = 0
    CONNECTING = 1
    CONNECTED = 2