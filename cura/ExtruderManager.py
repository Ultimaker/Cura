# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import pyqtSignal, pyqtProperty, pyqtSlot, QObject, QVariant #For communicating data and events to Qt.

import UM.Application #To get the global container stack to find the current machine.
import UM.Logger
import UM.Settings.ContainerRegistry #Finding containers by ID.


##  Manages all existing extruder stacks.
#
#   This keeps a list of extruder stacks for each machine.
class ExtruderManager(QObject):
    ##  Signal to notify other components when the list of extruders changes.
    extrudersChanged = pyqtSignal(QVariant)

    ##  Notify when the user switches the currently active extruder.
    activeExtruderChanged = pyqtSignal()

    ##  Registers listeners and such to listen to changes to the extruders.
    def __init__(self, parent = None):
        super().__init__(parent)
        self._extruder_trains = { } #Per machine, a dictionary of extruder container stack IDs.
        self._active_extruder_index = 0
        UM.Application.getInstance().globalContainerStackChanged.connect(self._addCurrentMachineExtruders)

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

    ##  The instance of the singleton pattern.
    #
    #   It's None if the extruder manager hasn't been created yet.
    __instance = None

    ##  Gets an instance of the extruder manager, or creates one if no instance
    #   exists yet.
    #
    #   This is an implementation of singleton. If an extruder manager already
    #   exists, it is re-used.
    #
    #   \return The extruder manager.
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
        if machine_id not in self._extruder_trains:
            self._extruder_trains[machine_id] = { }

        container_registry = UM.Settings.ContainerRegistry.getInstance()
        if not container_registry: #Then we shouldn't have any machine definition either. In any case, there are no extruder trains then so bye bye.
            return

        #Add the extruder trains that don't exist yet.
        for extruder_definition in container_registry.findDefinitionContainers(machine = machine_definition.getId()):
            position = extruder_definition.getMetaDataEntry("position", None)
            if not position:
                UM.Logger.log("w", "Extruder definition %s specifies no position metadata entry.", extruder_definition.getId())
            if not container_registry.findContainerStacks(machine = machine_id, position = position): #Doesn't exist yet.
                name = container_registry.uniqueName(extruder_definition.getId()) #Make a name based on the ID of the definition.
                self.createExtruderTrain(extruder_definition, machine_definition, name, position)

        #Gets the extruder trains that we just created as well as any that still existed.
        extruder_trains = container_registry.findContainerStacks(type = "extruder_train", machine = machine_definition.getId())
        for extruder_train in extruder_trains:
            self._extruder_trains[machine_id][extruder_train.getMetaDataEntry("position")] = extruder_train.getId()
        if extruder_trains:
            self.extrudersChanged.emit(machine_definition)

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

    ##  Generates extruders for a specific machine.
    def getMachineExtruders(self, machine_definition):
        container_registry = UM.Settings.ContainerRegistry.getInstance()
        machine_id = machine_definition.getId()
        if not machine_id in self._extruder_trains:
            UM.Logger.log("w", "Tried to get the extruder trains for machine %s, which doesn't exist.", machine_id)
            return
        for extruder_train_id in self._extruder_trains[machine_id]:
            extruder_train = container_registry.findContainerStacks(id = extruder_train_id)
            if extruder_train:
                yield extruder_train[0]
            else:
                UM.Logger.log("w", "Machine %s refers to an extruder train with ID %s, which doesn't exist.", machine_id, extruder_train_id)

    ##  Adds the extruders of the currently active machine.
    def _addCurrentMachineExtruders(self):
        global_stack = UM.Application.getInstance().getGlobalContainerStack()
        if global_stack and global_stack.getBottom():
            self.addMachineExtruders(global_stack.getBottom())