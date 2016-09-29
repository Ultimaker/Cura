# Copyright (c) 2016 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Application import Application
from UM.Settings.Models.InstanceContainersModel import InstanceContainersModel
from UM.Settings.ContainerRegistry import ContainerRegistry

from cura.Settings.ExtruderManager import ExtruderManager

##  QML Model for listing the current list of valid quality profiles.
#
class ProfilesModel(InstanceContainersModel):
    def __init__(self, parent = None):
        super().__init__(parent)

        Application.getInstance().globalContainerStackChanged.connect(self._update)

    ##  Fetch the list of containers to display.
    #
    #   See UM.Settings.Models.InstanceContainersModel._fetchInstanceContainers().
    def _fetchInstanceContainers(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack is None:
            return []

        global_machine_definition = global_container_stack.getBottom()

        extruder_stacks = ExtruderManager.getInstance().getActiveExtruderStacks()
        if extruder_stacks:
            # Multi-extruder machine detected.

            # Determine the common set of quality types which can be
            # applied to all of the materials for this machine.
            quality_type_dict = self.__fetchQualityTypeDictForStack(extruder_stacks[0], global_machine_definition)
            common_quality_types = set(quality_type_dict.keys())
            for stack in extruder_stacks[1:]:
                next_quality_type_dict = self.__fetchQualityTypeDictForStack(stack, global_machine_definition)
                common_quality_types.intersection_update(set(next_quality_type_dict.keys()))

            return [quality_type_dict[quality_type] for quality_type in common_quality_types]

        else:
            # Machine with one extruder.
            quality_type_dict = self.__fetchQualityTypeDictForStack(global_container_stack, global_machine_definition)
            return list(quality_type_dict.values())
        return []

    def __fetchQualityTypeDictForStack(self, stack, global_machine_definition):
        criteria = {"type": "quality" }
        if global_machine_definition.getMetaDataEntry("has_machine_quality", False):
            criteria["definition"] = global_machine_definition.getId()
            if global_machine_definition.getMetaDataEntry("has_materials", False):
                material = stack.findContainer(type="material")
                criteria["material"] = material.getId()
        else:
            criteria["definition"] = "fdmprinter"

        qualities = ContainerRegistry.getInstance().findInstanceContainers(**criteria)

        quality_type_dict = {}
        for quality in qualities:
            quality_type_dict[quality.getMetaDataEntry("quality_type")] = quality
        return quality_type_dict
