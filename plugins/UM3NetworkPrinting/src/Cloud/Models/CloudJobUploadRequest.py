# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from .BaseCloudModel import BaseCloudModel


# Model that represents the request to upload a print job to the cloud
class CloudJobUploadRequest(BaseCloudModel):
    def __init__(self, **kwargs) -> None:
        self.file_size = None  # type: int
        self.job_name = None  # type: str
        self.content_type = None  # type: str
        super().__init__(**kwargs)
