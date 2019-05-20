# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from datetime import datetime
from typing import List, Dict, Union, Any

from .CloudClusterPrinterStatus import CloudClusterPrinterStatus
from .CloudClusterPrintJobStatus import CloudClusterPrintJobStatus
from .BaseCloudModel import BaseCloudModel


# Model that represents the status of the cluster for the cloud
#  Spec: https://api-staging.ultimaker.com/connect/v1/spec
class CloudClusterStatus(BaseCloudModel):
    ## Creates a new cluster status model object.
    #  \param printers: The latest status of each printer in the cluster.
    #  \param print_jobs: The latest status of each print job in the cluster.
    #  \param generated_time: The datetime when the object was generated on the server-side.
    def __init__(self,
                 printers: List[Union[CloudClusterPrinterStatus, Dict[str, Any]]],
                 print_jobs: List[Union[CloudClusterPrintJobStatus, Dict[str, Any]]],
                 generated_time: Union[str, datetime],
                 **kwargs) -> None:
        self.generated_time = self.parseDate(generated_time)
        self.printers = self.parseModels(CloudClusterPrinterStatus, printers)
        self.print_jobs = self.parseModels(CloudClusterPrintJobStatus, print_jobs)
        super().__init__(**kwargs)
