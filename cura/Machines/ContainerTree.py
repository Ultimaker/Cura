# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Settings.ContainerRegistry import ContainerRegistry  # To listen to containers being added.
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.Interfaces import ContainerInterface
from cura.Machines.MachineNode import MachineNode

from typing import Dict

##  This class contains a look-up tree for which containers are available at
#   which stages of configuration.
#
#   The tree starts at the machine definitions. For every distinct definition
#   there will be one machine node here.
class ContainerTree:
    __instance = None

    @classmethod
    def getInstance(cls):
        if cls.__instance is None:
            cls.__instance = ContainerTree()
        return cls.__instance

    def __init__(self) -> None:
        self.machines = {}  # type: Dict[str, MachineNode] # Mapping from definition ID to machine nodes.
        container_registry = ContainerRegistry.getInstance()
        container_registry.containerAdded.connect(self._machineAdded)
        self._loadAll()

    ##  Builds the initial container tree.
    def _loadAll(self):
        all_stacks = ContainerRegistry.getInstance().findContainerStacks()
        for stack in all_stacks:
            definition_id = stack.definition.getId()
            if definition_id not in self.machines:
                self.machines[definition_id] = MachineNode(definition_id)

    ##  When a printer gets added, we need to build up the tree for that container.
    def _machineAdded(self, definition_container: ContainerInterface):
        if not isinstance(definition_container, DefinitionContainer):
            return  # Not our concern.
        definition_id = definition_container.getId()
        if definition_id in self.machines:
            return  # Already have this definition ID.

        self.machines[definition_id] = MachineNode(definition_id)