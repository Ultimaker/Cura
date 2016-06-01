# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import re

from cura.Extruder import Extruder #The individual extruders managed by this manager.
from UM.Application import Application #To get the global container stack to find the current machine.
from UM.Logger import Logger
from UM.Settings.ContainerStack import ContainerStack #To create container stacks for each extruder.
from UM.Settings.ContainerRegistry import ContainerRegistry #Finding containers by ID.


##  Class that handles the current extruder stack.
#
#   This finds the extruders that are available for the currently active machine
#   and makes sure that whenever the machine is swapped, this list is kept up to
#   date. It also contains and updates the setting stacks for the extruders.
class ExtruderManager:
    ##  Registers listeners and such to listen to changes to the extruders.
    def __init__(self):
        self._extruders = [] #Extruders for the current machine.

        Application.getInstance().getGlobalContainerStack().containersChanged.connect(self._reloadExtruders) #When the current machine changes, we need to reload all extruders belonging to the new machine.

    ##  (Re)loads all extruders of the currently active machine.
    #
    #   This looks at the global container stack to see which machine is active.
    #   Then it loads the extruders for that machine and loads each of them in a
    #   list of extruders.
    def _reloadExtruders(self):
        self._extruders = []
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if not global_container_stack: #No machine has been added yet.
            return #Then leave them empty!

        #Get the extruder definitions belonging to the current machine.
        machine = global_container_stack.getBottom()
        extruder_train_ids = machine.getMetaData("machine_extruder_trains")
        for extruder_train_id in extruder_train_ids:
            extruder_definitions = ContainerRegistry.getInstance().findDefinitionContainers(id = extruder_train_id) #Should be only 1 definition if IDs are unique, but add the whole list anyway.
            if not extruder_definitions: #Empty list or error.
                Logger.log("w", "Machine definition %s refers to an extruder train \"%s\", but no such extruder was found.", machine.getId(), extruder_train_id)
                continue
            for extruder_definition in extruder_definitions:
                self._extruders.append(Extruder(extruder_definition))