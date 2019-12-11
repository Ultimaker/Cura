# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Dict, Any

from ..BaseModel import BaseModel


## Class representing the system status of a printer.
class PrinterSystemStatus(BaseModel):

    def __init__(self, guid: str, firmware: str, hostname: str, name: str, platform: str, variant: str,
                 hardware: Dict[str, Any], **kwargs
                 ) -> None:
        self.guid = guid
        self.firmware = firmware
        self.hostname = hostname
        self.name = name
        self.platform = platform
        self.variant = variant
        self.hardware = hardware
        super().__init__(**kwargs)
