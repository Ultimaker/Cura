# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import pyqtSignal, pyqtProperty, pyqtSlot, QObject

import UM.Application #To get the global container stack to find the current machine.
import UM.Logger
import UM.Settings.ContainerRegistry #Finding containers by ID.
import UM.Signal #To notify other components of changes in the extruders.


##  Class that handles the current extruder stack.
#
#   This finds the extruders that are available for the currently active machine
#   and makes sure that whenever the machine is swapped, this list is kept up to
#   date. It also contains and updates the setting stacks for the extruders.
class ExtruderManager(QObject):
    ##  The singleton instance of this manager.
    __instance = None

    ##  Signal to notify other components when the list of extruders changes.
    extrudersChanged = UM.Signal()

    ##  Notify when the user switches the currently active extruder.
    activeExtruderChanged = pyqtSignal()

    ##  Registers listeners and such to listen to changes to the extruders.
    def __init__(self, parent = None):
        super().__init__(parent)
        self._extruder_trains = { } #Extruders for the current machine.
        self._next_item = 0 #For when you use this class as iterator.
        self._active_extruder_index = 0

        self._repopulate()

    ##  Gets an instance of this extruder manager.
    #
    #   If an instance was already created, the old instance is returned. This
    #   implements the singleton pattern.
    @classmethod
    def getInstance(cls):
        if not cls.__instance:
            cls.__instance = ExtruderManager()
        return cls.__instance

    ##  Creates an iterator over the extruders in this manager.
    #
    #   \return An iterator over the extruders in this manager.
    def __iter__(self):
        return iter(self._extruders)

    @pyqtProperty(str, notify = activeExtruderChanged)
    def activeExtruderStackId(self):
        if UM.Application.getInstance().getGlobalContainerStack():
            try:
                return self._extruder_trains[UM.Application.getInstance().getGlobalContainerStack().getId()][str(self._active_extruder_index)]
            except KeyError:
                pass

    @pyqtSlot(int)
    def setActiveExtruderIndex(self, index):
        self._active_extruder_index = index
        self.activeExtruderChanged.emit()

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

    def createExtruderTrain(self, definition, extruder_id):
        container_registry = UM.Settings.ContainerRegistry.getInstance()

        #Create a container stack for this extruder.
        name = self._uniqueName(extruder_id)
        container_stack = UM.Settings.ContainerStack(name)
        container_stack.addMetaDataEntry("type", "extruder_train")
        container_stack.addContainer(definition)

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
        user_profile = UM.Settings.InstanceContainer(name + "_current_settings")
        user_profile.addMetaDataEntry("type", "user")
        container_stack.addContainer(user_profile)
        container_registry.addContainer(user_profile)

        container_stack.setNextStack(UM.Application.getInstance().getGlobalContainerStack())

        container_registry.addContainer(container_stack)

def createExtruderManager(engine, script_engine):
    return ExtruderManager()