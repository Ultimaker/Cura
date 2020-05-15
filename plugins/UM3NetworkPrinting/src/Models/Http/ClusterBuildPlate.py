# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from ..BaseModel import BaseModel


class ClusterBuildPlate(BaseModel):
    """Class representing a cluster printer"""

    def __init__(self, type: str = "glass", **kwargs) -> None:
        """Create a new build plate
        
        :param type: The type of build plate glass or aluminium
        """
        self.type = type
        super().__init__(**kwargs)
