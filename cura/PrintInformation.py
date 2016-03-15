# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtSignal, pyqtProperty

from UM.Application import Application
from UM.Qt.Duration import Duration

import math

##  A class for processing and calculating minimum, current and maximum print time.
#
#   This class contains all the logic relating to calculation and slicing for the
#   time/quality slider concept. It is a rather tricky combination of event handling
#   and state management. The logic behind this is as follows:
#
#   - A scene change or setting change event happens.
#        We track what the source was of the change, either a scene change, a setting change, an active machine change or something else.
#   - This triggers a new slice with the current settings - this is the "current settings pass".
#   - When the slice is done, we update the current print time and material amount.
#   - If the source of the slice was not a Setting change, we start the second slice pass, the "low quality settings pass". Otherwise we stop here.
#   - When that is done, we update the minimum print time and start the final slice pass, the "high quality settings pass".
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

        self._current_print_time = Duration(None, self)

        self._material_amount = -1

        self._backend = Application.getInstance().getBackend()
        if self._backend:
            self._backend.printDurationMessage.connect(self._onPrintDurationMessage)

    currentPrintTimeChanged = pyqtSignal()
    
    @pyqtProperty(Duration, notify = currentPrintTimeChanged)
    def currentPrintTime(self):
        return self._current_print_time

    materialAmountChanged = pyqtSignal()
    
    @pyqtProperty(float, notify = materialAmountChanged)
    def materialAmount(self):
        return self._material_amount

    def _onPrintDurationMessage(self, time, amount):
        #if self._slice_pass == self.SlicePass.CurrentSettings:
        self._current_print_time.setDuration(time)
        self.currentPrintTimeChanged.emit()

        # Material amount is sent as an amount of mm^3, so calculate length from that
        r =  Application.getInstance().getMachineManager().getWorkingProfile().getSettingValue("material_diameter") / 2
        self._material_amount = round((amount / (math.pi * r ** 2)) / 1000, 2)
        self.materialAmountChanged.emit()
