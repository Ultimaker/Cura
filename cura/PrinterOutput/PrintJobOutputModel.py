# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtSignal, pyqtProperty, QObject, QVariant
MYPY = False
if MYPY:
    from cura.PrinterOutput.PrinterOutputController import PrinterOutputController


class PrintJobOutputModel(QObject):
    stateChanged = pyqtSignal()
    timeTotalChanged = pyqtSignal()
    timeElapsedChanged = pyqtSignal()

    def __init__(self, output_controller: "PrinterOutputController", parent=None):
        super().__init__(parent)
        self._output_controller = output_controller
        self._state = ""
        self._time_total = 0
        self._time_elapsed = 0

    @pyqtProperty(int, notify = timeTotalChanged)
    def timeTotal(self):
        return self._time_total

    @pyqtProperty(int, notify = timeElapsedChanged)
    def timeElapsed(self):
        return self._time_elapsed

    @pyqtProperty(str, notify=stateChanged)
    def state(self):
        return self._state

    def updateTimeTotal(self, new_time_total):
        if self._time_total != new_time_total:
            self._time_total = new_time_total
            self.timeTotalChanged.emit()

    def updateTimeElapsed(self, new_time_elapsed):
        if self._time_elapsed != new_time_elapsed:
            self._time_elapsed = new_time_elapsed
            self.timeElapsedChanged.emit()

    def updateState(self, new_state):
        if self._state != new_state:
            self._state = new_state
            self.stateChanged.emit()

    def setState(self, state):
        self._output_controller.setJobState(self, state)