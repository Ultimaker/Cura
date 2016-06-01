# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import re #To parse container registry names to increment the duplicates-resolving number.

import UM.Application #To link the stack to the global container stack.
import UM.Settings.ContainerRegistry #To search for nozzles, materials, etc.
import UM.Settings.ContainerStack #To create a container stack for this extruder.

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
        self._container_stack = UM.Settings.ContainerStack(self._uniqueName(self._definition.getId()))
        self._container_stack.addMetaDataEntry("type", "extruder_train")
        self._container_stack.addContainer(self._definition)

        #Find the nozzle to use for this extruder.
        self._nozzle = container_registry.getEmptyInstanceContainer()
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
        all_qualities = container_registry.findInstanceContainers(type = "quality")
        if len(all_qualities) >= 1:
            self._quality = all_qualities[0]
        preferred_quality_id = self._definition.getMetaDataEntry("preferred_quality")
        if preferred_quality_id:
            preferred_quality = container_registry.findInstanceContainers(type = "quality", id = preferred_quality_id.lower())
            if len(preferred_quality) >= 1:
                self._quality = preferred_quality[0]
        self._container_stack.addContainer(self._quality)

        self._container_stack.setNextStack(UM.Application.getInstance().getGlobalContainerStack())

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