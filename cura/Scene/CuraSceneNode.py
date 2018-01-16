from UM.Application import Application
from UM.Logger import Logger
from UM.Scene.SceneNode import SceneNode
from copy import deepcopy


##  Scene nodes that are models are only seen when selecting the corresponding build plate
#   Note that many other nodes can just be UM SceneNode objects.
class CuraSceneNode(SceneNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._outside_buildarea = False

    def setOutsideBuildArea(self, new_value):
        self._outside_buildarea = new_value

    def isOutsideBuildArea(self):
        return self._outside_buildarea or self.callDecoration("getBuildPlateNumber") < 0

    def isVisible(self):
        return super().isVisible() and self.callDecoration("getBuildPlateNumber") == Application.getInstance().getBuildPlateModel().activeBuildPlate

    def isSelectable(self) -> bool:
        return super().isSelectable() and self.callDecoration("getBuildPlateNumber") == Application.getInstance().getBuildPlateModel().activeBuildPlate

    ##  Taken from SceneNode, but replaced SceneNode with CuraSceneNode
    def __deepcopy__(self, memo):
        copy = CuraSceneNode()
        copy.setTransformation(self.getLocalTransformation())
        copy.setMeshData(self._mesh_data)
        copy.setVisible(deepcopy(self._visible, memo))
        copy._selectable = deepcopy(self._selectable, memo)
        copy._name = deepcopy(self._name, memo)
        for decorator in self._decorators:
            copy.addDecorator(deepcopy(decorator, memo))

        for child in self._children:
            copy.addChild(deepcopy(child, memo))
        self.calculateBoundingBoxMesh()
        return copy

    def transformChanged(self) -> None:
        self._transformChanged()
