# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from datetime import datetime
from typing import List, Dict, Union, Any

from ..BaseModel import BaseModel
from .ClusterPrinterStatus import ClusterPrinterStatus
from .ClusterPrintJobStatus import ClusterPrintJobStatus


# Model that represents the status of the cluster for the cloud
class CloudClusterStatus(BaseModel):

    ## Creates a new cluster status model object.
    #  \param printers: The latest status of each printer in the cluster.
    #  \param print_jobs: The latest status of each print job in the cluster.
    #  \param generated_time: The datetime when the object was generated on the server-side.
    def __init__(self,
                 printers: List[Union[ClusterPrinterStatus, Dict[str, Any]]],
                 print_jobs: List[Union[ClusterPrintJobStatus, Dict[str, Any]]],
                 generated_time: Union[str, datetime],
                 **kwargs) -> None:
        self.generated_time = self.parseDate(generated_time)
        self.printers = self.parseModels(ClusterPrinterStatus, printers)
        self.print_jobs = self.parseModels(ClusterPrintJobStatus, print_jobs)
        super().__init__(**kwargs)
