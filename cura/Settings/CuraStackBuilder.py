# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Logger import Logger

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
        stack.setDefinition(definition)
        stack.addMetaDataEntry("position", definition.getMetaDataEntry("position"))

        user_container = InstanceContainer(new_stack_id + "_user")
        user_container.addMetaDataEntry("type", "user")
        user_container.addMetaDataEntry("extruder", new_stack_id)

        stack.setUserChanges(user_container)

        if "next_stack" in kwargs:
            stack.setNextStack(kwargs["next_stack"])

        # Important! The order here matters, because that allows functions like __setStackQuality to
        # assume the material and variant have already been set.
        if "definition_changes" in kwargs:
            stack.setDefinitionChangesById(kwargs["definition_changes"])

        if "variant" in kwargs:
            cls.__setStackVariant(stack, kwargs["variant"])

        if "material" in kwargs:
            cls.__setStackMaterial(stack, kwargs["material"])

        if "quality" in kwargs:
            cls.__setStackQuality(stack, kwargs["quality"])

        if "quality_changes" in kwargs:
            stack.setQualityChangesById(kwargs["quality_changes"])

        # Only add the created containers to the registry after we have set all the other
        # properties. This makes the create operation more transactional, since any problems
        # setting properties will not result in incomplete containers being added.
        cls.__registry.addContainer(stack)
        cls.__registry.addContainer(user_container)

        return stack

    @classmethod
    def createGlobalStack(cls, new_stack_id: str, definition: DefinitionContainer, **kwargs) -> GlobalStack:
        cls.__registry = ContainerRegistry.getInstance()

        stack = GlobalStack(new_stack_id)
        stack.setDefinition(definition)

        user_container = InstanceContainer(new_stack_id + "_user")
        user_container.addMetaDataEntry("type", "user")
        user_container.addMetaDataEntry("machine", new_stack_id)
        user_container.setDefinition(definition)

        stack.setUserChanges(user_container)

        # Important! The order here matters, because that allows functions like __setStackQuality to
        # assume the material and variant have already been set.
        if "definition_changes" in kwargs:
            stack.setDefinitionChangesById(kwargs["definition_changes"])

        if "variant" in kwargs:
            cls.__setStackVariant(stack, kwargs["variant"])

        if "material" in kwargs:
            cls.__setStackMaterial(stack, kwargs["material"])

        if "quality" in kwargs:
            cls.__setStackQuality(stack, kwargs["quality"])

        if "quality_changes" in kwargs:
            stack.setQualityChangesById(kwargs["quality_changes"])

        cls.__registry.addContainer(stack)
        cls.__registry.addContainer(user_container)

        return stack

    # Convenience variable
    # It should get set before any private functions are called so the privates do not need to
    # re-get the container registry.
    __registry = None # type: ContainerRegistry

    @classmethod
    def __setStackQuality(cls, stack: CuraContainerStack, quality_id: str, machine_definition: DefinitionContainer) -> None:
        if quality_id != "default":
            # Specific quality ID specified, so use that.
            stack.setQualityById(quality_id)
            return

        quality = None

        container_registry = ContainerRegistry.getInstance()
        search_criteria = { "type": "quality" }

        if definition.getMetaDataEntry("has_machine_quality"):
            search_criteria["definition"] = self.getQualityDefinitionId(definition)

            if definition.getMetaDataEntry("has_materials") and material_container:
                search_criteria["material"] = material_container.id
        else:
            search_criteria["definition"] = "fdmprinter"

        if preferred_quality_name and preferred_quality_name != "empty":
            search_criteria["name"] = preferred_quality_name
        else:
            preferred_quality = definition.getMetaDataEntry("preferred_quality")
            if preferred_quality:
                search_criteria["id"] = preferred_quality

        containers = container_registry.findInstanceContainers(**search_criteria)
        if containers:
            return containers[0]

        if "material" in search_criteria:
            # First check if we can solve our material not found problem by checking if we can find quality containers
            # that are assigned to the parents of this material profile.
            try:
                inherited_files = material_container.getInheritedFiles()
            except AttributeError:  # Material_container does not support inheritance.
                inherited_files = []

            if inherited_files:
                for inherited_file in inherited_files:
                    # Extract the ID from the path we used to load the file.
                    search_criteria["material"] = os.path.basename(inherited_file).split(".")[0]
                    containers = container_registry.findInstanceContainers(**search_criteria)
                    if containers:
                        return containers[0]
            # We still weren't able to find a quality for this specific material.
            # Try to find qualities for a generic version of the material.
            material_search_criteria = { "type": "material", "material": material_container.getMetaDataEntry("material"), "color_name": "Generic"}
            if definition.getMetaDataEntry("has_machine_quality"):
                if material_container:
                    material_search_criteria["definition"] = material_container.getDefinition().id

                    if definition.getMetaDataEntry("has_variants"):
                        material_search_criteria["variant"] = material_container.getMetaDataEntry("variant")
                else:
                    material_search_criteria["definition"] = self.getQualityDefinitionId(definition)

                    if definition.getMetaDataEntry("has_variants") and variant_container:
                        material_search_criteria["variant"] = self.getQualityVariantId(definition, variant_container)
            else:
                material_search_criteria["definition"] = "fdmprinter"
            material_containers = container_registry.findInstanceContainers(**material_search_criteria)
            # Try all materials to see if there is a quality profile available.
            for material_container in material_containers:
                search_criteria["material"] = material_container.getId()

                containers = container_registry.findInstanceContainers(**search_criteria)
                if containers:
                    return containers[0]

        if "name" in search_criteria or "id" in search_criteria:
            # If a quality by this name can not be found, try a wider set of search criteria
            search_criteria.pop("name", None)
            search_criteria.pop("id", None)

            containers = container_registry.findInstanceContainers(**search_criteria)
            if containers:
                return containers[0]

        # Notify user that we were unable to find a matching quality
        message = Message(catalog.i18nc("@info:status", "Unable to find a quality profile for this combination. Default settings will be used instead."))
        message.show()
        return self._empty_quality_container

    @classmethod
    def __setStackMaterial(cls, stack: CuraContainerStack, material_id: str, machine_definition: DefinitionContainer) -> None:
        if not machine_definition.getMetaDataEntry("has_materials"):
            # Machine does not use materials, never try to set it.
            return

        if material_id != "default":
            # Specific material ID specified, so use that.
            stack.setMaterialById(material_id)
            return

        # If material_id is "default", find a default material to use for this stack.
        # First add any material. Later, overwrite with preference if the preference is valid.
        material = None
        search_criteria = { "type": "material" }
        if machine_definition.getMetaDataEntry("has_machine_materials"):
            search_criteria["definition"] = cls.__findInstanceContainerDefinitionId(machine_definition)

            if machine_definition.getMetaDataEntry("has_variants"):
                search_criteria["variant"] = stack.variant.id
        else:
            search_criteria["definition"] = "fdmprinter"

        preferred_material = machine_definition.getMetaDataEntry("preferred_material")
        if preferred_material:
            search_criteria["id"] = preferred_material

        materials = cls.__registry.findInstanceContainers(**search_criteria)
        if not materials:
            Logger.log("w", "The preferred material \"{material}\" could not be found for stack {stack}", material = preferred_material, stack = stack.id)
            search_criteria.pop("variant", None)
            search_criteria.pop("id", None)
            materials = cls.__registry.findInstanceContainers(**search_criteria)

        if materials:
            stack.setMaterial(materials[0])
        else:
            Logger.log("w", "Could not find a valid material for stack {stack}", stack = stack.id)

    @classmethod
    def __setStackVariant(cls, stack: CuraContainerStack, variant_id: str, machine_definition: DefinitionContainer) -> None:
        if not machine_definition.getMetaDataEntry("has_variants"):
            # If the machine does not use variants, we should never set a variant.
            return

        if variant_id != "default":
            # If we specify a specific variant ID, use that and do nothing else.
            stack.setVariantById(variant_id)
            return

        # When the id is "default", look up the variant based on machine definition etc.
        # First add any variant. Later, overwrite with preference if the preference is valid.
        variant = None

        definition_id = cls.__findInstanceContainerDefinitionId(machine_definition.id)
        variants = cls.__registry.findInstanceContainers(definition = definition_id, type = "variant")
        if variants:
            variant = variants[0]

        preferred_variant_id = machine_definition.getMetaDataEntry("preferred_variant")
        if preferred_variant_id:
            preferred_variants = cls.__registry.findInstanceContainers(id = preferred_variant_id, definition = definition_id, type = "variant")
            if len(preferred_variants) >= 1:
                variant = preferred_variants[0]
            else:
                Logger.log("w", "The preferred variant \"{variant}\" of stack {stack} does not exist or is not a variant.", variant = preferred_variant_id, stack = stack.id)
                # And leave it at the default variant.

        if variant:
            stack.setVariant(variant)
        else:
            Logger.log("w", "Could not find a valid default variant for stack {stack}", stack = stack.id)

    ##  Find the ID that should be used when searching for instance containers for a specified definition.
    #
    #   This handles the situation where the definition specifies we should use a different definition when
    #   searching for instance containers.
    #
    #   \param machine_definition The definition to find the "quality definition" for.
    #
    #   \return The ID of the definition container to use when searching for instance containers.
    @classmethod
    def __findInstanceContainerDefinitionId(cls, machine_definition: DefinitionContainer) -> str:
        quality_definition = machine_definition.getMetaDataEntry("quality_definition")
        if not quality_definition:
            return machine_definition.id

        definitions = cls.__registry.findDefinitionContainers(id = quality_definition)
        if not definitions:
            Logger.log("w", "Unable to find parent definition {parent} for machine {machine}", parent = quality_definition, machine = machine_definition.id)
            return machine_definition.id

        return cls.__findInstanceContainerDefinitionId(definitions[0])

