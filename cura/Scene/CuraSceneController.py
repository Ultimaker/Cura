from UM.Logger import Logger

from PyQt5.QtCore import Qt, pyqtSlot, QObject, QTimer
from PyQt5.QtWidgets import QApplication

from UM.Scene.Camera import Camera
from cura.UI.ObjectsModel import ObjectsModel
from cura.Machines.Models.MultiBuildPlateModel import MultiBuildPlateModel

from UM.Application import Application
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Selection import Selection
from UM.Signal import Signal


class CuraSceneController(QObject):
    activeBuildPlateChanged = Signal()

    def __init__(self, objects_model: ObjectsModel, multi_build_plate_model: MultiBuildPlateModel) -> None:
        super().__init__()

        self._objects_model = objects_model
        self._multi_build_plate_model = multi_build_plate_model
        self._active_build_plate = -1

        self._last_selected_index = 0
        self._max_build_plate = 1  # default
        self._change_timer = QTimer()
        self._change_timer.setInterval(100)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self.updateMaxBuildPlate)
        Application.getInstance().getController().getScene().sceneChanged.connect(self.updateMaxBuildPlateDelayed)

    def updateMaxBuildPlateDelayed(self, *args):
        if args:
            source = args[0]
        else:
            source = None

        if not isinstance(source, SceneNode) or isinstance(source, Camera):
            return
        self._change_timer.start()

    def updateMaxBuildPlate(self, *args):
        max_build_plate = self._calcMaxBuildPlate()
        changed = False
        if max_build_plate != self._max_build_plate:
            self._max_build_plate = max_build_plate
            changed = True
        if changed:
            self._multi_build_plate_model.setMaxBuildPlate(self._max_build_plate)
            build_plates = [{"name": "Build Plate %d" % (i + 1), "buildPlateNumber": i} for i in range(self._max_build_plate + 1)]
            self._multi_build_plate_model.setItems(build_plates)
            if self._active_build_plate > self._max_build_plate:
                build_plate_number = 0
                if self._last_selected_index >= 0:  # go to the buildplate of the item you last selected
                    item = self._objects_model.getItem(self._last_selected_index)
                    if "node" in item:
                        node = item["node"]
                        build_plate_number = node.callDecoration("getBuildPlateNumber")
                self.setActiveBuildPlate(build_plate_number)
            # self.buildPlateItemsChanged.emit()  # TODO: necessary after setItems?

    def _calcMaxBuildPlate(self):
        max_build_plate = 0
        for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):
            if node.callDecoration("isSliceable"):
                build_plate_number = node.callDecoration("getBuildPlateNumber")
                if build_plate_number is None:
                    build_plate_number = 0
                max_build_plate = max(build_plate_number, max_build_plate)
        return max_build_plate

    @pyqtSlot(int)
    def changeSelection(self, index):
        """Either select or deselect an item"""

        modifiers = QApplication.keyboardModifiers()
        ctrl_is_active = modifiers & Qt.ControlModifier
        shift_is_active = modifiers & Qt.ShiftModifier

        if ctrl_is_active:
            item = self._objects_model.getItem(index)
            node = item["node"]
            if Selection.isSelected(node):
                Selection.remove(node)
            else:
                Selection.add(node)
        elif shift_is_active:
            polarity = 1 if index + 1 > self._last_selected_index else -1
            for i in range(self._last_selected_index, index + polarity, polarity):
                item = self._objects_model.getItem(i)
                node = item["node"]
                Selection.add(node)
        else:
            # Single select
            item = self._objects_model.getItem(index)
            node = item["node"]
            build_plate_number = node.callDecoration("getBuildPlateNumber")
            if build_plate_number is not None and build_plate_number != -1:
                self.setActiveBuildPlate(build_plate_number)
            Selection.clear()
            Selection.add(node)

        self._last_selected_index = index

    @pyqtSlot(int)
    def setActiveBuildPlate(self, nr):
        if nr == self._active_build_plate:
            return
        Logger.log("d", "Select build plate: %s" % nr)
        self._active_build_plate = nr
        Selection.clear()

        self._multi_build_plate_model.setActiveBuildPlate(nr)
        self._objects_model.setActiveBuildPlate(nr)
        self.activeBuildPlateChanged.emit()

    @staticmethod
    def createCuraSceneController():
        objects_model = Application.getInstance().getObjectsModel()
        multi_build_plate_model = Application.getInstance().getMultiBuildPlateModel()
        return CuraSceneController(objects_model = objects_model, multi_build_plate_model = multi_build_plate_model)
