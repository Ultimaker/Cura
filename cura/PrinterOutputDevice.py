from UM.OutputDevice.OutputDevice import OutputDevice
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot


##  Printer output device adds extra interface options on top of output device.
#
#   The assumption is made the printer is a FDM printer.
#
#   Note that a number of settings are marked as "final". This is because decorators
#   are not inherited by children. To fix this we use the private counter part of those
#   functions to actually have the implementation.
#
#   For all other uses it should be used in the same way as a "regular" OutputDevice.
class PrinterOutputDevice(OutputDevice):
    def __init__(self, device_id):
        super().__init__(device_id)
        self._target_bed_temperature = 0
        self._target_hotend_temperatures = {}
        self._head_x = 0
        self._head_y = 0
        self._head_z = 0

    def requestWrite(self, node, file_name = None, filter_by_machine = False):
        raise NotImplementedError("requestWrite needs to be implemented")

    bedTemperatureChanged = pyqtSignal()
    targetBedTemperatureChanged = pyqtSignal()

    progressChanged = pyqtSignal()

    hotendTemperaturesChanged = pyqtSignal()
    targetHotendTemperaturesChanged = pyqtSignal()

    headPositionChanged = pyqtSignal()

    ##  Get the bed temperature of the bed (if any)
    #   This function is "final" (do not re-implement)
    #   /sa _getBedTemperature
    @pyqtProperty(float, notify = bedTemperatureChanged)
    def bedTemperature(self):
        return self._getBedTemperature()

    def _getBedTemperature(self):
        raise NotImplementedError("_getBedTemperature needs to be implemented")

    ##  Get the temperature of a hot end as defined by index.
    #   /parameter index Index of the hotend to get a temperature from.
    def getHotendTemperature(self, index):
        raise NotImplementedError("getHotendTemperature needs to be implemented")

    ##  Set the (target) bed temperature
    #   This function is "final" (do not re-implement)
    #   /sa _setBedTemperature
    @pyqtSlot(int)
    def setBedTemperature(self, temperature):
        self._setBedTemperature(temperature)
        self._target_bed_temperature = temperature
        self.targetBedTemperatureChanged.emit()

    ##  Set the bed temperature of the connected printer.
    def _setBedTemperature(self, temperature):
        raise NotImplementedError("_setBedTemperature needs to be implemented")

    def setHotendTemperature(self, index, temperature):
        self._setTargetHotendTemperature(index, temperature)
        self._target_hotend_temperatures[index] = temperature
        self.targetHotendTemperaturesChanged.emit()

    def _setTargetHotendTemperature(self, index, temperature):
        raise NotImplementedError("_setTargetHotendTemperature needs to be implemented")

    @pyqtProperty("QVariantMap", notify = targetHotendTemperaturesChanged)
    def targetHotendTemperatures(self):
        return self._getTargetHotendTemperatures()

    def _getTargetHotendTemperatures(self):
        raise NotImplementedError("_getTargetHotendTemperatures needs to be implemented")

    @pyqtProperty("QVariantMap", notify = hotendTemperaturesChanged)
    def hotendTemperatures(self):
        return self._getHotendTemperatures()

    def _getHotendTemperatures(self):
        raise NotImplementedError("_getHotendTemperatures needs to be implemented")

    ##  Attempt to establish connection
    def connect(self):
        pass

    def close(self):
        pass

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
    @pyqtSlot("long", "long", "long")
    @pyqtSlot("long", "long", "long", "long")
    def setHeadPosition(self, x, y, z, speed = 3000):
        self._setHeadPosition(x, y , z, speed)

    def _setHeadPosition(self, x, y, z, speed):
        pass

    def _setHeadX(self, x, speed):
        pass

    def _setHeadY(self, y, speed):
        pass

    def _setHeadZ(self, z, speed):
        pass

    ##  Get the progress of any currently active process.
    #   This function is "final" (do not re-implement)
    #   /sa _getProgress
    #   /returns float progess of the process. -1 indicates that there is no process.
    @pyqtProperty(float, notify = progressChanged)
    def progress(self):
        try:
            return float(self._getProgress())
        except ValueError:
            return -1

    def _getProgress(self):
        raise NotImplementedError("_getProgress needs to be implemented")