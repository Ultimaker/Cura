# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import re #To parse container registry names to increment the duplicates-resolving number.

import UM.Application #To link the stack to the global container stack.
import UM.Logger
import UM.Settings.ContainerRegistry #To search for nozzles, materials, etc.
import UM.Settings.ContainerStack #To create a container stack for this extruder.
import UM.Signal #To notify people of changing extruder stacks.

class Extruder:
    ##  Creates a new extruder from the specified definition container.
    #
    #   \param definition The definition container defining this extruder.
    def __init__(self, definition):
        self._definition = definition

        container_registry = UM.Settings.ContainerRegistry.getInstance()

        #Find the nozzles that fit on this extruder.
        self._nozzles = container_registry.findInstanceContainers(type = "nozzle", definitions = "*," + self._definition.getId() + ",*") #Extruder needs to be delimited by either a comma or the end of string.
        self._nozzles += container_registry.findInstanceContainers(type = "nozzle", definitions = "*," + self._definition.getId())
        self._nozzles += container_registry.findInstanceContainers(type = "nozzle", definitions = self._definition.getId() + ",*")
        self._nozzles += container_registry.findInstanceContainers(type = "nozzle", definitions = self._definition.getId())

        #Create a container stack for this extruder.
        self._name = self._uniqueName(self._definition)
        self._container_stack = UM.Settings.ContainerStack(self._name)
        self._container_stack.addMetaDataEntry("type", "extruder_train")
        self._container_stack.addContainer(self._definition)

        #Find the nozzle to use for this extruder.
        self._nozzle = container_registry.getEmptyInstanceContainer()
        if self._definition.getMetaDataEntry("has_nozzles", default = "False") == "True":
            if len(self._nozzles) >= 1: #First add any extruder. Later, overwrite with preference if the preference is valid.
                self._nozzle = self._nozzles[0]
            preferred_nozzle_id = self._definition.getMetaDataEntry("preferred_nozzle")
            if preferred_nozzle_id:
                for nozzle in self._nozzles:
                    if nozzle.getId() == preferred_nozzle_id:
                        self._nozzle = nozzle
                        break
            self._container_stack.addContainer(self._nozzle)

        #Find a material to use for this nozzle.
        self._material = container_registry.getEmptyInstanceContainer()
        if self._definition.getMetaDataEntry("has_materials", default = "False") == "True":
            if self._definition.getMetaDataEntry("has_nozzle_materials", default = "False") == "True":
                all_materials = container_registry.findInstanceContainers(type = "material", nozzle = self._nozzle.getId())
            else:
                all_materials = container_registry.findInstanceContainers(type = "material")
            if len(all_materials) >= 1:
                self._material = all_materials[0]
            preferred_material_id = self._definition.getMetaDataEntry("preferred_material")
            if preferred_material_id:
                preferred_material = container_registry.findInstanceContainers(type = "material", id = preferred_material_id.lower())
                if len(preferred_material) >= 1:
                    self._material = preferred_material[0]
            self._container_stack.addContainer(self._material)

        #Find a quality to use for this extruder.
        self._quality = container_registry.getEmptyInstanceContainer()
        if self._definition.getMetaDataEntry("has_machine_quality"):
            all_qualities = container_registry.findInstanceContainers(type = "quality")
            if len(all_qualities) >= 1:
                self._quality = all_qualities[0]
            preferred_quality_id = self._definition.getMetaDataEntry("preferred_quality")
            if preferred_quality_id:
                preferred_quality = container_registry.findInstanceContainers(type = "quality", id = preferred_quality_id.lower())
                if len(preferred_quality) >= 1:
                    self._quality = preferred_quality[0]
            self._container_stack.addContainer(self._quality)

        #Add an empty user profile.
        self._user_profile = UM.Settings.InstanceContainer(self._name + "_current_settings")
        self._user_profile.addMetaDataEntry("type", "user")
        self._container_stack.addContainer(self._user_profile)
        container_registry.addContainer(self._user_profile)

        self._container_stack.setNextStack(UM.Application.getInstance().getGlobalContainerStack())

    definition_changed = UM.Signal()
    material_changed = UM.Signal()
    name_changed = UM.Signal()
    nozzle_changed = UM.Signal()
    quality_changed = UM.Signal()

    ##  Gets the definition container of this extruder.
    #
    #   \return The definition container of this extruder.
    @property
    def definition(self):
        return self._definition

    ##  Changes the definition container of this extruder.
    #
    #   \param value The new definition for this extruder.
    @definition.setter
    def definition(self, value):
        try:
            position = self._container_stack.index(self._definition)
        except ValueError: #Definition is not in the list. Big trouble!
            UM.Logger.log("e", "I've lost my old extruder definition, so I can't find where to insert the new definition.")
            return
        self._container_stack.replaceContainer(position, value)
        self._definition = value
        self.definition_changed.emit()

    ##  Gets the currently active material on this extruder.
    #
    #   \return The currently active material on this extruder.
    @property
    def material(self):
        return self._material

    ##  Changes the currently active material in this extruder.
    #
    #   \param value The new material to extrude through this extruder.
    @material.setter
    def material(self, value):
        try:
            position = self._container_stack.index(self._material)
        except ValueError: #Material is not in the list.
            UM.Logger.log("e", "I've lost my old material, so I can't find where to insert the new material.")
            return
        self._container_stack.replaceContainer(position, value)
        self._material = value
        self.material_changed.emit()

    ##  Gets the name of this extruder.
    #
    #   \return The name of this extruder.
    @property
    def name(self):
        return self._name

    ##  Changes the name of this extruder.
    #
    #   \param value The new name for this extruder.
    @name.setter
    def name(self, value):
        self._name = value
        self._container_stack.setName(value) #Also update in container stack, being defensive.
        self.name_changed.emit()

    ##  Gets the currently active nozzle on this extruder.
    #
    #   \return The currently active nozzle on this extruder.
    @property
    def nozzle(self):
        return self._nozzle

    ##  Changes the currently active nozzle on this extruder.
    #
    #   \param value The new nozzle to use with this extruder.
    @nozzle.setter
    def nozzle(self, value):
        try:
            position = self._container_stack.index(self._nozzle)
        except ValueError: #Nozzle is not in the list.
            UM.Logger.log("e", "I've lost my old nozzle, so I can't find where to insert the new nozzle.")
            return
        self._container_stack.replaceContainer(position, value)
        self._nozzle = value
        self.nozzle_changed.emit()

    ##  Gets the currently active quality on this extruder.
    #
    #   \return The currently active quality on this extruder.
    @property
    def quality(self):
        return self._quality

    ##  Changes the currently active quality to use with this extruder.
    #
    #   \param value The new quality to use with this extruder.
    @quality.setter
    def quality(self, value):
        try:
            position = self._container_stack.index(self._quality)
        except ValueError: #Quality is not in the list.
            UM.Logger.log("e", "I've lost my old quality, so I can't find where to insert the new quality.")
            return
        self._container_stack.replaceContainer(position, value)
        self._quality = value
        self.quality_changed.emit()

    ##  Finds a unique name for an extruder stack.
    #
    #   \param extruder An extruder definition to design a name for.
    #   \return A name for an extruder stack that is unique and reasonably
    #   human-readable.
    def _uniqueName(self, extruder):
        container_registry = UM.Settings.ContainerRegistry.getInstance()

        name = extruder.getName().strip()
        num_check = re.compile("(.*?)\s*#\d$").match(name)
        if num_check: #There is a number in the name.
            name = num_check.group(1) #Filter out the number.
        if name == "": #Wait, that deleted everything!
            name = "Extruder"
        unique_name = name

        i = 1
        while container_registry.findContainers(id = unique_name) or container_registry.findContainers(name = unique_name): #A container already has this name.
            i += 1 #Try next numbering.
            unique_name = "%s #%d" % (name, i) #Fill name like this: "Extruder #2".
        return unique_name