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
        self._active_extruder_index = -1
        UM.Application.getInstance().globalContainerStackChanged.connect(self.__globalContainerStackChanged)
        self._addCurrentMachineExtruders()

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
            return self._extruder_trains[UM.Application.getInstance().getGlobalContainerStack().getBottom().getId()][str(self._active_extruder_index)].getId()
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

    ##  Changes the active extruder by index.
    #
    #   \param index The index of the new active extruder.
    @pyqtSlot(int)
    def setActiveExtruderIndex(self, index):
        self._active_extruder_index = index
        self.activeExtruderChanged.emit()

    @pyqtProperty(int, notify = activeExtruderChanged)
    def activeExtruderIndex(self):
        return self._active_extruder_index

    def getActiveExtruderStack(self):
        global_container_stack = UM.Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            global_definition_container = UM.Application.getInstance().getGlobalContainerStack().getBottom()
            if global_definition_container:
                if global_definition_container.getId() in self._extruder_trains:
                    if str(self._active_extruder_index) in self._extruder_trains[global_definition_container.getId()]:
                        return self._extruder_trains[global_definition_container.getId()][str(self._active_extruder_index)]
        return None

    ##  Adds all extruders of a specific machine definition to the extruder
    #   manager.
    #
    #   \param machine_definition The machine to add the extruders for.
    def addMachineExtruders(self, machine_definition):
        changed = False
        machine_id = machine_definition.getId()
        if machine_id not in self._extruder_trains:
            self._extruder_trains[machine_id] = { }
            changed = True

        container_registry = UM.Settings.ContainerRegistry.getInstance()
        if container_registry:

            #Add the extruder trains that don't exist yet.
            for extruder_definition in container_registry.findDefinitionContainers(machine = machine_definition.getId()):
                position = extruder_definition.getMetaDataEntry("position", None)
                if not position:
                    UM.Logger.log("w", "Extruder definition %s specifies no position metadata entry.", extruder_definition.getId())
                if not container_registry.findContainerStacks(machine = machine_id, position = position): #Doesn't exist yet.
                    self.createExtruderTrain(extruder_definition, machine_definition, position)
                    changed = True

            #Gets the extruder trains that we just created as well as any that still existed.
            extruder_trains = container_registry.findContainerStacks(type = "extruder_train", machine = machine_definition.getId())
            for extruder_train in extruder_trains:
                self._extruder_trains[machine_id][extruder_train.getMetaDataEntry("position")] = extruder_train

                #Ensure that the extruder train stacks are linked to global stack.
                extruder_train.setNextStack(UM.Application.getInstance().getGlobalContainerStack())
                changed = True

        if changed:
            self.extrudersChanged.emit(machine_definition)

    ##  Creates a container stack for an extruder train.
    #
    #   The container stack has an extruder definition at the bottom, which is
    #   linked to a machine definition. Then it has a variant profile, a material
    #   profile, a quality profile and a user profile, in that order.
    #
    #   The resulting container stack is added to the registry.
    #
    #   \param extruder_definition The extruder to create the extruder train
    #   for.
    #   \param machine_definition The machine that the extruder train belongs
    #   to.
    #   \param position The position of this extruder train in the extruder
    #   slots of the machine.
    def createExtruderTrain(self, extruder_definition, machine_definition, position):
        #Cache some things.
        container_registry = UM.Settings.ContainerRegistry.getInstance()
        machine_id = machine_definition.getId()

        #Create a container stack for this extruder.
        extruder_stack_id = container_registry.uniqueName(extruder_definition.getId())
        container_stack = UM.Settings.ContainerStack(extruder_stack_id)
        container_stack.setName(extruder_definition.getName()) #Take over the display name to display the stack with.
        container_stack.addMetaDataEntry("type", "extruder_train")
        container_stack.addMetaDataEntry("machine", machine_definition.getId())
        container_stack.addMetaDataEntry("position", position)
        container_stack.addContainer(extruder_definition)

        #Find the variant to use for this extruder.
        variant = container_registry.getEmptyInstanceContainer()
        if machine_definition.getMetaDataEntry("has_variants"):
            #First add any variant. Later, overwrite with preference if the preference is valid.
            variants = container_registry.findInstanceContainers(definition = machine_id, type = "variant")
            if len(variants) >= 1:
                variant = variants[0]
            preferred_variant_id = machine_definition.getMetaDataEntry("preferred_variant")
            if preferred_variant_id:
                preferred_variants = container_registry.findInstanceContainers(id = preferred_variant_id, type = "variant")
                if len(preferred_variants) >= 1:
                    variant = preferred_variants[0]
                else:
                    UM.Logger.log("w", "The preferred variant \"%s\" of machine %s doesn't exist or is not a variant profile.", preferred_variant_id, machine_id)
                    #And leave it at the default variant.
        container_stack.addContainer(variant)

        #Find a material to use for this variant.
        material = container_registry.getEmptyInstanceContainer()
        if machine_definition.getMetaDataEntry("has_materials"):
            #First add any material. Later, overwrite with preference if the preference is valid.
            if machine_definition.getMetaDataEntry("has_variant_materials", default = "False") == "True":
                materials = container_registry.findInstanceContainers(type = "material", definition = machine_id, variant = variant.getId())
            else:
                materials = container_registry.findInstanceContainers(type = "material", definition = machine_id)
            if len(materials) >= 1:
                material = materials[0]
            preferred_material_id = machine_definition.getMetaDataEntry("preferred_material")
            if preferred_material_id:
                search_criteria = { "type": "material",  "id": preferred_material_id}
                if machine_definition.getMetaDataEntry("has_machine_materials"):
                    search_criteria["definition"] = machine_definition.id

                    if machine_definition.getMetaDataEntry("has_variants") and variant:
                        search_criteria["variant"] = variant.id
                else:
                    search_criteria["definition"] = "fdmprinter"

                preferred_materials = container_registry.findInstanceContainers(**search_criteria)
                if len(preferred_materials) >= 1:
                    material = preferred_materials[0]
                else:
                    UM.Logger.log("w", "The preferred material \"%s\" of machine %s doesn't exist or is not a material profile.", preferred_material_id, machine_id)
                    #And leave it at the default material.
        container_stack.addContainer(material)

        #Find a quality to use for this extruder.
        quality = container_registry.getEmptyInstanceContainer()

        #First add any quality. Later, overwrite with preference if the preference is valid.
        qualities = container_registry.findInstanceContainers(type = "quality")
        if len(qualities) >= 1:
            quality = qualities[0]
        preferred_quality_id = machine_definition.getMetaDataEntry("preferred_quality")
        if preferred_quality_id:
            preferred_quality = container_registry.findInstanceContainers(id = preferred_quality_id, type = "quality")
            if len(preferred_quality) >= 1:
                quality = preferred_quality[0]
            else:
                UM.Logger.log("w", "The preferred quality \"%s\" of machine %s doesn't exist or is not a quality profile.", preferred_quality_id, machine_id)
                #And leave it at the default quality.
        container_stack.addContainer(quality)

        user_profile = container_registry.findInstanceContainers(id = extruder_stack_id + "_current_settings")
        if user_profile: #There was already a user profile, loaded from settings.
            user_profile = user_profile[0]
        else:
            user_profile = UM.Settings.InstanceContainer(extruder_stack_id + "_current_settings") #Add an empty user profile.
            user_profile.addMetaDataEntry("type", "user")
            user_profile.setDefinition(machine_definition)
            container_registry.addContainer(user_profile)
        container_stack.addContainer(user_profile)

        container_stack.setNextStack(UM.Application.getInstance().getGlobalContainerStack())

        container_registry.addContainer(container_stack)

    ##  Generates extruders for a specific machine.
    #
    #   \param machine_id The machine to get the extruders of.
    def getMachineExtruders(self, machine_id):
        if machine_id not in self._extruder_trains:
            UM.Logger.log("w", "Tried to get the extruder trains for machine %s, which doesn't exist.", machine_id)
            return
        for name in self._extruder_trains[machine_id]:
            yield self._extruder_trains[machine_id][name]

    def __globalContainerStackChanged(self):
        self._addCurrentMachineExtruders()
        self.activeExtruderChanged.emit()

    ##  Adds the extruders of the currently active machine.
    def _addCurrentMachineExtruders(self):
        global_stack = UM.Application.getInstance().getGlobalContainerStack()
        if global_stack and global_stack.getBottom():
            self.addMachineExtruders(global_stack.getBottom())
