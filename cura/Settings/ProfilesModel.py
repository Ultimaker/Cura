# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from collections import OrderedDict

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
    LayerHeightWithoutUnitRole = Qt.UserRole + 1002
    AvailableRole = Qt.UserRole + 1003

    def __init__(self, parent = None):
        super().__init__(parent)
        self.addRoleName(self.LayerHeightRole, "layer_height")
        self.addRoleName(self.LayerHeightWithoutUnitRole, "layer_height_without_unit")
        self.addRoleName(self.AvailableRole, "available")

        Application.getInstance().globalContainerStackChanged.connect(self._update)

        Application.getInstance().getMachineManager().activeVariantChanged.connect(self._update)
        Application.getInstance().getMachineManager().activeStackChanged.connect(self._update)
        Application.getInstance().getMachineManager().activeMaterialChanged.connect(self._update)

    # Factory function, used by QML
    @staticmethod
    def createProfilesModel(engine, js_engine):
        return ProfilesModel.getInstance()

    ##  Get the singleton instance for this class.
    @classmethod
    def getInstance(cls) -> "ProfilesModel":
        # Note: Explicit use of class name to prevent issues with inheritance.
        if not ProfilesModel.__instance:
            ProfilesModel.__instance = cls()
        return ProfilesModel.__instance

    __instance = None   # type: "ProfilesModel"

    ##  Fetch the list of containers to display.
    #
    #   See UM.Settings.Models.InstanceContainersModel._fetchInstanceContainers().
    def _fetchInstanceContainers(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack is None:
            return []
        global_stack_definition = global_container_stack.getBottom()

        # Get the list of extruders and place the selected extruder at the front of the list.
        extruder_manager = ExtruderManager.getInstance()
        active_extruder = extruder_manager.getActiveExtruderStack()
        extruder_stacks = extruder_manager.getActiveExtruderStacks()
        if active_extruder in extruder_stacks:
            extruder_stacks.remove(active_extruder)
            extruder_stacks = [active_extruder] + extruder_stacks

        if ExtruderManager.getInstance().getActiveExtruderStacks():
            # Multi-extruder machine detected.
            materials = [extruder.material for extruder in extruder_stacks]
        else:
            # Machine with one extruder.
            materials = [global_container_stack.material]

        # Fetch the list of usable qualities across all extruders.
        # The actual list of quality profiles come from the first extruder in the extruder list.
        result = QualityManager.getInstance().findAllQualitiesForMachineAndMaterials(global_stack_definition,
                                                                                     materials)

        for quality in QualityManager.getInstance().findAllUsableQualitiesForMachineAndExtruders(
                global_container_stack, extruder_stacks):
            if quality not in result:
                result.append(quality)
        return result

    ##  Re-computes the items in this model, and adds the layer height role.
    def _recomputeItems(self):
        #Some globals that we can re-use.
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack is None:
            return

        # Get the list of extruders and place the selected extruder at the front of the list.
        extruder_manager = ExtruderManager.getInstance()
        active_extruder = extruder_manager.getActiveExtruderStack()
        extruder_stacks = extruder_manager.getActiveExtruderStacks()
        if active_extruder in extruder_stacks:
            extruder_stacks.remove(active_extruder)
            extruder_stacks = [active_extruder] + extruder_stacks
        # Get a list of available qualities for this machine and material
        qualities = QualityManager.getInstance().findAllUsableQualitiesForMachineAndExtruders(global_container_stack,
                                                                                              extruder_stacks)
        container_registry = ContainerRegistry.getInstance()
        machine_manager = Application.getInstance().getMachineManager()

        unit = global_container_stack.getBottom().getProperty("layer_height", "unit")
        if not unit:
            unit = ""

        # group all quality items according to quality_types, so we know which profile suits the currently
        # active machine and material, and later yield the right ones.
        tmp_all_quality_items = OrderedDict()
        for item in super()._recomputeItems():
            profile = container_registry.findContainers(id=item["id"])
            quality_type = profile[0].getMetaDataEntry("quality_type") if profile else ""

            if quality_type not in tmp_all_quality_items:
                tmp_all_quality_items[quality_type] = {"suitable_container": None, "all_containers": []}

            tmp_all_quality_items[quality_type]["all_containers"].append(item)
            if tmp_all_quality_items[quality_type]["suitable_container"] is None and profile[0] in qualities:
                tmp_all_quality_items[quality_type]["suitable_container"] = item

        # reverse the ordering (finest first, coarsest last)
        all_quality_items = OrderedDict()
        for key in reversed(tmp_all_quality_items.keys()):
            all_quality_items[key] = tmp_all_quality_items[key]

        for data_item in all_quality_items.values():
            item = data_item["suitable_container"]
            if item is None:
                item = data_item["all_containers"][0]

            profile = container_registry.findContainers(id = item["id"])
            if not profile:
                item["layer_height"] = ""  # Can't update a profile that is unknown.
                item["available"] = False
                yield item
                continue

            profile = profile[0]
            item["available"] = profile in qualities

            # Easy case: This profile defines its own layer height.
            if profile.hasProperty("layer_height", "value"):
                self._setItemLayerHeight(item, profile.getProperty("layer_height", "value"), unit)
                yield item
                continue

            # Quality-changes profile that has no value for layer height. Get the corresponding quality profile and ask that profile.
            quality_type = profile.getMetaDataEntry("quality_type", None)
            if quality_type:
                quality_results = machine_manager.determineQualityAndQualityChangesForQualityType(quality_type)
                for quality_result in quality_results:
                    if quality_result["stack"] is global_container_stack:
                        quality = quality_result["quality"]
                        break
                else: #No global container stack in the results:
                    if quality_results:
                        quality = quality_results[0]["quality"] #Take any of the extruders.
                    else:
                        quality = None
                if quality and quality.hasProperty("layer_height", "value"):
                    self._setItemLayerHeight(item, quality.getProperty("layer_height", "value"), unit)
                    yield item
                    continue

            #Quality has no value for layer height either. Get the layer height from somewhere lower in the stack.
            skip_until_container = global_container_stack.material
            if not skip_until_container or skip_until_container == ContainerRegistry.getInstance().getEmptyInstanceContainer(): #No material in stack.
                skip_until_container = global_container_stack.variant
                if not skip_until_container or skip_until_container == ContainerRegistry.getInstance().getEmptyInstanceContainer(): #No variant in stack.
                    skip_until_container = global_container_stack.getBottom()
            self._setItemLayerHeight(item, global_container_stack.getRawProperty("layer_height", "value", skip_until_container = skip_until_container.getId()), unit)  # Fall through to the currently loaded material.
            yield item

    def _setItemLayerHeight(self, item, value, unit):
        item["layer_height"] = str(value) + unit
        item["layer_height_without_unit"] = str(value)
