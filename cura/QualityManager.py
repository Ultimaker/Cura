# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

# This collects a lot of quality and quality changes related code which was split between ContainerManager
# and the MachineManager and really needs to usable from both.
from typing import List, Optional, Dict, TYPE_CHECKING

from UM.Application import Application
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.InstanceContainer import InstanceContainer
from cura.Settings.ExtruderManager import ExtruderManager

if TYPE_CHECKING:
    from cura.Settings.GlobalStack import GlobalStack
    from cura.Settings.ExtruderStack import ExtruderStack
    from UM.Settings.DefinitionContainer import DefinitionContainerInterface

class QualityManager:

    ##  Get the singleton instance for this class.
    @classmethod
    def getInstance(cls) -> "QualityManager":
        # Note: Explicit use of class name to prevent issues with inheritance.
        if not QualityManager.__instance:
            QualityManager.__instance = cls()
        return QualityManager.__instance

    __instance = None   # type: "QualityManager"

    ##  Find a quality by name for a specific machine definition and materials.
    #
    #   \param quality_name
    #   \param machine_definition (Optional) \type{DefinitionContainerInterface} If nothing is
    #                               specified then the currently selected machine definition is used.
    #   \param material_containers (Optional) \type{List[InstanceContainer]} If nothing is specified then
    #                               the current set of selected materials is used.
    #   \return the matching quality container \type{InstanceContainer}
    def findQualityByName(self, quality_name: str, machine_definition: Optional["DefinitionContainerInterface"] = None, material_containers: List[InstanceContainer] = None) -> Optional[InstanceContainer]:
        criteria = {"type": "quality", "name": quality_name}
        result = self._getFilteredContainersForStack(machine_definition, material_containers, **criteria)

        # Fall back to using generic materials and qualities if nothing could be found.
        if not result and material_containers and len(material_containers) == 1:
            basic_materials = self._getBasicMaterials(material_containers[0])
            result = self._getFilteredContainersForStack(machine_definition, basic_materials, **criteria)

        return result[0] if result else None

    ##  Find a quality changes container by name.
    #
    #   \param quality_changes_name \type{str} the name of the quality changes container.
    #   \param machine_definition (Optional) \type{DefinitionContainer} If nothing is
    #                               specified then the currently selected machine definition is used..
    #   \return the matching quality changes containers \type{List[InstanceContainer]}
    def findQualityChangesByName(self, quality_changes_name: str, machine_definition: Optional["DefinitionContainerInterface"] = None):
        if not machine_definition:
            global_stack = Application.getGlobalContainerStack()
            if not global_stack:
                return [] #No stack, so no current definition could be found, so there are no quality changes either.
            machine_definition = global_stack.definition

        result = self.findAllQualityChangesForMachine(machine_definition)
        result = [quality_change for quality_change in result if quality_change.getName() == quality_changes_name]
        return result

    ##  Fetch the list of available quality types for this combination of machine definition and materials.
    #
    #   \param machine_definition \type{DefinitionContainer}
    #   \param material_containers \type{List[InstanceContainer]}
    #   \return \type{List[str]}
    def findAllQualityTypesForMachineAndMaterials(self, machine_definition: "DefinitionContainerInterface", material_containers: List[InstanceContainer]) -> List[str]:
        # Determine the common set of quality types which can be
        # applied to all of the materials for this machine.
        quality_type_dict = self.__fetchQualityTypeDictForMaterial(machine_definition, material_containers[0])
        common_quality_types = set(quality_type_dict.keys())
        for material_container in material_containers[1:]:
            next_quality_type_dict = self.__fetchQualityTypeDictForMaterial(machine_definition, material_container)
            common_quality_types.intersection_update(set(next_quality_type_dict.keys()))

        return list(common_quality_types)

    def findAllQualitiesForMachineAndMaterials(self, machine_definition: "DefinitionContainerInterface", material_containers: List[InstanceContainer]) -> List[InstanceContainer]:
        # Determine the common set of quality types which can be
        # applied to all of the materials for this machine.
        quality_type_dict = self.__fetchQualityTypeDictForMaterial(machine_definition, material_containers[0])
        qualities = set(quality_type_dict.values())
        for material_container in material_containers[1:]:
            next_quality_type_dict = self.__fetchQualityTypeDictForMaterial(machine_definition, material_container)
            qualities.intersection_update(set(next_quality_type_dict.values()))

        return list(qualities)

    ##  Fetches a dict of quality types names to quality profiles for a combination of machine and material.
    #
    #   \param machine_definition \type{DefinitionContainer} the machine definition.
    #   \param material \type{InstanceContainer} the material.
    #   \return \type{Dict[str, InstanceContainer]} the dict of suitable quality type names mapping to qualities.
    def __fetchQualityTypeDictForMaterial(self, machine_definition: "DefinitionContainerInterface", material: InstanceContainer) -> Dict[str, InstanceContainer]:
        qualities = self.findAllQualitiesForMachineMaterial(machine_definition, material)
        quality_type_dict = {}
        for quality in qualities:
            quality_type_dict[quality.getMetaDataEntry("quality_type")] = quality
        return quality_type_dict

    ##  Find a quality container by quality type.
    #
    #   \param quality_type \type{str} the name of the quality type to search for.
    #   \param machine_definition (Optional) \type{InstanceContainer} If nothing is
    #                               specified then the currently selected machine definition is used.
    #   \param material_containers (Optional) \type{List[InstanceContainer]} If nothing is specified then
    #                               the current set of selected materials is used.
    #   \return the matching quality container \type{InstanceContainer}
    def findQualityByQualityType(self, quality_type: str, machine_definition: Optional["DefinitionContainerInterface"] = None, material_containers: List[InstanceContainer] = None, **kwargs) -> InstanceContainer:
        criteria = kwargs
        criteria["type"] = "quality"
        if quality_type:
            criteria["quality_type"] = quality_type
        result = self._getFilteredContainersForStack(machine_definition, material_containers, **criteria)
        # Fall back to using generic materials and qualities if nothing could be found.
        if not result and material_containers and len(material_containers) == 1:
            basic_materials = self._getBasicMaterials(material_containers[0])
            if basic_materials:
                result = self._getFilteredContainersForStack(machine_definition, basic_materials, **criteria)
        return result[0] if result else None

    ##  Find all suitable qualities for a combination of machine and material.
    #
    #   \param machine_definition \type{DefinitionContainer} the machine definition.
    #   \param material_container \type{InstanceContainer} the material.
    #   \return \type{List[InstanceContainer]} the list of suitable qualities.
    def findAllQualitiesForMachineMaterial(self, machine_definition: "DefinitionContainerInterface", material_container: InstanceContainer) -> List[InstanceContainer]:
        criteria = {"type": "quality"}
        result = self._getFilteredContainersForStack(machine_definition, [material_container], **criteria)
        if not result:
            basic_materials = self._getBasicMaterials(material_container)
            if basic_materials:
                result = self._getFilteredContainersForStack(machine_definition, basic_materials, **criteria)

        return result

    ##  Find all quality changes for a machine.
    #
    #   \param machine_definition \type{DefinitionContainer} the machine definition.
    #   \return \type{List[InstanceContainer]} the list of quality changes
    def findAllQualityChangesForMachine(self, machine_definition: "DefinitionContainerInterface") -> List[InstanceContainer]:
        if machine_definition.getMetaDataEntry("has_machine_quality"):
            definition_id = machine_definition.getId()
        else:
            definition_id = "fdmprinter"

        filter_dict = { "type": "quality_changes", "definition": definition_id }
        quality_changes_list = ContainerRegistry.getInstance().findInstanceContainers(**filter_dict)
        return quality_changes_list

    def findAllExtruderDefinitionsForMachine(self, machine_definition: "DefinitionContainerInterface") -> List["DefinitionContainerInterface"]:
        filter_dict = { "machine": machine_definition.getId() }
        return ContainerRegistry.getInstance().findDefinitionContainers(**filter_dict)

    ##  Find all quality changes for a given extruder.
    #
    #   \param extruder_definition The extruder to find the quality changes for.
    #   \return The list of quality changes for the given extruder.
    def findAllQualityChangesForExtruder(self, extruder_definition: "DefinitionContainerInterface") -> List[InstanceContainer]:
        filter_dict = {"type": "quality_changes", "extruder": extruder_definition.getId()}
        return ContainerRegistry.getInstance().findInstanceContainers(**filter_dict)

    ##  Find all usable qualities for a machine and extruders.
    #
    #   Finds all of the qualities for this combination of machine and extruders.
    #   Only one quality per quality type is returned. i.e. if there are 2 qualities with quality_type=normal
    #   then only one of then is returned (at random).
    #
    #   \param global_container_stack \type{GlobalStack} the global machine definition
    #   \param extruder_stacks \type{List[ExtruderStack]} the list of extruder stacks
    #   \return \type{List[InstanceContainer]} the list of the matching qualities. The quality profiles
    #       return come from the first extruder in the given list of extruders.
    def findAllUsableQualitiesForMachineAndExtruders(self, global_container_stack: "GlobalStack", extruder_stacks: List["ExtruderStack"]) -> List[InstanceContainer]:
        global_machine_definition = global_container_stack.getBottom()

        machine_manager = Application.getInstance().getMachineManager()
        active_stack_id = machine_manager.activeStackId

        materials = []

        for stack in extruder_stacks:
            if stack.getId() == active_stack_id and machine_manager.newMaterial:
                materials.append(machine_manager.newMaterial)
            else:
                materials.append(stack.material)

        quality_types = self.findAllQualityTypesForMachineAndMaterials(global_machine_definition, materials)

        # Map the list of quality_types to InstanceContainers
        qualities = self.findAllQualitiesForMachineMaterial(global_machine_definition, materials[0])
        quality_type_dict = {}
        for quality in qualities:
            quality_type_dict[quality.getMetaDataEntry("quality_type")] = quality

        return [quality_type_dict[quality_type] for quality_type in quality_types]

    ##  Fetch more basic versions of a material.
    #
    #   This tries to find a generic or basic version of the given material.
    #   \param material_container \type{InstanceContainer} the material
    #   \return \type{List[InstanceContainer]} a list of the basic materials or an empty list if one could not be found.
    def _getBasicMaterials(self, material_container: InstanceContainer):
        base_material = material_container.getMetaDataEntry("material")
        material_container_definition = material_container.getDefinition()
        if material_container_definition and material_container_definition.getMetaDataEntry("has_machine_quality"):
            definition_id = material_container.getDefinition().getMetaDataEntry("quality_definition", material_container.getDefinition().getId())
        else:
            definition_id = "fdmprinter"
        if base_material:
            # There is a basic material specified
            criteria = { "type": "material", "name": base_material, "definition": definition_id }
            containers = ContainerRegistry.getInstance().findInstanceContainers(**criteria)
            containers = [basic_material for basic_material in containers if
                               basic_material.getMetaDataEntry("variant") == material_container.getMetaDataEntry(
                                   "variant")]
            return containers

        return []

    def _getFilteredContainers(self, **kwargs):
        return self._getFilteredContainersForStack(None, None, **kwargs)

    def _getFilteredContainersForStack(self, machine_definition: "DefinitionContainerInterface" = None, material_containers: List[InstanceContainer] = None, **kwargs):
        # Fill in any default values.
        if machine_definition is None:
            machine_definition = Application.getInstance().getGlobalContainerStack().getBottom()
            quality_definition_id = machine_definition.getMetaDataEntry("quality_definition")
            if quality_definition_id is not None:
                machine_definition = ContainerRegistry.getInstance().findDefinitionContainers(id=quality_definition_id)[0]

        # for convenience
        if material_containers is None:
            material_containers = []

        if not material_containers:
            active_stacks = ExtruderManager.getInstance().getActiveGlobalAndExtruderStacks()
            if active_stacks:
                material_containers = [stack.material for stack in active_stacks]

        criteria = kwargs
        filter_by_material = False

        machine_definition = self.getParentMachineDefinition(machine_definition)
        criteria["definition"] = machine_definition.getId()
        found_containers_with_machine_definition = ContainerRegistry.getInstance().findInstanceContainers(**criteria)
        whole_machine_definition = self.getWholeMachineDefinition(machine_definition)
        if whole_machine_definition.getMetaDataEntry("has_machine_quality"):
            definition_id = machine_definition.getMetaDataEntry("quality_definition", whole_machine_definition.getId())
            criteria["definition"] = definition_id

            filter_by_material = whole_machine_definition.getMetaDataEntry("has_materials")
        # only fall back to "fdmprinter" when there is no container for this machine
        elif not found_containers_with_machine_definition:
            criteria["definition"] = "fdmprinter"

        # Stick the material IDs in a set
        material_ids = set()

        for material_instance in material_containers:
            if material_instance is not None:
                # Add the parent material too.
                for basic_material in self._getBasicMaterials(material_instance):
                    material_ids.add(basic_material.getId())
                material_ids.add(material_instance.getId())
        containers = ContainerRegistry.getInstance().findInstanceContainers(**criteria)

        result = []
        for container in containers:
            # If the machine specifies we should filter by material, exclude containers that do not match any active material.
            if filter_by_material and container.getMetaDataEntry("material") not in material_ids and "global_quality" not in kwargs:
                continue
            result.append(container)

        return result

    ##  Get the parent machine definition of a machine definition.
    #
    #    \param machine_definition \type{DefinitionContainer} This may be a normal machine definition or
    #               an extruder definition.
    #    \return  \type{DefinitionContainer} the parent machine definition. If the given machine
    #               definition doesn't have a parent then it is simply returned.
    def getParentMachineDefinition(self, machine_definition: "DefinitionContainerInterface") -> "DefinitionContainerInterface":
        container_registry = ContainerRegistry.getInstance()

        machine_entry = machine_definition.getMetaDataEntry("machine")
        if machine_entry is None:
            # We have a normal (whole) machine defintion
            quality_definition = machine_definition.getMetaDataEntry("quality_definition")
            if quality_definition is not None:
                parent_machine_definition = container_registry.findDefinitionContainers(id=quality_definition)[0]
                return self.getParentMachineDefinition(parent_machine_definition)
            else:
                return machine_definition
        else:
            # This looks like an extruder. Find the rest of the machine.
            whole_machine = container_registry.findDefinitionContainers(id=machine_entry)[0]
            parent_machine = self.getParentMachineDefinition(whole_machine)
            if whole_machine is parent_machine:
                # This extruder already belongs to a 'parent' machine def.
                return machine_definition
            else:
                # Look up the corresponding extruder definition in the parent machine definition.
                extruder_position = machine_definition.getMetaDataEntry("position")
                parent_extruder_id = parent_machine.getMetaDataEntry("machine_extruder_trains")[extruder_position]
                return container_registry.findDefinitionContainers(id=parent_extruder_id)[0]

    ##  Get the whole/global machine definition from an extruder definition.
    #
    #    \param machine_definition \type{DefinitionContainer} This may be a normal machine definition or
    #               an extruder definition.
    #    \return \type{DefinitionContainerInterface}
    def getWholeMachineDefinition(self, machine_definition: "DefinitionContainerInterface") -> "DefinitionContainerInterface":
        machine_entry = machine_definition.getMetaDataEntry("machine")
        if machine_entry is None:
            # This already is a 'global' machine definition.
            return machine_definition
        else:
            container_registry = ContainerRegistry.getInstance()
            whole_machine = container_registry.findDefinitionContainers(id=machine_entry)[0]
            return whole_machine
