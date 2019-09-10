# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Logger import Logger
from UM.Settings.ContainerRegistry import ContainerRegistry  # To listen to containers being added.
from UM.Settings.Interfaces import ContainerInterface
from UM.Signal import Signal
import cura.CuraApplication  # Imported like this to prevent circular dependencies.
from cura.Machines.MachineNode import MachineNode
from cura.Settings.GlobalStack import GlobalStack  # To listen only to global stacks being added.

from typing import Dict, List, TYPE_CHECKING
import time

if TYPE_CHECKING:
    from cura.Machines.QualityGroup import QualityGroup
    from cura.Machines.QualityChangesGroup import QualityChangesGroup

##  This class contains a look-up tree for which containers are available at
#   which stages of configuration.
#
#   The tree starts at the machine definitions. For every distinct definition
#   there will be one machine node here.
#
#   All of the fallbacks for material choices, quality choices, etc. should be
#   encoded in this tree. There must always be at least one child node (for
#   nodes that have children) but that child node may be a node representing the
#   empty instance container.
class ContainerTree:
    __instance = None

    @classmethod
    def getInstance(cls):
        if cls.__instance is None:
            cls.__instance = ContainerTree()
        return cls.__instance

    def __init__(self) -> None:
        self.machines = {}  # type: Dict[str, MachineNode] # Mapping from definition ID to machine nodes.
        self.materialsChanged = Signal()  # Emitted when any of the material nodes in the tree got changed.

        container_registry = ContainerRegistry.getInstance()
        container_registry.containerAdded.connect(self._machineAdded)
        self._loadAll()

    ##  Get the quality groups available for the currently activated printer.
    #
    #   This contains all quality groups, enabled or disabled. To check whether
    #   the quality group can be activated, test for the
    #   ``QualityGroup.is_available`` property.
    #   \return For every quality type, one quality group.
    def getCurrentQualityGroups(self) -> Dict[str, "QualityGroup"]:
        global_stack = cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack()
        if global_stack is None:
            return {}
        variant_names = [extruder.variant.getName() for extruder in global_stack.extruderList]
        material_bases = [extruder.material.getMetaDataEntry("base_file") for extruder in global_stack.extruderList]
        extruder_enabled = [extruder.isEnabled for extruder in global_stack.extruderList]
        return self.machines[global_stack.definition.getId()].getQualityGroups(variant_names, material_bases, extruder_enabled)

    ##  Get the quality changes groups available for the currently activated
    #   printer.
    #
    #   This contains all quality changes groups, enabled or disabled. To check
    #   whether the quality changes group can be activated, test for the
    #   ``QualityChangesGroup.is_available`` property.
    #   \return A list of all quality changes groups.
    def getCurrentQualityChangesGroups(self) -> List["QualityChangesGroup"]:
        global_stack = cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack()
        if global_stack is None:
            return []
        variant_names = [extruder.variant.getName() for extruder in global_stack.extruderList]
        material_bases = [extruder.material.getMetaDataEntry("base_file") for extruder in global_stack.extruderList]
        extruder_enabled = [extruder.isEnabled for extruder in global_stack.extruderList]
        return self.machines[global_stack.definition.getId()].getQualityChangesGroups(variant_names, material_bases, extruder_enabled)

    ##  Builds the initial container tree.
    def _loadAll(self):
        Logger.log("i", "Building container tree.")
        start_time = time.time()
        all_stacks = ContainerRegistry.getInstance().findContainerStacks()
        for stack in all_stacks:
            if not isinstance(stack, GlobalStack):
                continue  # Only want to load global stacks. We don't need to create a tree for extruder definitions.
            definition_id = stack.definition.getId()
            if definition_id not in self.machines:
                definition_start_time = time.time()
                self.machines[definition_id] = MachineNode(definition_id)
                self.machines[definition_id].materialsChanged.connect(self.materialsChanged)
                Logger.log("d", "Adding container tree for {definition_id} took {duration} seconds.".format(definition_id = definition_id, duration = time.time() - definition_start_time))

        Logger.log("d", "Building the container tree took %s seconds",  time.time() - start_time)
        
    ##  When a printer gets added, we need to build up the tree for that container.
    def _machineAdded(self, container_stack: ContainerInterface):
        if not isinstance(container_stack, GlobalStack):
            return  # Not our concern.
        definition_id = container_stack.definition.getId()
        if definition_id in self.machines:
            return  # Already have this definition ID.

        start_time = time.time()
        self.machines[definition_id] = MachineNode(definition_id)
        self.machines[definition_id].materialsChanged.connect(self.materialsChanged)
        Logger.log("d", "Adding container tree for {definition_id} took {duration} seconds.".format(definition_id = definition_id, duration = time.time() - start_time))