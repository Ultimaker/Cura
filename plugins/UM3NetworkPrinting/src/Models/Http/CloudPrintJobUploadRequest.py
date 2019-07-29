# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from ..BaseModel import BaseModel


# Model that represents the request to upload a print job to the cloud
class CloudPrintJobUploadRequest(BaseModel):

    ## Creates a new print job upload request.
    #  \param job_name: The name of the print job.
    #  \param file_size: The size of the file in bytes.
    #  \param content_type: The content type of the print job (e.g. text/plain or application/gzip)
    def __init__(self, job_name: str, file_size: int, content_type: str, **kwargs) -> None:
        self.job_name = job_name
        self.file_size = file_size
        self.content_type = content_type
        super().__init__(**kwargs)
