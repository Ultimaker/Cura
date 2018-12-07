# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from .BaseCloudModel import BaseCloudModel


# Model that represents the responses received from the cloud after requesting a job to be printed.
class CloudPrintResponse(BaseCloudModel):
    def __init__(self, **kwargs) -> None:
        self.cluster_job_id = None  # type: str
        self.job_id = None  # type: str
        self.status = None  # type: str
        super().__init__(**kwargs)
