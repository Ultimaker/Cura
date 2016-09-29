# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import UM.Application
import cura.Settings.ExtruderManager
import UM.Settings.ContainerRegistry

# This collects a lot of quality and quality changes related code which was split between ContainerManager
# and the MachineManager and really needs to usable from both.

class QualityManager:

    ##  Get the singleton instance for this class.
    @classmethod
    def getInstance(cls):
        # Note: Explicit use of class name to prevent issues with inheritance.
        if QualityManager.__instance is None:
            QualityManager.__instance = cls()
        return QualityManager.__instance

    __instance = None

    ##  Find a quality by name for a specific machine definition and materials.
    #
    #   \param quality_name
    #   \param machine_definition (Optional) \type{ContainerInstance} If nothing is
    #                               specified then the currently selected machine definition is used.
    #   \param material_containers (Optional) \type{List[ContainerInstance]} If nothing is specified then
    #                               the current set of selected materials is used.
    #   \return the matching quality containers \type{List[ContainerInstance]}
    def findQualityByName(self, quality_name, machine_definition=None, material_containers=None):
        criteria = {"type": "quality", "name": quality_name}
        return self._getFilteredContainersForStack(machine_definition, material_containers, **criteria)

    ##  Find a quality changes container by name.
    #
    #   \param quality_changes_name \type{str} the name of the quality changes container.
    #   \param machine_definition (Optional) \type{ContainerInstance} If nothing is
    #                               specified then the currently selected machine definition is used.
    #   \param material_containers (Optional) \type{List[ContainerInstance]} If nothing is specified then
    #                               the current set of selected materials is used.
    #   \return the matching quality changes containers \type{List[ContainerInstance]}
    def findQualityChangesByName(self, quality_changes_name, machine_definition=None):
        criteria = {"type": "quality_changes", "name": quality_changes_name}
        return self._getFilteredContainersForStack(machine_definition, [], **criteria)

    ##  Find a quality container by quality type.
    #
    #   \param quality_type \type{str} the name of the quality type to search for.
    #   \param machine_definition (Optional) \type{ContainerInstance} If nothing is
    #                               specified then the currently selected machine definition is used.
    #   \param material_containers (Optional) \type{List[ContainerInstance]} If nothing is specified then
    #                               the current set of selected materials is used.
    #   \return the matching quality containers \type{List[ContainerInstance]}
    def findQualityByQualityType(self, quality_type, machine_definition=None, material_containers=None):
        criteria = {"type": "quality", "quality_type": quality_type}
        return self._getFilteredContainersForStack(machine_definition, material_containers, **criteria)

    def _getFilteredContainers(self, **kwargs):
        return self._getFilteredContainersForStack(None, None, **kwargs)

    def _getFilteredContainersForStack(self, machine_definition=None, material_containers=None, **kwargs):
        # Fill in any default values.
        if machine_definition is None:
            machine_definition = UM.Application.getInstance().getGlobalContainerStack().getBottom()
            quality_definition_id = machine_definition.getMetaDataEntry("quality_definition")
            if quality_definition_id is not None:
                machine_definition = UM.Settings.ContainerRegistry.getInstance().findDefinitionContainers(id=quality_definition_id)[0]

        if material_containers is None:
            active_stacks = cura.Settings.ExtruderManager.getInstance().getActiveGlobalAndExtruderStacks()
            material_containers = [stack.findContainer(type="material") for stack in active_stacks]

        criteria = kwargs
        filter_by_material = False

        machine_definition = self.getParentMachineDefinition(machine_definition)
        whole_machine_definition = self.getWholeMachineDefinition(machine_definition)
        if whole_machine_definition.getMetaDataEntry("has_machine_quality"):
            definition_id = machine_definition.getMetaDataEntry("quality_definition", whole_machine_definition.getId())
            criteria["definition"] = definition_id

            filter_by_material = whole_machine_definition.getMetaDataEntry("has_materials")
        else:
            criteria["definition"] = "fdmprinter"

        # Stick the material IDs in a set
        if material_containers is None or len(material_containers) == 0:
            filter_by_material = False
        else:
            material_ids = set()
            for material_instance in material_containers:
                material_ids.add(material_instance.getId())


        if machine_definition.getMetaDataEntry("type") == "extruder":
            extruder_id = machine_definition.getId()
        else:
            extruder_id = None

        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(**criteria)

        result = []
        for container in containers:
            # If the machine specifies we should filter by material, exclude containers that do not match any active material.
            if filter_by_material and container.getMetaDataEntry("material") not in material_ids:
                continue
            if extruder_id != container.getMetaDataEntry("extruder"):
                continue
            result.append(container)
        return result

    ##  Get the parent machine definition of a machine definition.
    #
    #    \param machine_definition \type{DefinitionContainer} This may be a normal machine definition or
    #               an extruder definition.
    #    \return  \type{DefinitionContainer} the parent machine definition. If the given machine
    #               definition doesn't have a parent then it is simply returned.
    def getParentMachineDefinition(self, machine_definition):
        container_registry = UM.Settings.ContainerRegistry.getInstance()

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
    #    \return \type{DefinitionContainer}
    def getWholeMachineDefinition(self, machine_definition):
        machine_entry = machine_definition.getMetaDataEntry("machine")
        if machine_entry is None:
            # This already is a 'global' machine definition.
            return machine_definition
        else:
            container_registry = UM.Settings.ContainerRegistry.getInstance()
            whole_machine = container_registry.findDefinitionContainers(id=machine_entry)[0]
            return whole_machine
