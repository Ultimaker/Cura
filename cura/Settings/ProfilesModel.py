# Copyright (c) 2016 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Application import Application
from UM.Settings.Models.InstanceContainersModel import InstanceContainersModel

from cura.QualityManager import QualityManager
from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.MachineManager import MachineManager

##  QML Model for listing the current list of valid quality profiles.
#
class ProfilesModel(InstanceContainersModel):
    def __init__(self, parent = None):
        super().__init__(parent)

        Application.getInstance().globalContainerStackChanged.connect(self._update)

        Application.getInstance().getMachineManager().activeVariantChanged.connect(self._update)
        Application.getInstance().getMachineManager().activeStackChanged.connect(self._update)
        Application.getInstance().getMachineManager().activeMaterialChanged.connect(self._update)

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
            materials = [stack.findContainer(type="material") for stack in extruder_stacks]
        else:
            # Machine with one extruder.
            materials = [global_container_stack.findContainer(type="material")]

        quality_types = QualityManager.getInstance().findAllQualityTypesForMachineAndMaterials(global_machine_definition,
                                                                                            materials)
        # Map the list of quality_types to InstanceContainers
        qualities = QualityManager.getInstance().findAllQualitiesForMachineMaterial(global_machine_definition,
                                                                                    materials[0])
        quality_type_dict = {}
        for quality in qualities:
            quality_type_dict[quality.getMetaDataEntry("quality_type")] = quality

        return [quality_type_dict[quality_type] for quality_type in quality_types]
