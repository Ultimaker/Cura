# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional

from UM.ConfigurationErrorMessage import ConfigurationErrorMessage
from UM.Logger import Logger
from UM.Settings.Interfaces import DefinitionContainerInterface
from UM.Settings.InstanceContainer import InstanceContainer

from cura.Machines.ContainerTree import ContainerTree
from .GlobalStack import GlobalStack
from .ExtruderStack import ExtruderStack


class CuraStackBuilder:
    """Contains helper functions to create new machines."""


    @classmethod
    def createMachine(cls, name: str, definition_id: str) -> Optional[GlobalStack]:
        """Create a new instance of a machine.

        :param name: The name of the new machine.
        :param definition_id: The ID of the machine definition to use.

        :return: The new global stack or None if an error occurred.
        """

        from cura.CuraApplication import CuraApplication
        application = CuraApplication.getInstance()
        registry = application.getContainerRegistry()
        container_tree = ContainerTree.getInstance()

        definitions = registry.findDefinitionContainers(id = definition_id)
        if not definitions:
            ConfigurationErrorMessage.getInstance().addFaultyContainers(definition_id)
            Logger.log("w", "Definition {definition} was not found!", definition = definition_id)
            return None

        machine_definition = definitions[0]
        machine_node = container_tree.machines[machine_definition.getId()]

        generated_name = registry.createUniqueName("machine", "", name, machine_definition.getName())
        # Make sure the new name does not collide with any definition or (quality) profile
        # createUniqueName() only looks at other stacks, but not at definitions or quality profiles
        # Note that we don't go for uniqueName() immediately because that function matches with ignore_case set to true
        if registry.findContainersMetadata(id = generated_name):
            generated_name = registry.uniqueName(generated_name)

        new_global_stack = cls.createGlobalStack(
            new_stack_id = generated_name,
            definition = machine_definition,
            variant_container = application.empty_variant_container,
            material_container = application.empty_material_container,
            quality_container = machine_node.preferredGlobalQuality().container,
        )
        new_global_stack.setName(generated_name)

        # Create ExtruderStacks
        extruder_dict = machine_definition.getMetaDataEntry("machine_extruder_trains")
        for position in extruder_dict:
            try:
                cls.createExtruderStackWithDefaultSetup(new_global_stack, position)
            except IndexError:
                return None

        for new_extruder in new_global_stack.extruderList:  # Only register the extruders if we're sure that all of them are correct.
            registry.addContainer(new_extruder)

        # Register the global stack after the extruder stacks are created. This prevents the registry from adding another
        # extruder stack because the global stack didn't have one yet (which is enforced since Cura 3.1).
        registry.addContainer(new_global_stack)

        return new_global_stack

    @classmethod
    def createExtruderStackWithDefaultSetup(cls, global_stack: "GlobalStack", extruder_position: int) -> None:
        """Create a default Extruder Stack

        :param global_stack: The global stack this extruder refers to.
        :param extruder_position: The position of the current extruder.
        """

        from cura.CuraApplication import CuraApplication
        application = CuraApplication.getInstance()
        registry = application.getContainerRegistry()

        # Get the extruder definition.
        extruder_definition_dict = global_stack.getMetaDataEntry("machine_extruder_trains")
        extruder_definition_id = extruder_definition_dict[str(extruder_position)]
        try:
            extruder_definition = registry.findDefinitionContainers(id = extruder_definition_id)[0]
        except IndexError:
            # It still needs to break, but we want to know what extruder ID made it break.
            msg = "Unable to find extruder definition with the id [%s]" % extruder_definition_id
            Logger.logException("e", msg)
            raise IndexError(msg)

        # Find out what filament diameter we need.
        approximate_diameter = round(extruder_definition.getProperty("material_diameter", "value"))  # Can't be modified by definition changes since we are just initialising the stack here.

        # Find the preferred containers.
        machine_node = ContainerTree.getInstance().machines[global_stack.definition.getId()]
        extruder_variant_node = machine_node.variants.get(machine_node.preferred_variant_name)
        if not extruder_variant_node:
            Logger.log("w", "Could not find preferred nozzle {nozzle_name}. Falling back to {fallback}.".format(nozzle_name = machine_node.preferred_variant_name, fallback = next(iter(machine_node.variants))))
            extruder_variant_node = next(iter(machine_node.variants.values()))
        extruder_variant_container = extruder_variant_node.container
        material_node = extruder_variant_node.preferredMaterial(approximate_diameter)
        material_container = material_node.container
        quality_node = material_node.preferredQuality()

        new_extruder_id = registry.uniqueName(extruder_definition_id)
        new_extruder = cls.createExtruderStack(
            new_extruder_id,
            extruder_definition = extruder_definition,
            machine_definition_id = global_stack.definition.getId(),
            position = extruder_position,
            variant_container = extruder_variant_container,
            material_container = material_container,
            quality_container = quality_node.container
        )
        new_extruder.setNextStack(global_stack)

        registry.addContainer(new_extruder)

    @classmethod
    def createExtruderStack(cls, new_stack_id: str, extruder_definition: DefinitionContainerInterface,
                            machine_definition_id: str,
                            position: int,
                            variant_container: "InstanceContainer",
                            material_container: "InstanceContainer",
                            quality_container: "InstanceContainer") -> ExtruderStack:

        """Create a new Extruder stack

        :param new_stack_id: The ID of the new stack.
        :param extruder_definition: The definition to base the new stack on.
        :param machine_definition_id: The ID of the machine definition to use for the user container.
        :param position: The position the extruder occupies in the machine.
        :param variant_container: The variant selected for the current extruder.
        :param material_container: The material selected for the current extruder.
        :param quality_container: The quality selected for the current extruder.

        :return: A new Extruder stack instance with the specified parameters.
        """

        from cura.CuraApplication import CuraApplication
        application = CuraApplication.getInstance()
        registry = application.getContainerRegistry()

        stack = ExtruderStack(new_stack_id)
        stack.setName(extruder_definition.getName())
        stack.setDefinition(extruder_definition)

        stack.setMetaDataEntry("position", str(position))

        user_container = cls.createUserChangesContainer(new_stack_id + "_user", machine_definition_id, new_stack_id,
                                                        is_global_stack = False)

        stack.definitionChanges = cls.createDefinitionChangesContainer(stack, new_stack_id + "_settings")
        stack.variant = variant_container
        stack.material = material_container
        stack.quality = quality_container
        stack.intent = application.empty_intent_container
        stack.qualityChanges = application.empty_quality_changes_container
        stack.userChanges = user_container

        # Only add the created containers to the registry after we have set all the other
        # properties. This makes the create operation more transactional, since any problems
        # setting properties will not result in incomplete containers being added.
        registry.addContainer(user_container)

        return stack

    @classmethod
    def createGlobalStack(cls, new_stack_id: str, definition: DefinitionContainerInterface,
                          variant_container: "InstanceContainer",
                          material_container: "InstanceContainer",
                          quality_container: "InstanceContainer") -> GlobalStack:

        """Create a new Global stack

        :param new_stack_id: The ID of the new stack.
        :param definition: The definition to base the new stack on.
        :param variant_container: The variant selected for the current stack.
        :param material_container: The material selected for the current stack.
        :param quality_container: The quality selected for the current stack.

        :return: A new Global stack instance with the specified parameters.
        """

        from cura.CuraApplication import CuraApplication
        application = CuraApplication.getInstance()
        registry = application.getContainerRegistry()

        stack = GlobalStack(new_stack_id)
        stack.setDefinition(definition)

        # Create user container
        user_container = cls.createUserChangesContainer(new_stack_id + "_user", definition.getId(), new_stack_id,
                                                        is_global_stack = True)

        stack.definitionChanges = cls.createDefinitionChangesContainer(stack, new_stack_id + "_settings")
        stack.variant = variant_container
        stack.material = material_container
        stack.quality = quality_container
        stack.intent = application.empty_intent_container
        stack.qualityChanges = application.empty_quality_changes_container
        stack.userChanges = user_container

        registry.addContainer(user_container)

        return stack

    @classmethod
    def createUserChangesContainer(cls, container_name: str, definition_id: str, stack_id: str,
                                   is_global_stack: bool) -> "InstanceContainer":
        from cura.CuraApplication import CuraApplication
        application = CuraApplication.getInstance()
        registry = application.getContainerRegistry()

        unique_container_name = registry.uniqueName(container_name)

        container = InstanceContainer(unique_container_name)
        container.setDefinition(definition_id)
        container.setMetaDataEntry("type", "user")
        container.setMetaDataEntry("setting_version", CuraApplication.SettingVersion)

        metadata_key_to_add = "machine" if is_global_stack else "extruder"
        container.setMetaDataEntry(metadata_key_to_add, stack_id)

        return container

    @classmethod
    def createDefinitionChangesContainer(cls, container_stack, container_name):
        from cura.CuraApplication import CuraApplication
        application = CuraApplication.getInstance()
        registry = application.getContainerRegistry()

        unique_container_name = registry.uniqueName(container_name)

        definition_changes_container = InstanceContainer(unique_container_name)
        definition_changes_container.setDefinition(container_stack.getBottom().getId())
        definition_changes_container.setMetaDataEntry("type", "definition_changes")
        definition_changes_container.setMetaDataEntry("setting_version", CuraApplication.SettingVersion)

        registry.addContainer(definition_changes_container)
        container_stack.definitionChanges = definition_changes_container

        return definition_changes_container
