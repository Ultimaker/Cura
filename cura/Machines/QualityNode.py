# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING

from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.Interfaces import ContainerInterface
from cura.Machines.ContainerNode import ContainerNode
from cura.Machines.IntentNode import IntentNode

if TYPE_CHECKING:
    from typing import Dict
    from cura.Machines.MaterialNode import MaterialNode

##  Represents a material profile in the container tree.
#
#   Its subcontainers are intent profiles.
class QualityNode(ContainerNode):
    def __init__(self, container_id: str, material: "MaterialNode") -> None:
        super().__init__(container_id)
        self.material = material
        self.intents = {}  # type: Dict[str, IntentNode]
        ContainerRegistry.getInstance().containerAdded.connect(self._intentAdded)
        self._loadAll()

    def _loadAll(self) -> None:
        container_registry = ContainerRegistry.getInstance()
        # Find all intent profiles that fit the current configuration.
        for intent in container_registry.findInstanceContainersMetadata(type = "intent", definition = self.material.variant.machine.quality_definition, variant = self.material.variant.variant_name, material = self.material.base_file):
            self.intents[intent["id"]] = IntentNode(intent["id"], quality = self)

    def _intentAdded(self, container: ContainerInterface) -> None:
        if container.getMetaDataEntry("type") != "intent":
            return  # Not interested if it's not an intent.
        if container.getMetaDataEntry("definition") != self.material.variant.machine.quality_definition:
            return  # Incorrect printer.
        if container.getMetaDataEntry("variant") != self.material.variant.variant_name:
            return  # Incorrect variant.
        if container.getMetaDataEntry("material") != self.material.base_file:
            return  # Incorrect material.
        container_id = container.getId()
        if container_id in self.intents:
            return  # Already have this.
        self.intents[container_id] = IntentNode(container_id, quality = self)