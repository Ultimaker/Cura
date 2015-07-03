# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QObject, QDateTime, QTimer, pyqtSignal, pyqtSlot, pyqtProperty

from UM.Application import Application
from UM.Settings.MachineSettings import MachineSettings
from UM.Resources import Resources
from UM.Scene.SceneNode import SceneNode
from UM.Qt.Duration import Duration

##  A class for processing and calculating minimum, currrent and maximum print time.
#
#   This class contains all the logic relating to calculation and slicing for the
#   time/quality slider concept. It is a rather tricky combination of event handling
#   and state management. The logic behind this is as follows:
#
#   - A scene change or settting change event happens.
#        We track what the source was of the change, either a scene change, a setting change, an active machine change or something else.
#   - This triggers a new slice with the current settings - this is the "current settings pass".
#   - When the slice is done, we update the current print time and material amount.
#   - If the source of the slice was not a Setting change, we start the second slice pass, the "low quality settings pass". Otherwise we stop here.
#   - When that is done, we update the minimum print time and start the final slcice pass, the "high quality settings pass".
#   - When the high quality pass is done, we update the maximum print time.
#
class PrintInformation(QObject):
    class SlicePass:
        CurrentSettings = 1
        LowQualitySettings = 2
        HighQualitySettings = 3

    class SliceReason:
        SceneChanged = 1
        SettingChanged = 2
        ActiveMachineChanged = 3
        Other = 4

    def __init__(self, parent = None):
        super().__init__(parent)

        self._enabled = False

        self._minimum_print_time = Duration(None, self)
        self._current_print_time = Duration(None, self)
        self._maximum_print_time = Duration(None, self)

        self._material_amount = -1

        self._time_quality_value = 50
        self._time_quality_changed_timer = QTimer()
        self._time_quality_changed_timer.setInterval(500)
        self._time_quality_changed_timer.setSingleShot(True)
        self._time_quality_changed_timer.timeout.connect(self._updateTimeQualitySettings)

        self._interpolation_settings = {
            "layer_height": { "minimum": "low", "maximum": "high", "curve": "linear", "precision": 2 },
            "fill_sparse_density": { "minimum": "low", "maximum": "high", "curve": "linear", "precision": 0 }
        }

        self._low_quality_settings = None
        self._current_settings = None
        self._high_quality_settings = None

        self._slice_pass = None
        self._slice_reason = None

        Application.getInstance().activeMachineChanged.connect(self._onActiveMachineChanged)
        self._onActiveMachineChanged()

        Application.getInstance().getController().getScene().sceneChanged.connect(self._onSceneChanged)

        self._backend = Application.getInstance().getBackend()
        if self._backend:
            self._backend.printDurationMessage.connect(self._onPrintDurationMessage)
            self._backend.slicingStarted.connect(self._onSlicingStarted)
            self._backend.slicingCancelled.connect(self._onSlicingCancelled)

    minimumPrintTimeChanged = pyqtSignal()
    
    @pyqtProperty(Duration, notify = minimumPrintTimeChanged)
    def minimumPrintTime(self):
        return self._minimum_print_time

    currentPrintTimeChanged = pyqtSignal()
    
    @pyqtProperty(Duration, notify = currentPrintTimeChanged)
    def currentPrintTime(self):
        return self._current_print_time

    maximumPrintTimeChanged = pyqtSignal()
    
    @pyqtProperty(Duration, notify = maximumPrintTimeChanged)
    def maximumPrintTime(self):
        return self._maximum_print_time

    materialAmountChanged = pyqtSignal()
    
    @pyqtProperty(float, notify = materialAmountChanged)
    def materialAmount(self):
        return self._material_amount

    timeQualityValueChanged = pyqtSignal()
    
    @pyqtProperty(int, notify = timeQualityValueChanged)
    def timeQualityValue(self):
        return self._time_quality_value

    def setEnabled(self, enabled):
        if enabled != self._enabled:
            self._enabled = enabled

            if self._enabled:
                self._updateTimeQualitySettings()
                self._onSlicingStarted()

            self.enabledChanged.emit()

    enabledChanged = pyqtSignal()
    @pyqtProperty(bool, fset = setEnabled, notify = enabledChanged)
    def enabled(self):
        return self._enabled

    @pyqtSlot(int)
    def setTimeQualityValue(self, value):
        if value != self._time_quality_value:
            self._time_quality_value = value
            self.timeQualityValueChanged.emit()

            self._time_quality_changed_timer.start()

    def _onSlicingStarted(self):
        if self._slice_pass is None:
            self._slice_pass = self.SlicePass.CurrentSettings

        if self._slice_reason is None:
            self._slice_reason = self.SliceReason.Other

        if self._slice_pass == self.SlicePass.CurrentSettings and self._slice_reason != self.SliceReason.SettingChanged:
            self._minimum_print_time.setDuration(-1)
            self.minimumPrintTimeChanged.emit()
            self._maximum_print_time.setDuration(-1)
            self.maximumPrintTimeChanged.emit()

    def _onPrintDurationMessage(self, time, amount):
        if self._slice_pass == self.SlicePass.CurrentSettings:
            self._current_print_time.setDuration(time)
            self.currentPrintTimeChanged.emit()

            self._material_amount = round(amount / 10) / 100
            self.materialAmountChanged.emit()

            if not self._enabled:
                return

            if self._slice_reason != self.SliceReason.SettingChanged or not self._minimum_print_time.valid or not self._maximum_print_time.valid:
                self._slice_pass = self.SlicePass.LowQualitySettings
                self._backend.slice(settings = self._low_quality_settings, save_gcode = False, save_polygons = False, force_restart = False, report_progress = False)
            else:
                self._slice_pass = None
                self._slice_reason = None
        elif self._slice_pass == self.SlicePass.LowQualitySettings:
            self._minimum_print_time.setDuration(time)
            self.minimumPrintTimeChanged.emit()

            self._slice_pass = self.SlicePass.HighQualitySettings
            self._backend.slice(settings = self._high_quality_settings, save_gcode = False, save_polygons = False, force_restart = False, report_progress = False)
        elif self._slice_pass == self.SlicePass.HighQualitySettings:
            self._maximum_print_time.setDuration(time)
            self.maximumPrintTimeChanged.emit()

            self._slice_pass = None
            self._slice_reason = None

    def _onActiveMachineChanged(self):
        if self._current_settings:
            self._current_settings.settingChanged.disconnect(self._onSettingChanged)

        self._current_settings = Application.getInstance().getActiveMachine()

        if self._current_settings:
            self._current_settings.settingChanged.connect(self._onSettingChanged)
            self._low_quality_settings = None
            self._high_quality_settings = None
            self._updateTimeQualitySettings()

            self._slice_reason = self.SliceReason.ActiveMachineChanged

    def _updateTimeQualitySettings(self):
        if not self._current_settings or not self._enabled:
            return

        if not self._low_quality_settings:
            self._low_quality_settings = MachineSettings()
            self._low_quality_settings.loadSettingsFromFile(Resources.getPath(Resources.SettingsLocation, self._current_settings.getTypeID() + ".json"))
            self._low_quality_settings.loadValuesFromFile(Resources.getPath(Resources.SettingsLocation, "profiles", "low_quality.conf"))

        if not self._high_quality_settings:
            self._high_quality_settings = MachineSettings()
            self._high_quality_settings.loadSettingsFromFile(Resources.getPath(Resources.SettingsLocation, self._current_settings.getTypeID() + ".json"))
            self._high_quality_settings.loadValuesFromFile(Resources.getPath(Resources.SettingsLocation, "profiles", "high_quality.conf"))

        for key, options in self._interpolation_settings.items():
            minimum_value = None
            if options["minimum"] == "low":
                minimum_value = self._low_quality_settings.getSettingValueByKey(key)
            elif options["minimum"] == "high":
                minimum_value = self._high_quality_settings.getSettingValueByKey(key)
            else:
                continue

            maximum_value = None
            if options["maximum"] == "low":
                maximum_value = self._low_quality_settings.getSettingValueByKey(key)
            elif options["maximum"] == "high":
                maximum_value = self._high_quality_settings.getSettingValueByKey(key)
            else:
                continue

            setting_value = round(minimum_value + (maximum_value - minimum_value) * (self._time_quality_value / 100), options["precision"])
            self._current_settings.setSettingValueByKey(key, setting_value)

    def _onSceneChanged(self, source):
        self._slice_reason = self.SliceReason.SceneChanged

    def _onSettingChanged(self, source):
        self._slice_reason = self.SliceReason.SettingChanged

    def _onSlicingCancelled(self):
        self._slice_pass = None
