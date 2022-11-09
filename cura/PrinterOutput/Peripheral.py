# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from dataclasses import dataclass

@dataclass
class Peripheral:
    """Data class that represents a peripheral for a printer.

    Output device plug-ins may specify that the printer has a certain set of
    peripherals. This set is then possibly shown in the interface of the monitor
    stage.

    Args:
        type (string): A unique ID for the type of peripheral.
        name (string): A human-readable name for the peripheral.
    """
    type: str
    name: str
