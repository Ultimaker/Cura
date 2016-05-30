# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal
import re

from UM.Application import Application #To get the global container stack to find the current machine.
from UM.Logger import Logger
from UM.Settings.ContainerStack import ContainerStack #To create container stacks for each extruder.
from UM.Settings.ContainerRegistry import ContainerRegistry #Finding containers by ID.


##  Class that handles the current extruder stack.
#
#   This finds the extruders that are available for the currently active machine
#   and makes sure that whenever the machine is swapped, this list is kept up to
#   date. It also contains and updates the setting stacks for the extruders.
class ExtruderManagerModel(QObject):
    ##  Registers listeners and such to listen to changes to the extruders.
    #
    #   \param parent Parent QObject of this model.
    def __init__(self, parent = None):
        super().__init__(parent)

        self._extruderDefinitions = [] #Extruder definitions for the current machine.
        self._nozzles = {} #Nozzle instances for each extruder.
        self._extruderTrains = [] #Container stacks for each of the extruder trains.

        Application.getInstance().getGlobalContainerStack().containersChanged.connect(self._reloadExtruders) #When the current machine changes, we need to reload all extruders belonging to the new machine.

    ##  (Re)loads all extruders of the currently active machine.
    #
    #   This looks at the global container stack to see which machine is active.
    #   Then it loads the extruder definitions for that machine and the variants
    #   of those definitions. Then it puts the new extruder definitions in the
    #   appropriate place in the container stacks.
    def _reloadExtruders(self):
        self._extruderDefinitions = []
        self._nozzles = {}
        self._extruderTrains = []
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if not global_container_stack: #No machine has been added yet.
            return #Then leave them empty!

        #Fill the list of extruder trains.
        machine = global_container_stack.getBottom()
        extruder_train_ids = machine.getMetaData("machine_extruder_trains")
        for extruder_train_id in extruder_train_ids:
            extruders = ContainerRegistry.getInstance().findDefinitionContainers(id = extruder_train_id) #Should be only 1 definition if IDs are unique, but add the whole list anyway.
            if not extruders: #Empty list or error.
                Logger.log("w", "Machine definition %s refers to an extruder train \"%s\", but no such extruder was found.", machine.getId(), extruder_train_id)
                continue
            self._extruderDefinitions += extruders

        #Fill the nozzles for each of the extruder trains.
        for extruder in self._extruderDefinitions:
            self._nozzles[extruder.id] = []
        all_nozzles = ContainerRegistry.getInstance().findInstanceContainers(type="nozzle")
        for nozzle in all_nozzles:
            extruders = nozzle.getMetaDataEntry("definitions").split(",").strip()
            for extruder_id in extruders:
                self._nozzles[extruder_id] = nozzle

        #Create the extruder train container stacks.
        for extruder in self._extruderDefinitions:
            self._extruderTrains.append(self._createContainerStack(extruder))

    ##  Creates a container stack for the specified extruder.
    #
    #   This fills in the specified extruder as base definition, then a nozzle
    #   that fits in that extruder train, then a material that fits through that
    #   nozzle, then a quality profile that can be used with that material, and
    #   finally an empty user profile.
    #
    #   \param extruder The extruder to create the container stack for.
    #   \return A container stack with the specified extruder as base.
    def _createContainerStack(self, extruder):
        container_stack = ContainerStack(self._uniqueName(extruder))
        #TODO: Fill the container stack.
        return container_stack

    ##  Finds a unique name for an extruder stack.
    #
    #   \param extruder Extruder to design a name for.
    #   \return A name for an extruder stack that is unique and reasonably
    #   human-readable.
    def _uniqueName(self, extruder):
        container_registry = ContainerRegistry.getInstance()

        name = extruder.getName().strip()
        num_check = re.compile("(.*?)\s*#\d$").match(name)
        if(num_check): #There is a number in the name.
            name = num_check.group(1) #Filter out the number.
        if name == "": #Wait, that deleted everything!
            name = "Extruder"
        unique_name = name

        i = 1
        while(container_registry.findContainers(id = unique_name) or container_registry.findContainers(name = unique_name)): #A container already has this name.
            i += 1 #Try next numbering.
            unique_name = "%s #%d" % (name, i) #Fill name like this: "Extruder #2".
        return unique_name