from typing import List

from UM.Application import Application
from UM.Scene.SceneNode import SceneNode
from copy import deepcopy
from cura.Settings.ExtrudersModel import ExtrudersModel


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
        return super().isVisible() and self.callDecoration("getBuildPlateNumber") == Application.getInstance().getMultiBuildPlateModel().activeBuildPlate

    def isSelectable(self) -> bool:
        return super().isSelectable() and self.callDecoration("getBuildPlateNumber") == Application.getInstance().getMultiBuildPlateModel().activeBuildPlate

    ##  Get the extruder used to print this node. If there is no active node, then the extruder in position zero is returned
    #   TODO The best way to do it is by adding the setActiveExtruder decorator to every node when is loaded
    def getPrintingExtruder(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        per_mesh_stack = self.callDecoration("getStack")
        extruders = list(global_container_stack.extruders.values())

        # Use the support extruder instead of the active extruder if this is a support_mesh
        if per_mesh_stack:
            if per_mesh_stack.getProperty("support_mesh", "value"):
                return extruders[int(global_container_stack.getProperty("support_extruder_nr", "value"))]

        # It's only set if you explicitly choose an extruder
        extruder_id = self.callDecoration("getActiveExtruder")

        for extruder in extruders:
            # Find out the extruder if we know the id.
            if extruder_id is not None:
                if extruder_id == extruder.getId():
                    return extruder
            else: # If the id is unknown, then return the extruder in the position 0
                try:
                    if extruder.getMetaDataEntry("position", default = "0") == "0":  # Check if the position is zero
                        return extruder
                except ValueError:
                    continue

        # This point should never be reached
        return None

    ##  Return the color of the material used to print this model
    def getDiffuseColor(self) -> List[float]:
        printing_extruder = self.getPrintingExtruder()

        material_color = "#808080"  # Fallback color
        if printing_extruder is not None and printing_extruder.material:
            material_color = printing_extruder.material.getMetaDataEntry("color_code", default = material_color)

        # Colors are passed as rgb hex strings (eg "#ffffff"), and the shader needs
        # an rgba list of floats (eg [1.0, 1.0, 1.0, 1.0])
        return [
            int(material_color[1:3], 16) / 255,
            int(material_color[3:5], 16) / 255,
            int(material_color[5:7], 16) / 255,
            1.0
        ]

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
