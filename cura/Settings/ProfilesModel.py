# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import Qt

from UM.Application import Application
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.Models.InstanceContainersModel import InstanceContainersModel

from cura.QualityManager import QualityManager
from cura.Settings.ExtruderManager import ExtruderManager

##  QML Model for listing the current list of valid quality profiles.
#
class ProfilesModel(InstanceContainersModel):
    LayerHeightRole = Qt.UserRole + 1001

    def __init__(self, parent = None):
        super().__init__(parent)
        self.addRoleName(self.LayerHeightRole, "layer_height")

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

        # Get the  list of extruders and place the selected extruder at the front of the list.
        extruder_manager = ExtruderManager.getInstance()
        active_extruder = extruder_manager.getActiveExtruderStack()
        extruder_stacks = extruder_manager.getActiveExtruderStacks()
        if active_extruder in extruder_stacks:
            extruder_stacks.remove(active_extruder)
            extruder_stacks = [active_extruder] + extruder_stacks

        # Fetch the list of useable qualities across all extruders.
        # The actual list of quality profiles come from the first extruder in the extruder list.
        return QualityManager.getInstance().findAllUsableQualitiesForMachineAndExtruders(global_container_stack,
                                                                                         extruder_stacks)

    ##  Re-computes the items in this model, and adds the layer height role.
    def _recomputeItems(self):
        #Some globals that we can re-use.
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack is None:
            return
        container_registry = ContainerRegistry.getInstance()
        machine_manager = Application.getInstance().getMachineManager()

        unit = global_container_stack.getBottom().getProperty("layer_height", "unit")

        for item in super()._recomputeItems():
            profile = container_registry.findContainers(id = item["id"])
            if not profile:
                item["layer_height"] = "" #Can't update a profile that is unknown.
                yield item
                continue

            #Easy case: This profile defines its own layer height.
            profile = profile[0]
            if profile.hasProperty("layer_height", "value"):
                item["layer_height"] = str(profile.getProperty("layer_height", "value")) + unit
                yield item
                continue

            #Quality-changes profile that has no value for layer height. Get the corresponding quality profile and ask that profile.
            quality_type = profile.getMetaDataEntry("quality_type", None)
            if quality_type:
                quality_results = machine_manager.determineQualityAndQualityChangesForQualityType(quality_type)
                for quality_result in quality_results:
                    if quality_result["stack"] is global_container_stack:
                        quality = quality_result["quality"]
                        break
                else: #No global container stack in the results:
                    quality = quality_results[0]["quality"] #Take any of the extruders.
                if quality and quality.hasProperty("layer_height", "value"):
                    item["layer_height"] = str(quality.getProperty("layer_height", "value")) + unit
                    yield item
                    continue

            #Quality has no value for layer height either. Get the layer height from somewhere lower in the stack.
            skip_until_container = global_container_stack.findContainer({"type": "material"})
            if not skip_until_container: #No material in stack.
                skip_until_container = global_container_stack.findContainer({"type": "variant"})
                if not skip_until_container: #No variant in stack.
                    skip_until_container = global_container_stack.getBottom()
            item["layer_height"] = str(global_container_stack.getRawProperty("layer_height", "value", skip_until_container = skip_until_container.getId())) + unit #Fall through to the currently loaded material.
            yield item