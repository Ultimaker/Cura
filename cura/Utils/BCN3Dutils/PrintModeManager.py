from UM.Application import Application

from UM.Signal import Signal
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
from UM.Math.Vector import Vector
import cura.CuraApplication
from cura.Scene.CuraSceneNode import CuraSceneNode
from .Scene.DuplicatedNode import DuplicatedNode
from cura.Settings.ExtruderManager import ExtruderManager
from cura.Arranging.ShapeArray import ShapeArray
from UM.Scene.Selection import Selection
from UM.Logger import Logger


class PrintModeManager:

    def __init__(self):
        super().__init__()
        if PrintModeManager._instance is not None:
            raise ValueError("Duplicate singleton creation")

        PrintModeManager._instance = self
        self._duplicated_nodes = []
        self._scene = Application.getInstance().getController().getScene()
        application = cura.CuraApplication.CuraApplication.getInstance()
        self._global_stack = application.getGlobalContainerStack()
        self._last_mode = "singleT0"
        if self._global_stack is not None:
            self._global_stack.setProperty("print_mode", "value", "singleT0")
            for node in Selection.getAllSelectedObjects():
                node.setSetting("print_mode", "singleT0")
            self._last_mode = self._global_stack.getProperty("print_mode", "value")

        #remember last mode and settings offset
        self._last_max_offset = 0
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalStackChanged)
        self._onGlobalStackChanged()
        #
        self.printModeChanged.connect(self._onPrintModeChanged)
        self._onPrintModeChanged()

    def addDuplicatedNode(self, node):
        node.callDecoration("setBuildPlateNumber", 0)
        if node not in self._duplicated_nodes:
            self._duplicated_nodes.append(node)
        for child in node.getChildren():
            if isinstance(child, CuraSceneNode):
                self.addDuplicatedNode(child)

    def deleteDuplicatedNodes(self):
        del self._duplicated_nodes[:]

    def deleteDuplicatedNode(self, node, delete_children = True):
        if node in self._duplicated_nodes:
            self._duplicated_nodes.remove(node)
        if delete_children:
            for child in node.getChildren():
                if isinstance(child, CuraSceneNode):
                    self.deleteDuplicatedNode(child)

    def getDuplicatedNode(self, node):
        for node_dup in self._duplicated_nodes:
            if node_dup.node == node:
                return node_dup

    def getDuplicatedNodes(self):
        return self._duplicated_nodes

    def renderDuplicatedNode(self, node):
        node.callDecoration("setBuildPlateNumber", 0)
        if node.node.getParent() != self._scene.getRoot():
            parent = self.getDuplicatedNode(node.node.getParent())
        else:
            parent = self._scene.getRoot()
        op = AddSceneNodeOperation(node, parent)
        op.redo()
        node.update()

    def renderDuplicatedNodes(self):
        for node in self._duplicated_nodes:
            self.renderDuplicatedNode(node)

    def removeDuplicatedNodes(self):
        for node in self._duplicated_nodes:
            op = RemoveSceneNodeOperation(node)
            op.redo()

    def _onGlobalStackChanged(self):
        if self._global_stack:
            self._global_stack.propertyChanged.disconnect(self._onPropertyChanged)

        self._global_stack = Application.getInstance().getGlobalContainerStack()

        if self._global_stack:
            self._global_stack.propertyChanged.connect(self._onPropertyChanged)
            if not self._global_stack.getProperty("print_mode", "enabled"):
                self.removeDuplicatedNodes()
                self.deleteDuplicatedNodes()
            else:
                if len(self._duplicated_nodes) == 0:
                    for node in self._scene.getRoot().getChildren():
                        if type(node) == CuraSceneNode:
                            self.addDuplicatedNode(DuplicatedNode(node, node.getParent()))
                self._onPrintModeChanged()

    printModeChanged = Signal()
    printModeApplied = Signal()

    def _onPropertyChanged(self, key, property_name):
        if key == "print_mode" and property_name == "value":
            self.printModeChanged.emit()

    def _onPrintModeChanged(self):
        if self._global_stack:
            print_mode = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
            machine_width = Application.getInstance().getGlobalContainerStack().getProperty("machine_width", "value")
            nodes = self._scene.getRoot().getChildren()
            #max_offset = 0
            offset = 0
            sceneNodes = 0
            for node in nodes:
                self._setActiveExtruder(node)
                #We only want to model_plate_move sliceable or group nodes
                if (node.callDecoration("isSliceable") or node.callDecoration("isGroup") ) and not isinstance(node, DuplicatedNode):
                    position = node.getPosition()
                    if print_mode in ["mirror", "duplication"]:
                        #we do not need to extend margin anymore due now is centerd on the ¨new¨bed and can not colapse
                        if self._last_mode in ["mirror", "duplication"]:
                            model_plate_proportion = 1
                            model_plate_move = 0
                        elif self._last_mode in ["singleT0", "singleT1", "dual"]:
                            model_plate_proportion = 1/2
                            model_plate_move = machine_width/4
                        offset = position.x * model_plate_proportion - model_plate_move #- max_offset + self._last_max_offset
                        #self._last_max_offset = max_offset
                        self.renderDuplicatedNodes()
                    elif print_mode in ["singleT0", "singleT1", "dual"]:
                        if self._last_mode in ["mirror", "duplication"]:
                            model_plate_proportion = 2
                            model_plate_move = machine_width/4
                        elif self._last_mode in ["singleT0", "singleT1", "dual"]:
                            model_plate_proportion = 1
                            model_plate_move = 0
                        offset = ( position.x + model_plate_move) * model_plate_proportion #+ self._last_max_offset (on moves))
                        #self._last_max_offset = 0
                        self.removeDuplicatedNodes()

                    sceneNodes += 1
                    node.setPosition(Vector(offset, position.y, position.z))
                
            if sceneNodes > 0:
                self._last_mode = print_mode


    def _setActiveExtruder(self, node):
        if type(node) == CuraSceneNode:
            node.callDecoration("setActiveExtruder", ExtruderManager.getInstance().getExtruderStack(0).getId())
            for child in node.getChildren():
                self._setActiveExtruder(child)

    @classmethod
    def getInstance(cls) -> "PrintModeManager":
        # Note: Explicit use of class name to prevent issues with inheritance.
        if not PrintModeManager._instance:
            PrintModeManager._instance = cls()

        return PrintModeManager._instance

    _instance = None