# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

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
        materials = [global_container_stack.material]

        if active_extruder in extruder_stacks:
            extruder_stacks.remove(active_extruder)
            extruder_stacks = [active_extruder] + extruder_stacks
            materials = [extruder.material for extruder in extruder_stacks]

        # Fetch the list of usable qualities across all extruders.
        # The actual list of quality profiles come from the first extruder in the extruder list.
        result = QualityManager.getInstance().findAllUsableQualitiesForMachineAndExtruders(global_container_stack, extruder_stacks)

        # The usable quality types are set
        quality_type_set = set([x.getMetaDataEntry("quality_type") for x in result])

        # Fetch all qualities available for this machine and the materials selected in extruders
        all_qualities = QualityManager.getInstance().findAllQualitiesForMachineAndMaterials(global_stack_definition, materials)

        # If in the all qualities there is some of them that are not available due to incompatibility with materials
        # we also add it so that they will appear in the slide quality bar. However in recomputeItems will be marked as
        # not available so they will be shown in gray
        for quality in all_qualities:
            if quality.getMetaDataEntry("quality_type") not in quality_type_set:
                result.append(quality)

        # if still profiles are found, add a single empty_quality ("Not supported") instance to the drop down list
        if len(result) == 0:
            # If not qualities are found we dynamically create a not supported container for this machine + material combination
            not_supported_container = ContainerRegistry.getInstance().findContainers(id = "empty_quality")[0]
            result.append(not_supported_container)

        return result

    ##  Re-computes the items in this model, and adds the layer height role.
    def _recomputeItems(self):

        # Some globals that we can re-use.
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack is None:
            return

        # Detecting if the machine has multiple extrusion
        multiple_extrusion = global_container_stack.getProperty("machine_extruder_count", "value") > 1

        # Get the list of extruders and place the selected extruder at the front of the list.
        extruder_manager = ExtruderManager.getInstance()
        active_extruder = extruder_manager.getActiveExtruderStack()
        extruder_stacks = extruder_manager.getActiveExtruderStacks()

        if multiple_extrusion:
            # Place the active extruder at the front of the list.
            # This is a workaround checking if there is an active_extruder or not before moving it to the front of the list.
            # Actually, when a printer has multiple extruders, should exist always an active_extruder. However, in some
            # cases the active_extruder is still None.
            if active_extruder in extruder_stacks:
                extruder_stacks.remove(active_extruder)
            new_extruder_stacks = []
            if active_extruder is not None:
                new_extruder_stacks = [active_extruder]
            extruder_stacks = new_extruder_stacks + extruder_stacks

        # Get a list of usable/available qualities for this machine and material
        qualities = QualityManager.getInstance().findAllUsableQualitiesForMachineAndExtruders(global_container_stack, extruder_stacks)

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
            if tmp_all_quality_items[quality_type]["suitable_container"] is None:
                tmp_all_quality_items[quality_type]["suitable_container"] = item

        # reverse the ordering (finest first, coarsest last)
        all_quality_items = OrderedDict()
        for key in reversed(tmp_all_quality_items.keys()):
            all_quality_items[key] = tmp_all_quality_items[key]

        # First the suitable containers are set in the model
        containers = []
        for data_item in all_quality_items.values():
            suitable_item = data_item["suitable_container"]
            if suitable_item is not None:
                containers.append(suitable_item)

        # Once the suitable containers are collected, the rest of the containers are appended
        for data_item in all_quality_items.values():
            for item in data_item["all_containers"]:
                if item not in containers:
                    containers.append(item)

        # Now all the containers are set
        for item in containers:
            profile = container_registry.findContainers(id = item["id"])

            # When for some reason there is no profile container in the registry
            if not profile:
                self._setItemLayerHeight(item, "", "")
                item["available"] = False
                yield item
                continue

            profile = profile[0]

            # When there is a profile but it's an empty quality should. It's shown in the list (they are "Not Supported" profiles)
            if profile.getId() == "empty_quality":
                self._setItemLayerHeight(item, "", "")
                item["available"] = True
                yield item
                continue

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
                else:
                    # No global container stack in the results:
                    if quality_results:
                        quality = quality_results[0]["quality"]  # Take any of the extruders.
                    else:
                        quality = None
                if quality and quality.hasProperty("layer_height", "value"):
                    self._setItemLayerHeight(item, quality.getProperty("layer_height", "value"), unit)
                    yield item
                    continue

            # Quality has no value for layer height either. Get the layer height from somewhere lower in the stack.
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
