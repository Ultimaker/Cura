# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Union, Dict, Any, List

from ..BaseModel import BaseModel
from .ClusterPrinterMaterialStationSlot import ClusterPrinterMaterialStationSlot


## Class representing the data of a Material Station in the cluster.
class ClusterPrinterMaterialStation(BaseModel):

    ## Creates a new Material Station status.
    #  \param status: The status of the material station.
    #  \param: supported: Whether the material station is supported on this machine or not.
    #  \param material_slots: The active slots configurations of this material station.
    def __init__(self, status: str, supported: bool = False,
                 material_slots: List[Union[None, Dict[str, Any], ClusterPrinterMaterialStationSlot]] = None,
                 **kwargs) -> None:
        self.status = status
        self.supported = supported
        self.material_slots = self.parseModels(ClusterPrinterMaterialStationSlot, material_slots)\
            if material_slots else []  # type: List[ClusterPrinterMaterialStationSlot]
        super().__init__(**kwargs)
