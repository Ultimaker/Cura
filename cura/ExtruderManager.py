# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import pyqtSignal, pyqtProperty, pyqtSlot, QObject #For communicating data and events to Qt.

import UM.Application #To get the global container stack to find the current machine.
import UM.Logger
import UM.Settings.ContainerRegistry #Finding containers by ID.
import re


##  Manages all existing extruder stacks.
#
#   This keeps a list of extruder stacks for each machine.
class ExtruderManager(QObject):
    ##  Signal to notify other components when the list of extruders changes.
    extrudersChanged = pyqtSignal()

    ##  Notify when the user switches the currently active extruder.
    activeExtruderChanged = pyqtSignal()

    ##  Registers listeners and such to listen to changes to the extruders.
    def __init__(self, parent = None):
        super().__init__(parent)
        self._extruder_trains = { } #Extruders for the current machine.
        self._next_item = 0 #For when you use this class as iterator.
        self._active_extruder_index = 0

        self._repopulate()

    ##  Creates an iterator over the extruders in this manager.
    #
    #   \return An iterator over the extruders in this manager.
    def __iter__(self):
        return iter(self._extruders)

    ##  Gets the unique identifier of the currently active extruder stack.
    #
    #   The currently active extruder stack is the stack that is currently being
    #   edited.
    #
    #   \return The unique ID of the currently active extruder stack.
    @pyqtProperty(str, notify = activeExtruderChanged)
    def activeExtruderStackId(self):
        if not UM.Application.getInstance().getGlobalContainerStack():
            return None #No active machine, so no active extruder.
        try:
            return self._extruder_trains[UM.Application.getInstance().getGlobalContainerStack().getId()][str(self._active_extruder_index)]
        except KeyError: #Extruder index could be -1 if the global tab is selected, or the entry doesn't exist if the machine definition is wrong.
            return None

    __instance = None
    @classmethod
    def getInstance(cls):
        if not cls.__instance:
            cls.__instance = ExtruderManager()
        return cls.__instance

    @pyqtSlot(int)
    def setActiveExtruderIndex(self, index):
        self._active_extruder_index = index
        self.activeExtruderChanged.emit()

    ##  Adds all extruders of a specific machine definition to the extruder
    #   manager.
    #
    #   \param machine_definition The machine to add the extruders for.
    def addMachineExtruders(self, machine_definition):
        machine_id = machine_definition.getId()
        if not self._extruder_trains[machine_id]:
            self._extruder_trains[machine_id] = { }

        container_registry = UM.Settings.ContainerRegistry.getInstance()
        if not container_registry: #Then we shouldn't have any machine definition either. In any case, there are no extruder trains then so bye bye.
            return

        #Add the extruder trains that don't exist yet.
        for position, extruder_definition_id in machine_definition.getMetaDataEntry("machine_extruder_trains", default = {}).items():
            extruder_definition = container_registry.findDefinitionContainers(id = extruder_definition_id)
            if extruder_definition:
                extruder_definition = extruder_definition[0]
            else:
                Logger.log("w", "Machine %s references an extruder with ID %s, which doesn't exist.", machine_definition.getName(), extruder_definition_id)
                continue
            name = self._uniqueName(extruder_definition_id) #Make a name based on the ID of the definition.
            if not container_registry.findContainerStacks(id = name): #Doesn't exist yet.
                self.createExtruderTrain(extruder_definition, machine_definition, name, position)

        #Gets the extruder trains that we just created as well as any that still existed.
        extruder_trains = container_registry.findContainerStacks(type = "extruder_train", machine = machine_definition.getId())
        for extruder_train in extruder_trains:
            self._extruder_trains[machine_id][extruder_train.getMetaDataEntry("position")] = extruder_train.getId()
        if extruder_trains:
            self.extrudersChanged.emit()

    ##  (Re)populates the collections of extruders by machine.
    def _repopulate(self):
        self._extruder_trains = { }
        if not UM.Application.getInstance().getGlobalContainerStack(): #No machine has been added yet.
            self.extrudersChanged.emit() #Yes, we just cleared the _extruders list!
            return #Then leave them empty!

        extruder_trains = UM.Settings.ContainerRegistry.getInstance().findContainerStacks(type = "extruder_train")
        for extruder_train in extruder_trains:
            machine_id = extruder_train.getMetaDataEntry("machine")
            if not machine_id:
                continue
            if machine_id not in self._extruder_trains:
                self._extruder_trains[machine_id] = { }
            self._extruder_trains[machine_id][extruder_train.getMetaDataEntry("position")] = extruder_train.getId()
        self.extrudersChanged.emit()

    def createExtruderTrain(self, extruder_definition, machine_definition, extruder_train_id, position):
        container_registry = UM.Settings.ContainerRegistry.getInstance()

        #Create a container stack for this extruder.
        container_stack = UM.Settings.ContainerStack(extruder_train_id)
        container_stack.addMetaDataEntry("type", "extruder_train")
        container_stack.addMetaDataEntry("machine", machine_definition.getId())
        container_stack.addMetaDataEntry("position", position)
        container_stack.addContainer(extruder_definition)

        """
        Yes, I'm committing this code which needs to be transformed to work later.
        #Find the nozzle to use for this extruder.
        nozzle = container_registry.getEmptyInstanceContainer()
        if definition.getMetaDataEntry("has_nozzles", default = "False") == "True":
            if len(self._nozzles) >= 1: #First add any extruder. Later, overwrite with preference if the preference is valid.
                self._nozzle = self._nozzles[0]
            preferred_nozzle_id = definition.getMetaDataEntry("preferred_nozzle")
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
        """

        #Add an empty user profile.
        user_profile = UM.Settings.InstanceContainer(extruder_train_id + "_current_settings")
        user_profile.addMetaDataEntry("type", "user")
        user_profile.setDefinition(machine_definition)
        container_stack.addContainer(user_profile)
        container_registry.addContainer(user_profile)

        container_stack.setNextStack(UM.Application.getInstance().getGlobalContainerStack())

        container_registry.addContainer(container_stack)


    def _uniqueName(self, original):
        container_registry = UM.Settings.ContainerRegistry.getInstance()

        name = original.strip()
        num_check = re.compile("(.*?)\s*#\d$").match(name)
        if num_check:  # There is a number in the name.
            name = num_check.group(1)  # Filter out the number.
        if name == "":  # Wait, that deleted everything!
            name = "Extruder"
        unique_name = name

        i = 1
        while container_registry.findContainers(id=unique_name) or container_registry.findContainers(
                name=unique_name):  # A container already has this name.
            i += 1  # Try next numbering.
            unique_name = "%s #%d" % (name, i)  # Fill name like this: "Extruder #2".
        return unique_name


def createExtruderManager(engine, script_engine):
    return ExtruderManager()