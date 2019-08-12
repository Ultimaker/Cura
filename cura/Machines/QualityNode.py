# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Union, TYPE_CHECKING

from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.Interfaces import ContainerInterface
from cura.Machines.ContainerNode import ContainerNode
from cura.Machines.IntentNode import IntentNode

if TYPE_CHECKING:
    from typing import Dict
    from cura.Machines.MaterialNode import MaterialNode
    from cura.Machines.MachineNode import MachineNode

##  Represents a material profile in the container tree.
#
#   Its subcontainers are intent profiles.
class QualityNode(ContainerNode):
    def __init__(self, container_id: str, parent: Union["MaterialNode", "MachineNode"]) -> None:
        super().__init__(container_id)
        self.parent = parent
        self.intents = {}  # type: Dict[str, IntentNode]
        ContainerRegistry.getInstance().containerAdded.connect(self._intentAdded)
        self._loadAll()

    def _loadAll(self) -> None:
        container_registry = ContainerRegistry.getInstance()
        # Find all intent profiles that fit the current configuration.
        if not isinstance(self.parent, MachineNode):  # Not a global profile.
            for intent in container_registry.findInstanceContainersMetadata(type = "intent", definition = self.parent.variant.machine.quality_definition, variant = self.parent.variant.variant_name, material = self.parent.base_file):
                self.intents[intent["id"]] = IntentNode(intent["id"], quality = self)
        # Otherwise, there are no intents for global profiles.

    def _intentAdded(self, container: ContainerInterface) -> None:
        from cura.Machines.MachineNode import MachineNode  # Imported here to prevent circular imports.
        if container.getMetaDataEntry("type") != "intent":
            return  # Not interested if it's not an intent.
        if isinstance(self.parent, MachineNode):
            return  # Global profiles don't have intents.
        if container.getMetaDataEntry("definition") != self.parent.variant.machine.quality_definition:
            return  # Incorrect printer.
        if container.getMetaDataEntry("variant") != self.parent.variant.variant_name:
            return  # Incorrect variant.
        if container.getMetaDataEntry("material") != self.parent.base_file:
            return  # Incorrect material.
        container_id = container.getId()
        if container_id in self.intents:
            return  # Already have this.
        self.intents[container_id] = IntentNode(container_id, quality = self)