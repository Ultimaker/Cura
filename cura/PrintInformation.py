# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot

from UM.Application import Application
from UM.Qt.Duration import Duration
from UM.Preferences import Preferences

import math
import os.path
import unicodedata

##  A class for processing and calculating minimum, current and maximum print time as well as managing the job name
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
#   This class also mangles the current machine name and the filename of the first loaded mesh into a job name.
#   This job name is requested by the JobSpecs qml file.
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

        self._job_name = ""
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalStackChanged)
        Application.getInstance().fileLoaded.connect(self.setJobName)

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
        r = Application.getInstance().getGlobalContainerStack().getProperty("material_diameter", "value") / 2
        self._material_amount = round((amount / (math.pi * r ** 2)) / 1000, 2)
        self.materialAmountChanged.emit()

    @pyqtSlot(str)
    def setJobName(self, name):
        # when a file is opened using the terminal; the filename comes from _onFileLoaded and still contains its
        # extension. This cuts the extension off if necessary.
        name = os.path.splitext(name)[0]
        if self._job_name != name:
            self._job_name = name
            self.jobNameChanged.emit()

    jobNameChanged = pyqtSignal()

    @pyqtProperty(str, notify = jobNameChanged)
    def jobName(self):
        return self._job_name

    @pyqtSlot(str, result = str)
    def createJobName(self, base_name):
        base_name = self._stripAccents(base_name)
        if Preferences.getInstance().getValue("cura/jobname_prefix"):
            return self._abbr_machine + "_" + base_name
        else:
            return base_name

    def _onGlobalStackChanged(self):
        global_stack_name = Application.getInstance().getGlobalContainerStack().getName()
        split_name = global_stack_name.split(" ")
        abbr_machine = ""
        for word in split_name:
            if(word.lower() == "ultimaker"):
                abbr_machine += "UM"
            elif word.isdigit():
                abbr_machine += word
            else:
                abbr_machine += self._stripAccents(word.strip("()[]{}#").upper())[0]

        self._abbr_machine = abbr_machine

    def _stripAccents(self, str):
       return ''.join(char for char in unicodedata.normalize('NFD', str) if unicodedata.category(char) != 'Mn')