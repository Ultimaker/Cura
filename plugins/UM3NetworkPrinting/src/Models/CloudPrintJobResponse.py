# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional

from .BaseCloudModel import BaseCloudModel


# Model that represents the response received from the cloud after requesting to upload a print job
#  Spec: https://api-staging.ultimaker.com/cura/v1/spec
class CloudPrintJobResponse(BaseCloudModel):
    ## Creates a new print job response model.
    #  \param job_id: The job unique ID, e.g. 'kBEeZWEifXbrXviO8mRYLx45P8k5lHVGs43XKvRniPg='.
    #  \param status: The status of the print job.
    #  \param status_description: Contains more details about the status, e.g. the cause of failures.
    #  \param download_url: A signed URL to download the resulting status. Only available when the job is finished.
    #  \param job_name: The name of the print job.
    #  \param slicing_details: Model for slice information.
    #  \param upload_url: The one-time use URL where the toolpath must be uploaded to (only if status is uploading).
    #  \param content_type: The content type of the print job (e.g. text/plain or application/gzip)
    #  \param generated_time: The datetime when the object was generated on the server-side.
    def __init__(self, job_id: str, status: str, download_url: Optional[str] = None, job_name: Optional[str] = None,
                 upload_url: Optional[str] = None, content_type: Optional[str] = None,
                 status_description: Optional[str] = None, slicing_details: Optional[dict] = None, **kwargs) -> None:
        self.job_id = job_id
        self.status = status
        self.download_url = download_url
        self.job_name = job_name
        self.upload_url = upload_url
        self.content_type = content_type
        self.status_description = status_description
        # TODO: Implement slicing details
        self.slicing_details = slicing_details
        super().__init__(**kwargs)
