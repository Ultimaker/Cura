# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.


class Peripheral:
    """Data class that represents a peripheral for a printer.
    
    Output device plug-ins may specify that the printer has a certain set of
    peripherals. This set is then possibly shown in the interface of the monitor
    stage.
    """

    def __init__(self, peripheral_type: str, name: str) -> None:
        """Constructs the peripheral.
        
        :param peripheral_type: A unique ID for the type of peripheral.
        :param name: A human-readable name for the peripheral.
        """
        self.type = peripheral_type
        self.name = name
