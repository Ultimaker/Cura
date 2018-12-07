# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from .BaseCloudModel import BaseCloudModel


# Model that represents the response received from the cloud after requesting to upload a print job
class CloudJobResponse(BaseCloudModel):
    def __init__(self, **kwargs) -> None:
        self.download_url = None  # type: str
        self.job_id = None  # type: str
        self.job_name = None  # type: str
        self.slicing_details = None  # type: str
        self.status = None  # type: str
        self.upload_url = None  # type: str
        self.content_type = None  # type: str
        super().__init__(**kwargs)
