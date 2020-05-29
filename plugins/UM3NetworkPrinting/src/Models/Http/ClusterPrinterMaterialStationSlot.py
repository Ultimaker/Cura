# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional

from .ClusterPrintCoreConfiguration import ClusterPrintCoreConfiguration


class ClusterPrinterMaterialStationSlot(ClusterPrintCoreConfiguration):
    """Class representing the data of a single slot in the material station."""

    def __init__(self, slot_index: int, compatible: bool, material_remaining: float,
                 material_empty: Optional[bool] = False, **kwargs) -> None:
        """Create a new material station slot object.

        :param slot_index: The index of the slot in the material station (ranging 0 to 5).
        :param compatible: Whether the configuration is compatible with the print core.
        :param material_remaining: How much material is remaining on the spool (between 0 and 1, or -1 for missing data).
        :param material_empty: Whether the material spool is too empty to be used.
        """

        self.slot_index = slot_index
        self.compatible = compatible
        self.material_remaining = material_remaining
        self.material_empty = material_empty
        super().__init__(**kwargs)
