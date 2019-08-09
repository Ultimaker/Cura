# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from ..BaseModel import BaseModel


## Class representing a cluster printer
class ClusterBuildPlate(BaseModel):

    ## Create a new build plate
    #  \param type: The type of build plate glass or aluminium
    def __init__(self, type: str = "glass", **kwargs) -> None:
        self.type = type
        super().__init__(**kwargs)
