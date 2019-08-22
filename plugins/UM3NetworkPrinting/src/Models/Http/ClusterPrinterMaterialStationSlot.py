# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from .ClusterPrintCoreConfiguration import ClusterPrintCoreConfiguration


##  Class representing the data of a single slot in the material station.
class ClusterPrinterMaterialStationSlot(ClusterPrintCoreConfiguration):
    
    ## Create a new material station slot object.
    #  \param slot_index: The index of the slot in the material station (ranging 0 to 5).
    #  \param compatible: Whether the configuration is compatible with the print core.
    #  \param material_remaining: How much material is remaining on the spool (between 0 and 1, or -1 for missing data).
    def __init__(self, slot_index: int, compatible: bool, material_remaining: float, **kwargs):
        self.slot_index = slot_index
        self.compatible = compatible
        self.material_remaining = material_remaining
        super().__init__(**kwargs)
