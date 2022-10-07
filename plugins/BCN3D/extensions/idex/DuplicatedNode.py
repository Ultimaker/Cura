
from UM.Math.Vector import Vector
from UM.Operations.MirrorOperation import MirrorOperation
from UM.Application import Application


from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Scene.BuildPlateDecorator import BuildPlateDecorator
from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.SetObjectExtruderOperation import SetObjectExtruderOperation


from copy import deepcopy

class DuplicatedNode(CuraSceneNode):

    def __init__(self, node, parent = None):
        super().__init__(parent)
        self.node = node
        self.setTransformation(node.getLocalTransformation())
        self.setMeshData(node.getMeshData())
        self.setVisible(deepcopy(node.isVisible()))
        self._selectable = False
        self._name = deepcopy(node.getName())
        # Make sure the BuildPlateDecorator is added the first
        build_plate_decorator = node.getDecorator(BuildPlateDecorator)
        if build_plate_decorator is not None:
            self.addDecorator(deepcopy(build_plate_decorator))
        for decorator in node.getDecorators():
            self.addDecorator(deepcopy(decorator))

        for child in node.getChildren():
            if isinstance(child, CuraSceneNode):
                self.addChild(DuplicatedNode(child))
            else:
                self.addChild(deepcopy(child))

        node.calculateBoundingBoxMesh()
        self.node.transformationChanged.connect(self._onTransformationChanged)
        self.node.parentChanged.connect(self._someParentChanged)
        self.parentChanged.connect(self._someParentChanged)
        SetObjectExtruderOperation(self, ExtruderManager.getInstance().getExtruderStack(0).getId()).redo()

    def setSelectable(self, select: bool):
        self._selectable = False

    def update(self):
        if type(self.getParent()) == DuplicatedNode:
            self.setTransformation(self.node.getLocalTransformation())
            return
        print_mode = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
        machine_width = Application.getInstance().getGlobalContainerStack().getProperty("machine_width", "value")
        self.setScale(self.node.getScale())
        node_pos = self.node.getPosition()
        self.setTransformation(self.node.getLocalTransformation())

        if print_mode == "mirror":
            MirrorOperation(self, Vector(-1, 1, 1)).redo()
            self.setPosition(Vector(-node_pos.x, node_pos.y, node_pos.z))
        elif print_mode == "duplication":
            self.setPosition(Vector(node_pos.x + (machine_width/2), node_pos.y, node_pos.z))
        else:
            return

        if node_pos.x > 0:
            self.node.setPosition(Vector(0, node_pos.y, node_pos.z))

    def _onTransformationChanged(self, node):
        print_mode = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
        if print_mode not in ["singleT0", "singleT1", "dual"]:
            self.update()

    def _someParentChanged(self, node=None):
        self.update()