# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Logger import Logger

from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.ContainerRegistry import ContainerRegistry

from .GlobalStack import GlobalStack
from .ExtruderStack import ExtruderStack
from typing import Optional


##  Contains helper functions to create new machines.
class CuraStackBuilder:
    ##  Create a new instance of a machine.
    #
    #   \param name The name of the new machine.
    #   \param definition_id The ID of the machine definition to use.
    #
    #   \return The new global stack or None if an error occurred.
    @classmethod
    def createMachine(cls, name: str, definition_id: str) -> Optional[GlobalStack]:
        registry = ContainerRegistry.getInstance()
        definitions = registry.findDefinitionContainers(id = definition_id)
        if not definitions:
            Logger.log("w", "Definition {definition} was not found!", definition = definition_id)
            return None

        machine_definition = definitions[0]

        generated_name = registry.createUniqueName("machine", "", name, machine_definition.name)
        # Make sure the new name does not collide with any definition or (quality) profile
        # createUniqueName() only looks at other stacks, but not at definitions or quality profiles
        # Note that we don't go for uniqueName() immediately because that function matches with ignore_case set to true
        if registry.findContainers(id = generated_name):
            generated_name = registry.uniqueName(generated_name)

        new_global_stack = cls.createGlobalStack(
            new_stack_id = generated_name,
            definition = machine_definition,
            quality = "default",
            material = "default",
            variant = "default",
        )

        new_global_stack.setName(generated_name)

        extruder_definition = registry.findDefinitionContainers(machine = machine_definition.getId())

        if not extruder_definition:
            # create extruder stack for single extrusion machines that have no separate extruder definition files
            extruder_definition = registry.findDefinitionContainers(id = "fdmextruder")[0]
            new_extruder_id = registry.uniqueName(machine_definition.getName() + " " + extruder_definition.id)
            new_extruder = cls.createExtruderStack(
                new_extruder_id,
                definition=extruder_definition,
                machine_definition=machine_definition,
                quality="default",
                material="default",
                variant="default",
                next_stack=new_global_stack
            )
            new_global_stack.addExtruder(new_extruder)
        else:
            # create extruder stack for each found extruder definition
            for extruder_definition in registry.findDefinitionContainers(machine = machine_definition.id):
                position = extruder_definition.getMetaDataEntry("position", None)
                if not position:
                    Logger.log("w", "Extruder definition %s specifies no position metadata entry.", extruder_definition.id)

                new_extruder_id = registry.uniqueName(extruder_definition.id)
                new_extruder = cls.createExtruderStack(
                    new_extruder_id,
                    definition = extruder_definition,
                    machine_definition = machine_definition,
                    quality = "default",
                    material = "default",
                    variant = "default",
                    next_stack = new_global_stack
                )
                new_global_stack.addExtruder(new_extruder)

        return new_global_stack

    ##  Create a new Extruder stack
    #
    #   \param new_stack_id The ID of the new stack.
    #   \param definition The definition to base the new stack on.
    #   \param machine_definition The machine definition to use for the user container.
    #   \param kwargs You can add keyword arguments to specify IDs of containers to use for a specific type, for example "variant": "0.4mm"
    #
    #   \return A new Global stack instance with the specified parameters.
    @classmethod
    def createExtruderStack(cls, new_stack_id: str, definition: DefinitionContainer, machine_definition: DefinitionContainer, **kwargs) -> ExtruderStack:
        stack = ExtruderStack(new_stack_id)
        stack.setName(definition.getName())
        stack.setDefinition(definition)
        stack.addMetaDataEntry("position", definition.getMetaDataEntry("position"))

        if "next_stack" in kwargs:
            # Add stacks before containers are added, since they may trigger a setting update.
            stack.setNextStack(kwargs["next_stack"])

        user_container = InstanceContainer(new_stack_id + "_user")
        user_container.addMetaDataEntry("type", "user")
        user_container.addMetaDataEntry("extruder", new_stack_id)
        from cura.CuraApplication import CuraApplication
        user_container.addMetaDataEntry("setting_version", CuraApplication.SettingVersion)
        user_container.setDefinition(machine_definition)

        stack.setUserChanges(user_container)

        # Important! The order here matters, because that allows the stack to
        # assume the material and variant have already been set.
        if "definition_changes" in kwargs:
            stack.setDefinitionChangesById(kwargs["definition_changes"])
        else:
            stack.setDefinitionChanges(cls.createDefinitionChangesContainer(stack, new_stack_id + "_settings"))

        if "variant" in kwargs:
            stack.setVariantById(kwargs["variant"])

        if "material" in kwargs:
            stack.setMaterialById(kwargs["material"])

        if "quality" in kwargs:
            stack.setQualityById(kwargs["quality"])

        if "quality_changes" in kwargs:
            stack.setQualityChangesById(kwargs["quality_changes"])

        # Only add the created containers to the registry after we have set all the other
        # properties. This makes the create operation more transactional, since any problems
        # setting properties will not result in incomplete containers being added.
        registry = ContainerRegistry.getInstance()
        registry.addContainer(stack)
        registry.addContainer(user_container)

        return stack

    ##  Create a new Global stack
    #
    #   \param new_stack_id The ID of the new stack.
    #   \param definition The definition to base the new stack on.
    #   \param kwargs You can add keyword arguments to specify IDs of containers to use for a specific type, for example "variant": "0.4mm"
    #
    #   \return A new Global stack instance with the specified parameters.
    @classmethod
    def createGlobalStack(cls, new_stack_id: str, definition: DefinitionContainer, **kwargs) -> GlobalStack:
        stack = GlobalStack(new_stack_id)
        stack.setDefinition(definition)

        user_container = InstanceContainer(new_stack_id + "_user")
        user_container.addMetaDataEntry("type", "user")
        user_container.addMetaDataEntry("machine", new_stack_id)
        from cura.CuraApplication import CuraApplication
        user_container.addMetaDataEntry("setting_version", CuraApplication.SettingVersion)
        user_container.setDefinition(definition)

        stack.setUserChanges(user_container)

        # Important! The order here matters, because that allows the stack to
        # assume the material and variant have already been set.
        if "definition_changes" in kwargs:
            stack.setDefinitionChangesById(kwargs["definition_changes"])
        else:
            stack.setDefinitionChanges(cls.createDefinitionChangesContainer(stack, new_stack_id + "_settings"))

        if "variant" in kwargs:
            stack.setVariantById(kwargs["variant"])

        if "material" in kwargs:
            stack.setMaterialById(kwargs["material"])

        if "quality" in kwargs:
            stack.setQualityById(kwargs["quality"])

        if "quality_changes" in kwargs:
            stack.setQualityChangesById(kwargs["quality_changes"])

        registry = ContainerRegistry.getInstance()
        registry.addContainer(stack)
        registry.addContainer(user_container)

        return stack

    @classmethod
    def createDefinitionChangesContainer(cls, container_stack, container_name, container_index = None):
        from cura.CuraApplication import CuraApplication

        unique_container_name = ContainerRegistry.getInstance().uniqueName(container_name)

        definition_changes_container = InstanceContainer(unique_container_name)
        definition = container_stack.getBottom()
        definition_changes_container.setDefinition(definition)
        definition_changes_container.addMetaDataEntry("type", "definition_changes")
        definition_changes_container.addMetaDataEntry("setting_version", CuraApplication.SettingVersion)

        ContainerRegistry.getInstance().addContainer(definition_changes_container)
        container_stack.definitionChanges = definition_changes_container

        return definition_changes_container
