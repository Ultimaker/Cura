# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.ContainerRegistry import ContainerRegistry

from .GlobalStack import GlobalStack
from .ExtruderStack import ExtruderStack

class CuraStackBuilder:
    @staticmethod
    def createExtruderStack(new_stack_id: str, definition_id: str, **kwargs) -> ExtruderStack:
        registry = ContainerRegistry.getInstance()

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
