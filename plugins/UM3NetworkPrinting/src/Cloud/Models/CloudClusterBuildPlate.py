# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from .BaseCloudModel import BaseCloudModel


##  Class representing a cluster printer
#  Spec: https://api-staging.ultimaker.com/connect/v1/spec
class CloudClusterBuildPlate(BaseCloudModel):
    ## Create a new build plate
    #  \param type: The type of buildplate glass or aluminium
    def __init__(self, type: str = "glass", **kwargs) -> None:
        self.type = type
        super().__init__(**kwargs)
