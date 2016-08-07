from cura.MachineAction import MachineAction
from cura.PrinterOutputDevice import PrinterOutputDevice
from UM.Application import Application
from PyQt5.QtCore import pyqtSlot, pyqtSignal, pyqtProperty

from UM.Logger import Logger
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class UMOCheckupMachineAction(MachineAction):
    def __init__(self):
        super().__init__("UMOCheckup", catalog.i18nc("@action", "Checkup"))
        self._qml_url = "UMOCheckupMachineAction.qml"
        self._hotend_target_temp = 180
        self._bed_target_temp = 60
        self._output_device = None
        self._bed_test_completed = False
        self._hotend_test_completed = False

        # Endstop tests
        self._x_min_endstop_test_completed = False
        self._y_min_endstop_test_completed = False
        self._z_min_endstop_test_completed = False

        self._check_started = False

        Application.getInstance().getOutputDeviceManager().outputDevicesChanged.connect(self._onOutputDevicesChanged)


    onBedTestCompleted = pyqtSignal()
    onHotendTestCompleted = pyqtSignal()

    onXMinEndstopTestCompleted = pyqtSignal()
    onYMinEndstopTestCompleted = pyqtSignal()
    onZMinEndstopTestCompleted = pyqtSignal()

    bedTemperatureChanged = pyqtSignal()
    hotendTemperatureChanged = pyqtSignal()

    def _onOutputDevicesChanged(self):
        # Check if this action was started, but no output device was found the first time.
        # If so, re-try now that an output device has been added/removed.
        if self._output_device is None and self._check_started:
            self.startCheck()

    def _getPrinterOutputDevices(self):
        return [printer_output_device for printer_output_device in
                Application.getInstance().getOutputDeviceManager().getOutputDevices() if
                isinstance(printer_output_device, PrinterOutputDevice)]

    def _reset(self):
        if self._output_device:
            self._output_device.bedTemperatureChanged.disconnect(self.bedTemperatureChanged)
            self._output_device.hotendTemperaturesChanged.disconnect(self.hotendTemperatureChanged)
            self._output_device.bedTemperatureChanged.disconnect(self._onBedTemperatureChanged)
            self._output_device.hotendTemperaturesChanged.disconnect(self._onHotendTemperatureChanged)
            self._output_device.endstopStateChanged.disconnect(self._onEndstopStateChanged)
            try:
                self._output_device.stopPollEndstop()
            except AttributeError as e:  # Connection is probably not a USB connection. Something went pretty wrong if this happens.
                Logger.log("e", "An exception occurred while stopping end stop polling: %s" % str(e))

        self._output_device = None

        self._check_started = False
        self.checkStartedChanged.emit()

        # Ensure everything is reset (and right signals are emitted again)
        self._bed_test_completed = False
        self.onBedTestCompleted.emit()
        self._hotend_test_completed = False
        self.onHotendTestCompleted.emit()

        self._x_min_endstop_test_completed = False
        self.onXMinEndstopTestCompleted.emit()
        self._y_min_endstop_test_completed = False
        self.onYMinEndstopTestCompleted.emit()
        self._z_min_endstop_test_completed = False
        self.onZMinEndstopTestCompleted.emit()

        self.heatedBedChanged.emit()

    @pyqtProperty(bool, notify = onBedTestCompleted)
    def bedTestCompleted(self):
        return self._bed_test_completed

    @pyqtProperty(bool, notify = onHotendTestCompleted)
    def hotendTestCompleted(self):
        return self._hotend_test_completed

    @pyqtProperty(bool, notify = onXMinEndstopTestCompleted)
    def xMinEndstopTestCompleted(self):
        return self._x_min_endstop_test_completed

    @pyqtProperty(bool, notify=onYMinEndstopTestCompleted)
    def yMinEndstopTestCompleted(self):
        return self._y_min_endstop_test_completed

    @pyqtProperty(bool, notify=onZMinEndstopTestCompleted)
    def zMinEndstopTestCompleted(self):
        return self._z_min_endstop_test_completed

    @pyqtProperty(float, notify = bedTemperatureChanged)
    def bedTemperature(self):
        if not self._output_device:
            return 0
        return self._output_device.bedTemperature

    @pyqtProperty(float, notify=hotendTemperatureChanged)
    def hotendTemperature(self):
        if not self._output_device:
            return 0
        return self._output_device.hotendTemperatures[0]

    def _onHotendTemperatureChanged(self):
        if not self._output_device:
            return
        if not self._hotend_test_completed:
            if self._output_device.hotendTemperatures[0] + 10 > self._hotend_target_temp and self._output_device.hotendTemperatures[0] - 10 < self._hotend_target_temp:
                self._hotend_test_completed = True
                self.onHotendTestCompleted.emit()

    def _onBedTemperatureChanged(self):
        if not self._output_device:
            return
        if not self._bed_test_completed:
            if self._output_device.bedTemperature + 5 > self._bed_target_temp and self._output_device.bedTemperature - 5 < self._bed_target_temp:
                self._bed_test_completed = True
                self.onBedTestCompleted.emit()

    def _onEndstopStateChanged(self, switch_type, state):
        if state:
            if switch_type == "x_min":
                self._x_min_endstop_test_completed = True
                self.onXMinEndstopTestCompleted.emit()
            elif switch_type == "y_min":
                self._y_min_endstop_test_completed = True
                self.onYMinEndstopTestCompleted.emit()
            elif switch_type == "z_min":
                self._z_min_endstop_test_completed = True
                self.onZMinEndstopTestCompleted.emit()

    checkStartedChanged = pyqtSignal()

    @pyqtProperty(bool, notify = checkStartedChanged)
    def checkStarted(self):
        return self._check_started

    @pyqtSlot()
    def startCheck(self):
        self._check_started = True
        self.checkStartedChanged.emit()
        output_devices = self._getPrinterOutputDevices()
        if output_devices:
            self._output_device = output_devices[0]
            try:
                self._output_device.sendCommand("M18") # Turn off all motors so the user can move the axes
                self._output_device.startPollEndstop()
                self._output_device.bedTemperatureChanged.connect(self.bedTemperatureChanged)
                self._output_device.hotendTemperaturesChanged.connect(self.hotendTemperatureChanged)
                self._output_device.bedTemperatureChanged.connect(self._onBedTemperatureChanged)
                self._output_device.hotendTemperaturesChanged.connect(self._onHotendTemperatureChanged)
                self._output_device.endstopStateChanged.connect(self._onEndstopStateChanged)
            except AttributeError as e:  # Connection is probably not a USB connection. Something went pretty wrong if this happens.
                Logger.log("e", "An exception occurred while starting end stop polling: %s" % str(e))

    @pyqtSlot()
    def cooldownHotend(self):
        if self._output_device is not None:
            self._output_device.setTargetHotendTemperature(0, 0)

    @pyqtSlot()
    def cooldownBed(self):
        if self._output_device is not None:
            self._output_device.setTargetBedTemperature(0)

    @pyqtSlot()
    def heatupHotend(self):
        if self._output_device is not None:
            self._output_device.setTargetHotendTemperature(0, self._hotend_target_temp)

    @pyqtSlot()
    def heatupBed(self):
        if self._output_device is not None:
            self._output_device.setTargetBedTemperature(self._bed_target_temp)

    heatedBedChanged = pyqtSignal()

    @pyqtProperty(bool, notify = heatedBedChanged)
    def hasHeatedBed(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        return global_container_stack.getProperty("machine_heated_bed", "value")