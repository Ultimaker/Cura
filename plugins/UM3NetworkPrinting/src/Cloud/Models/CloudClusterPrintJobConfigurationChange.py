# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional

from .BaseCloudModel import BaseCloudModel


## Model for the types of changes that are needed before a print job can start
#  Spec: https://api-staging.ultimaker.com/connect/v1/spec
class CloudClusterPrintJobConfigurationChange(BaseCloudModel):
    ## Creates a new print job constraint.
    #  \param type_of_change: The type of configuration change, one of: "material", "print_core_change"
    #  \param index: The hotend slot or extruder index to change
    #  \param target_id: Target material guid or hotend id
    #  \param origin_id: Original/current material guid or hotend id
    #  \param target_name: Target material name or hotend id
    #  \param origin_name: Original/current material name or hotend id
    def __init__(self, type_of_change: str, target_id: str, origin_id: str,
                 index: Optional[int] = None, target_name: Optional[str] = None, origin_name: Optional[str] = None,
                 **kwargs) -> None:
        self.type_of_change = type_of_change
        self.index = index
        self.target_id = target_id
        self.origin_id = origin_id
        self.target_name = target_name
        self.origin_name = origin_name
        super().__init__(**kwargs)
