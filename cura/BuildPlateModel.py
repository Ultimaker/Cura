from UM.Qt.ListModel import ListModel
from PyQt5.QtCore import pyqtSignal, pyqtProperty, pyqtSlot
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Logger import Logger
from UM.Application import Application


class BuildPlateModel(ListModel):
    maxBuildPlateChanged = pyqtSignal()
    activeBuildPlateChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        Application.getInstance().getController().getScene().sceneChanged.connect(self.updateMaxBuildPlate)  # it may be a bit inefficient when changing a lot simultaneously

        self._max_build_plate = 1  # default
        self._active_build_plate = 0

    @pyqtSlot(int)
    def setActiveBuildPlate(self, nr):
        if nr == self._active_build_plate:
            return
        Logger.log("d", "Select build plate: %s" % nr)
        self._active_build_plate = nr

        self.activeBuildPlateChanged.emit()

    @pyqtProperty(int, notify = activeBuildPlateChanged)
    def activeBuildPlate(self):
        return self._active_build_plate

    ##  Return the highest build plate number
    @pyqtProperty(int, notify = maxBuildPlateChanged)
    def maxBuildPlate(self):
        return self._max_build_plate

    def updateMaxBuildPlate(self, source):
        if not issubclass(type(source), SceneNode):
            return
        max_build_plate = self._calcMaxBuildPlate()
        changed = False
        if max_build_plate != self._max_build_plate:
            self._max_build_plate = max_build_plate
            changed = True
        if changed:
            self.maxBuildPlateChanged.emit()
            build_plates = [{"name": "Build Plate %d" % (i + 1), "buildPlateNumber": i} for i in range(self._max_build_plate + 1)]
            self.setItems(build_plates)
            self.itemsChanged.emit()

    def _calcMaxBuildPlate(self):
        max_build_plate = 0
        for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):
            if node.callDecoration("isSliceable"):
                build_plate_number = node.callDecoration("getBuildPlateNumber")
                max_build_plate = max(build_plate_number, max_build_plate)
        return max_build_plate

    @staticmethod
    def createBuildPlateModel():
        return BuildPlateModel()
