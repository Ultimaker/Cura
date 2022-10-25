# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional

from .BaseModel import BaseModel


# Model that represents the request to upload a print job to the cloud
class DFPrintJobUploadRequest(BaseModel):

    def __init__(self, job_name: str, file_size: int, content_type: str, library_project_id: str, source_file_id: str, **kwargs) -> None:
        """Creates a new print job upload request.

        :param job_name: The name of the print job.
        :param file_size: The size of the file in bytes.
        :param content_type: The content type of the print job (e.g. text/plain or application/gzip)
        """

        self.job_name = job_name
        self.file_size = file_size
        self.content_type = content_type
        self.library_project_id = library_project_id
        self.source_file_id = source_file_id
        super().__init__(**kwargs)
