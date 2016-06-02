# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from cura.Extruder import Extruder #The individual extruders managed by this manager.
import UM.Application #To get the global container stack to find the current machine.
import UM.Logger
import UM.Settings.ContainerRegistry #Finding containers by ID.
import UM.Signal #To notify other components of changes in the extruders.


##  Class that handles the current extruder stack.
#
#   This finds the extruders that are available for the currently active machine
#   and makes sure that whenever the machine is swapped, this list is kept up to
#   date. It also contains and updates the setting stacks for the extruders.
class ExtruderManager:
    ##  The singleton instance of this manager.
    __instance = None

    ##  Signal to notify other components when the list of extruders changes.
    extrudersChanged = UM.Signal()

    ##  Registers listeners and such to listen to changes to the extruders.
    def __init__(self):
        self._extruders = [] #Extruders for the current machine.
        self._global_container_stack = None
        self._next_item = 0 #For when you use this class as iterator.

        UM.Application.getInstance().globalContainerStackChanged.connect(self._reconnectExtruderReload) #When the current machine changes, we need to reload all extruders belonging to the new machine.

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

    ##  When the global container stack changes, this reconnects to the new
    #   signal for containers changing.
    def _reconnectExtruderReload(self):
        if self._global_container_stack:
            self._global_container_stack.containersChanged.disconnect(self._reloadExtruders) #Disconnect from the old global container stack.
        self._global_container_stack = UM.Application.getInstance().getGlobalContainerStack()
        self._global_container_stack.containersChanged.connect(self._reloadExtruders) #When the current machine changes, we need to reload all extruders belonging to the new machine.

    ##  (Re)loads all extruders of the currently active machine.
    #
    #   This looks at the global container stack to see which machine is active.
    #   Then it loads the extruders for that machine and loads each of them in a
    #   list of extruders.
    def _reloadExtruders(self):
        self._extruders = []
        if not self._global_container_stack: #No machine has been added yet.
            self.extrudersChanged.emit() #Yes, we just cleared the _extruders list!
            return #Then leave them empty!

        #Get the extruder definitions belonging to the current machine.
        machine = self._global_container_stack.getBottom()
        extruder_train_ids = machine.getMetaData("machine_extruder_trains")
        for extruder_train_id in extruder_train_ids:
            extruder_definitions = UM.Settings.ContainerRegistry.getInstance().findDefinitionContainers(id = extruder_train_id) #Should be only 1 definition if IDs are unique, but add the whole list anyway.
            if not extruder_definitions: #Empty list or error.
                UM.Logger.log("w", "Machine definition %s refers to an extruder train \"%s\", but no such extruder was found.", machine.getId(), extruder_train_id)
                continue
            for extruder_definition in extruder_definitions:
                self._extruders.append(Extruder(extruder_definition))
        self.extrudersChanged.emit()