from UM.Logger import Logger
from PyQt5.QtCore import pyqtSignal, pyqtProperty, pyqtSlot
from UM.Application import Application
from UM.Qt.ListModel import ListModel
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Selection import Selection
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
#from cura.Scene.CuraSceneNode import CuraSceneNode
from UM.Preferences import Preferences


class ObjectManager(ListModel):
    def __init__(self):
        super().__init__()
        self._last_selected_index = 0
        Application.getInstance().getController().getScene().sceneChanged.connect(self._update_scene_changed)
        Preferences.getInstance().preferenceChanged.connect(self._update)
        Application.getInstance().activeBuildPlateChanged.connect(self._update)

    def _update(self, *args):
        nodes = []
        filter_current_build_plate = Preferences.getInstance().getValue("view/filter_current_build_plate")
        active_build_plate_number = Application.getInstance().activeBuildPlate
        for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):
            if not issubclass(type(node), SceneNode) or (not node.getMeshData() and not node.callDecoration("getLayerData")):
                continue
            if not node.callDecoration("isSliceable"):
                continue
            node_build_plate_number = node.callDecoration("getBuildPlateNumber")
            if filter_current_build_plate and node_build_plate_number != active_build_plate_number:
                continue
            nodes.append({
                "name": node.getName(),
                "isSelected": Selection.isSelected(node),
                "isOutsideBuildArea": node.isOutsideBuildArea(),
                "buildPlateNumber": node_build_plate_number,
                "node": node
            })
        nodes = sorted(nodes, key=lambda n: n["name"])
        self.setItems(nodes)

        self.itemsChanged.emit()

    def _update_scene_changed(self, *args):
        # if args and type(args[0]) is not CuraSceneNode:
        #     Logger.log("d", "   ascdf %s", args)
        #     return
        self._update(*args)

    ##  Either select or deselect an item
    @pyqtSlot(int)
    def changeSelection(self, index):
        modifiers = QApplication.keyboardModifiers()
        ctrl_is_active = modifiers & Qt.ControlModifier
        shift_is_active = modifiers & Qt.ShiftModifier

        if ctrl_is_active:
            item = self.getItem(index)
            node = item["node"]
            if Selection.isSelected(node):
                Selection.remove(node)
            else:
                Selection.add(node)
        elif shift_is_active:
            polarity = 1 if index + 1 > self._last_selected_index else -1
            for i in range(self._last_selected_index, index + polarity, polarity):
                item = self.getItem(i)
                node = item["node"]
                Selection.add(node)
        else:
            # Single select
            item = self.getItem(index)
            node = item["node"]
            Selection.clear()
            Selection.add(node)
            build_plate_number = node.callDecoration("getBuildPlateNumber")
            if build_plate_number is not None and build_plate_number != -1:
                Application.getInstance().setActiveBuildPlate(build_plate_number)

        self._last_selected_index = index

        # testing
        for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):
            if node.callDecoration("getLayerData"):
                Logger.log("d", "   ##### NODE: %s", node)

    @staticmethod
    def createObjectManager():
        return ObjectManager()
