# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, TYPE_CHECKING, List

from PyQt5.QtCore import pyqtSignal, pyqtProperty, QObject, pyqtSlot, QUrl
from PyQt5.QtGui import QImage

if TYPE_CHECKING:
    from cura.PrinterOutput.PrinterOutputController import PrinterOutputController
    from cura.PrinterOutput.Models.PrinterOutputModel import PrinterOutputModel
    from cura.PrinterOutput.Models.PrinterConfigurationModel import PrinterConfigurationModel


class PrintJobOutputModel(QObject):
    stateChanged = pyqtSignal()
    timeTotalChanged = pyqtSignal()
    timeElapsedChanged = pyqtSignal()
    nameChanged = pyqtSignal()
    keyChanged = pyqtSignal()
    assignedPrinterChanged = pyqtSignal()
    ownerChanged = pyqtSignal()
    configurationChanged = pyqtSignal()
    previewImageChanged = pyqtSignal()
    compatibleMachineFamiliesChanged = pyqtSignal()

    def __init__(self, output_controller: "PrinterOutputController", key: str = "", name: str = "", parent = None) -> None:
        super().__init__(parent)
        self._output_controller = output_controller
        self._state = ""
        self._time_total = 0
        self._time_elapsed = 0
        self._name = name  # Human readable name
        self._key = key  # Unique identifier
        self._assigned_printer = None  # type: Optional[PrinterOutputModel]
        self._owner = ""  # Who started/owns the print job?

        self._configuration = None  # type: Optional[PrinterConfigurationModel]
        self._compatible_machine_families = []  # type: List[str]
        self._preview_image_id = 0

        self._preview_image = None  # type: Optional[QImage]

    @pyqtProperty("QStringList", notify=compatibleMachineFamiliesChanged)
    def compatibleMachineFamilies(self):
        # Hack; Some versions of cluster will return a family more than once...
        return list(set(self._compatible_machine_families))

    def setCompatibleMachineFamilies(self, compatible_machine_families: List[str]) -> None:
        if self._compatible_machine_families != compatible_machine_families:
            self._compatible_machine_families = compatible_machine_families
            self.compatibleMachineFamiliesChanged.emit()

    @pyqtProperty(QUrl, notify=previewImageChanged)
    def previewImageUrl(self):
        self._preview_image_id += 1
        # There is an image provider that is called "print_job_preview". In order to ensure that the image qml object, that
        # requires a QUrl to function, updates correctly we add an increasing number. This causes to see the QUrl
        # as new (instead of relying on cached version and thus forces an update.
        temp = "image://print_job_preview/" + str(self._preview_image_id) + "/" + self._key
        return QUrl(temp, QUrl.TolerantMode)

    def getPreviewImage(self) -> Optional[QImage]:
        return self._preview_image

    def updatePreviewImage(self, preview_image: Optional[QImage]) -> None:
        if self._preview_image != preview_image:
            self._preview_image = preview_image
            self.previewImageChanged.emit()

    @pyqtProperty(QObject, notify=configurationChanged)
    def configuration(self) -> Optional["PrinterConfigurationModel"]:
        return self._configuration

    def updateConfiguration(self, configuration: Optional["PrinterConfigurationModel"]) -> None:
        if self._configuration != configuration:
            self._configuration = configuration
            self.configurationChanged.emit()

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

    def updateAssignedPrinter(self, assigned_printer: Optional["PrinterOutputModel"]) -> None:
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
    def timeTotal(self) -> int:
        return self._time_total

    @pyqtProperty(int, notify = timeElapsedChanged)
    def timeElapsed(self) -> int:
        return self._time_elapsed

    @pyqtProperty(int, notify = timeElapsedChanged)
    def timeRemaining(self) -> int:
        # Never get a negative time remaining
        return max(self.timeTotal - self.timeElapsed, 0)

    @pyqtProperty(float, notify = timeElapsedChanged)
    def progress(self) -> float:
        result = float(self.timeElapsed) / max(self.timeTotal, 1.0) # Prevent a division by zero exception.
        return min(result, 1.0)  # Never get a progress past 1.0

    @pyqtProperty(str, notify=stateChanged)
    def state(self) -> str:
        return self._state

    @pyqtProperty(bool, notify=stateChanged)
    def isActive(self) -> bool:
        inactive_states = [
            "pausing",
            "paused",
            "resuming",
            "wait_cleanup"
        ]
        if self.state in inactive_states and self.timeRemaining > 0:
            return False
        return True

    def updateTimeTotal(self, new_time_total):
        if self._time_total != new_time_total:
            self._time_total = new_time_total
            self.timeTotalChanged.emit()

    def updateTimeElapsed(self, new_time_elapsed):
        if self._time_elapsed != new_time_elapsed:
            self._time_elapsed = new_time_elapsed
            self.timeElapsedChanged.emit()

    def updateState(self, new_state: str) -> None:
        if self._state != new_state:
            self._state = new_state
            self.stateChanged.emit()

    @pyqtSlot(str)
    def setState(self, state):
        self._output_controller.setJobState(self, state)
