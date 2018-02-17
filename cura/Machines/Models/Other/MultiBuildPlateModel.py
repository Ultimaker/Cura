from PyQt5.QtCore import pyqtSignal, pyqtProperty

from UM.Application import Application
from UM.Scene.Selection import Selection
from UM.Qt.ListModel import ListModel


class MultiBuildPlateModel(ListModel):

    maxBuildPlateChanged = pyqtSignal()
    activeBuildPlateChanged = pyqtSignal()
    selectionChanged = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)

        self._application = Application.getInstance()
        self._application.getController().getScene().sceneChanged.connect(self._updateSelectedObjectBuildPlateNumbers)
        Selection.selectionChanged.connect(self._updateSelectedObjectBuildPlateNumbers)

        self._max_build_plate = 1  # default
        self._active_build_plate = -1

    def setMaxBuildPlate(self, max_build_plate):
        self._max_build_plate = max_build_plate
        self.maxBuildPlateChanged.emit()

    ##  Return the highest build plate number
    @pyqtProperty(int, notify = maxBuildPlateChanged)
    def maxBuildPlate(self):
        return self._max_build_plate

    def setActiveBuildPlate(self, nr):
        self._active_build_plate = nr
        self.activeBuildPlateChanged.emit()

    @pyqtProperty(int, notify = activeBuildPlateChanged)
    def activeBuildPlate(self):
        return self._active_build_plate

    def _updateSelectedObjectBuildPlateNumbers(self, *args):
        result = set()
        for node in Selection.getAllSelectedObjects():
            result.add(node.callDecoration("getBuildPlateNumber"))
        self._selection_build_plates = list(result)
        self.selectionChanged.emit()

    @pyqtProperty("QVariantList", notify = selectionChanged)
    def selectionBuildPlates(self):
        return self._selection_build_plates
