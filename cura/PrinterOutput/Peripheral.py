# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

##  Data class that represents a peripheral for a printer.
#
#   Output device plug-ins may specify that the printer has a certain set of
#   peripherals. This set is then possibly shown in the interface of the monitor
#   stage.
class Peripheral:
    ##  Constructs the peripheral.
    #   \param id A unique ID for the peripheral object, like a MAC address or
    #   some hardware ID.
    #   \param type A unique ID for the type of peripheral.
    #   \param name A human-readable name for the peripheral.
    def __init__(self, type: str, name: str):
        self.type = type
        self.name = name