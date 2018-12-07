# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from .BaseCloudModel import BaseCloudModel


## Class representing a cloud cluster print job constraint
class CloudClusterPrintJobConstraint(BaseCloudModel):
    def __init__(self, **kwargs) -> None:
        self.require_printer_name = None  # type: str
        super().__init__(**kwargs)
