# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from cura.Machines.MachineNode import MachineNode

from typing import Dict

##  This class contains a look-up tree for which containers are available at
#   which stages of configuration.
#
#   The tree starts at the machine definitions. For every distinct definition
#   there will be one machine node here.
class ContainerTree:
    def __init__(self) -> None:
        self.machines = {}  # type: Dict[str, MachineNode] # Mapping from definition ID to machine nodes.