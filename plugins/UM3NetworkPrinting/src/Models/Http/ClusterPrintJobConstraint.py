# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional

from ..BaseModel import BaseModel


class ClusterPrintJobConstraints(BaseModel):
    """Class representing a cloud cluster print job constraint"""

    def __init__(self, require_printer_name: Optional[str] = None, **kwargs) -> None:
        """Creates a new print job constraint.

        :param require_printer_name: Unique name of the printer that this job should be printed on.
        Should be one of the unique_name field values in the cluster, e.g. 'ultimakersystem-ccbdd30044ec'
        """
        self.require_printer_name = require_printer_name
        super().__init__(**kwargs)
