# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QTimer, pyqtSignal, pyqtProperty

from UM.Application import Application
from UM.Scene.Camera import Camera
from UM.Scene.Selection import Selection
from UM.Qt.ListModel import ListModel


#
# This is the model for multi build plate feature.
# This has nothing to do with the build plate types you can choose on the sidebar for a machine.
#
class MultiBuildPlateModel(ListModel):

    maxBuildPlateChanged = pyqtSignal()
    activeBuildPlateChanged = pyqtSignal()
    selectionChanged = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)

        self._update_timer = QTimer()
        self._update_timer.setInterval(100)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._updateSelectedObjectBuildPlateNumbers)

        self._application = Application.getInstance()
        self._application.getController().getScene().sceneChanged.connect(self._updateSelectedObjectBuildPlateNumbersDelayed)
        Selection.selectionChanged.connect(self._updateSelectedObjectBuildPlateNumbers)

        self._max_build_plate = 1  # default
        self._active_build_plate = -1

    def setMaxBuildPlate(self, max_build_plate):
        if self._max_build_plate != max_build_plate:
            self._max_build_plate = max_build_plate
            self.maxBuildPlateChanged.emit()

    ##  Return the highest build plate number
    @pyqtProperty(int, notify = maxBuildPlateChanged)
    def maxBuildPlate(self):
        return self._max_build_plate

    def setActiveBuildPlate(self, nr):
        if self._active_build_plate != nr:
            self._active_build_plate = nr
            self.activeBuildPlateChanged.emit()

    @pyqtProperty(int, notify = activeBuildPlateChanged)
    def activeBuildPlate(self):
        return self._active_build_plate

    def _updateSelectedObjectBuildPlateNumbersDelayed(self, *args):
        if not isinstance(args[0], Camera):
            self._update_timer.start()

    def _updateSelectedObjectBuildPlateNumbers(self, *args):
        result = set()
        for node in Selection.getAllSelectedObjects():
            result.add(node.callDecoration("getBuildPlateNumber"))
        self._selection_build_plates = list(result)
        self.selectionChanged.emit()

    @pyqtProperty("QVariantList", notify = selectionChanged)
    def selectionBuildPlates(self):
        return self._selection_build_plates
