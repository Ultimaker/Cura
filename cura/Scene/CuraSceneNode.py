from typing import List

from UM.Application import Application
from UM.Logger import Logger
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
        return super().isVisible() and self.callDecoration("getBuildPlateNumber") == Application.getInstance().getBuildPlateModel().activeBuildPlate

    def isSelectable(self) -> bool:
        return super().isSelectable() and self.callDecoration("getBuildPlateNumber") == Application.getInstance().getBuildPlateModel().activeBuildPlate

    def getPrintingExtruderPosition(self) -> int:
        # took bits and pieces from extruders model, solid view

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        per_mesh_stack = self.callDecoration("getStack")
        # It's only set if you explicitly choose an extruder
        extruder_id = self.callDecoration("getActiveExtruder")

        machine_extruder_count = global_container_stack.getProperty("machine_extruder_count", "value")

        extruder_index = 0

        for extruder in Application.getInstance().getExtruderManager().getMachineExtruders(global_container_stack.getId()):
            position = extruder.getMetaDataEntry("position", default = "0")  # Get the position
            try:
                position = int(position)
            except ValueError:
                # Not a proper int.
                position = -1
            if position > machine_extruder_count:
                continue

            # Find out the extruder index if we know the id.
            if extruder_id is not None and extruder_id == extruder.getId():
                extruder_index = position
                break

        # Use the support extruder instead of the active extruder if this is a support_mesh
        if per_mesh_stack:
            if per_mesh_stack.getProperty("support_mesh", "value"):
                extruder_index = int(global_container_stack.getProperty("support_extruder_nr", "value"))

        return extruder_index

    def getDiffuseColor(self) -> List[float]:
        # took bits and pieces from extruders model, solid view

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        machine_extruder_count = global_container_stack.getProperty("machine_extruder_count", "value")

        extruder_index = self.getPrintingExtruderPosition()

        material_color = ExtrudersModel.defaultColors[extruder_index]

        # Collect color from the extruder we want
        for extruder in Application.getInstance().getExtruderManager().getMachineExtruders(global_container_stack.getId()):
            position = extruder.getMetaDataEntry("position", default = "0")  # Get the position
            try:
                position = int(position)
            except ValueError:
                # Not a proper int.
                position = -1
            if position > machine_extruder_count:
                continue

            if extruder.material and position == extruder_index:
                material_color = extruder.material.getMetaDataEntry("color_code", default = material_color)
                break

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
