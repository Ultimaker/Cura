# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.ContainerRegistry import ContainerRegistry

from .GlobalStack import GlobalStack
from .ExtruderStack import ExtruderStack
from .CuraContainerStack import CuraContainerStack

class CuraStackBuilder:
    @classmethod
    def createMachine(cls, name: str, definition_id: str) -> GlobalStack:
        cls.__registry = ContainerRegistry.getInstance()
        definitions = cls.__registry.findDefinitionContainers(id = definition_id)
        if not definitions:
            Logger.log("w", "Definition {definition} was not found!", definition = definition_id)
            return None

        machine_definition = definitions[0]
        name = cls.__registry.createUniqueName("machine", "", name, machine_definition.name)

        new_global_stack = cls.createGlobalStack(
            new_stack_id = name,
            definition = machine_definition,
            quality = "default",
            material = "default",
            variant = "default",
        )

        for extruder_definition in cls.__registry.findDefinitionContainers(machine = machine_definition.id):
            position = extruder_definition.getMetaDataEntry("position", None)
            if not position:
                Logger.log("w", "Extruder definition %s specifies no position metadata entry.", extruder_definition.id)

            new_extruder_id = cls.__registry.uniqueName(extruder_definition.id)
            new_extruder = cls.createExtruderStack(
                new_extruder_id = new_extruder_id,
                definition = extruder_definition,
                machine_definition = machine_definition,
                quality = "default",
                material = "default",
                variant = "default",
                next_stack = new_global_stack
            )

        return new_global_stack


    @classmethod
    def createExtruderStack(cls, new_stack_id: str, definition: DefinitionContainer, machine_definition: DefinitionContainer, **kwargs) -> ExtruderStack:
        cls.__registry = ContainerRegistry.getInstance()

        stack = ExtruderStack(new_stack_id)

        user_container = InstanceContainer(new_stack_id + "_user")
        user_container.addMetaDataEntry("type", "user")
        user_container.addMetaDataEntry("machine", new_stack_id)

        stack.setUserChanges(user_container)

        if "quality_changes" in kwargs:
            stack.setQualityChangesById(kwargs["quality_changes"])

        if "quality" in kwargs:
            stack.setQualityById(kwargs["quality"])

        if "material" in kwargs:
            stack.setMaterialById(kwargs["material"])

        if "variant" in kwargs:
            stack.setVariantById(kwargs["variant"])

        if "definition_changes" in kwargs:
            stack.setDefinitionChangesById(kwargs["definition_changes"])

        if "definition" in kwargs:
            stack.setDefinitionById(kwargs["definition"])

        if "next_stack" in kwargs:
            stack.setNextStack(kwargs["next_stack"])

        # Only add the created containers to the registry after we have set all the other
        # properties. This makes the create operation more transactional, since any problems
        # setting properties will not result in incomplete containers being added.
        registry.addContainer(stack)
        registry.addContainer(user_container)

        return stack

    @staticmethod
    def createGlobalStack(new_stack_id: str, definition: DefinitionContainer, **kwargs) -> GlobalStack:
        registry = ContainerRegistry.getInstance()

        stack = GlobalStack(new_stack_id)

        stack.setDefinition(definition)

        user_container = InstanceContainer(new_stack_id + "_user")
        user_container.addMetaDataEntry("type", "user")
        user_container.addMetaDataEntry("machine", new_stack_id)
        user_container.setDefinition(definition)

        stack.setUserChanges(user_container)

        if "quality_changes" in kwargs:
            stack.setQualityChangesById(kwargs["quality_changes"])

        if "quality" in kwargs:
            stack.setQualityById(kwargs["quality"])

        if "material" in kwargs:
            stack.setMaterialById(kwargs["material"])

        if "variant" in kwargs:
            stack.setVariantById(kwargs["variant"])

        if "definition_changes" in kwargs:
            stack.setDefinitionChangesById(kwargs["definition_changes"])

        registry.addContainer(stack)
        registry.addContainer(user_container)

        return stack

    # Convenience variable
    # It should get set before any private functions are called so the privates do not need to
    # re-get the container registry.
    __registry = None # type: ContainerRegistry

