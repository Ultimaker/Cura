# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from datetime import datetime
from typing import List

from .CloudClusterPrinter import CloudClusterPrinter
from .CloudClusterPrintJob import CloudClusterPrintJob
from .BaseCloudModel import BaseCloudModel


# Model that represents the status of the cluster for the cloud
class CloudClusterStatus(BaseCloudModel):
    def __init__(self, **kwargs) -> None:
        self.generated_time = None  # type: datetime
        # a list of the printers
        self.printers = []  # type: List[CloudClusterPrinter]
        # a list of the print jobs
        self.print_jobs = []  # type: List[CloudClusterPrintJob]

        super().__init__(**kwargs)

        # converting any dictionaries into models
        self.printers = [CloudClusterPrinter(**p) if isinstance(p, dict) else p for p in self.printers]
        self.print_jobs = [CloudClusterPrintJob(**j) if isinstance(j, dict) else j for j in self.print_jobs]

        # converting generated time into datetime
        if isinstance(self.generated_time, str):
            self.generated_time = self.parseDate(self.generated_time)
