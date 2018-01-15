# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtSignal, pyqtProperty, QObject, pyqtSlot
from typing import Optional
MYPY = False
if MYPY:
    from cura.PrinterOutput.PrinterOutputController import PrinterOutputController
    from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel


class PrintJobOutputModel(QObject):
    stateChanged = pyqtSignal()
    timeTotalChanged = pyqtSignal()
    timeElapsedChanged = pyqtSignal()
    nameChanged = pyqtSignal()
    keyChanged = pyqtSignal()
    assignedPrinterChanged = pyqtSignal()
    ownerChanged = pyqtSignal()

    def __init__(self, output_controller: "PrinterOutputController", key: str = "", name: str = "", parent=None):
        super().__init__(parent)
        self._output_controller = output_controller
        self._state = ""
        self._time_total = 0
        self._time_elapsed = 0
        self._name = name  # Human readable name
        self._key = key  # Unique identifier
        self._assigned_printer = None  # type: Optional[PrinterOutputModel]
        self._owner = ""  # Who started/owns the print job?

    @pyqtProperty(str, notify=ownerChanged)
    def owner(self):
        return self._owner

    def updateOwner(self, owner):
        if self._owner != owner:
            self._owner = owner
            self.ownerChanged.emit()

    @pyqtProperty(QObject, notify=assignedPrinterChanged)
    def assignedPrinter(self):
        return self._assigned_printer

    def updateAssignedPrinter(self, assigned_printer: "PrinterOutputModel"):
        if self._assigned_printer != assigned_printer:
            old_printer = self._assigned_printer
            self._assigned_printer = assigned_printer
            if old_printer is not None:
                # If the previously assigned printer is set, this job is moved away from it.
                old_printer.updateActivePrintJob(None)
            self.assignedPrinterChanged.emit()

    @pyqtProperty(str, notify=keyChanged)
    def key(self):
        return self._key

    def updateKey(self, key: str):
        if self._key != key:
            self._key = key
            self.keyChanged.emit()

    @pyqtProperty(str, notify = nameChanged)
    def name(self):
        return self._name

    def updateName(self, name: str):
        if self._name != name:
            self._name = name
            self.nameChanged.emit()

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

    @pyqtSlot(str)
    def setState(self, state):
        self._output_controller.setJobState(self, state)