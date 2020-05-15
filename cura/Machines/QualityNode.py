# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Union, TYPE_CHECKING

from UM.Settings.ContainerRegistry import ContainerRegistry
from cura.Machines.ContainerNode import ContainerNode
from cura.Machines.IntentNode import IntentNode
import UM.FlameProfiler
if TYPE_CHECKING:
    from typing import Dict
    from cura.Machines.MaterialNode import MaterialNode
    from cura.Machines.MachineNode import MachineNode


class QualityNode(ContainerNode):
    """Represents a quality profile in the container tree.
    
    This may either be a normal quality profile or a global quality profile.
    
    Its subcontainers are intent profiles.
    """

    def __init__(self, container_id: str, parent: Union["MaterialNode", "MachineNode"]) -> None:
        super().__init__(container_id)
        self.parent = parent
        self.intents = {}  # type: Dict[str, IntentNode]

        my_metadata = ContainerRegistry.getInstance().findContainersMetadata(id = container_id)[0]
        self.quality_type = my_metadata["quality_type"]
        # The material type of the parent doesn't need to be the same as this due to generic fallbacks.
        self._material = my_metadata.get("material")
        self._loadAll()

    @UM.FlameProfiler.profile
    def _loadAll(self) -> None:
        container_registry = ContainerRegistry.getInstance()

        # Find all intent profiles that fit the current configuration.
        from cura.Machines.MachineNode import MachineNode
        if not isinstance(self.parent, MachineNode):  # Not a global profile.
            for intent in container_registry.findInstanceContainersMetadata(type = "intent", definition = self.parent.variant.machine.quality_definition, variant = self.parent.variant.variant_name, material = self._material, quality_type = self.quality_type):
                self.intents[intent["id"]] = IntentNode(intent["id"], quality = self)

        self.intents["empty_intent"] = IntentNode("empty_intent", quality = self)
        # Otherwise, there are no intents for global profiles.
