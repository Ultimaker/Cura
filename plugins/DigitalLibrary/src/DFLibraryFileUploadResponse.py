# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from datetime import datetime
from typing import Optional

from .BaseModel import BaseModel


class DFLibraryFileUploadResponse(BaseModel):
    """
    Model that represents the response received from the Digital Factory after requesting to upload a file in a Library project
    """

    def __init__(self, client_id: str, content_type: str, file_id: str, file_name: str, library_project_id: str,
                 status: str, uploaded_at: str, user_id: str, username: str, download_url: Optional[str] = None,
                 file_size: Optional[int] = None, status_description: Optional[str] = None,
                 upload_url: Optional[str] = None, **kwargs) -> None:

        """
        :param client_id: The ID of the OAuth2 client that uploaded this file
        :param content_type: The content type of the Digital Library project file
        :param file_id: The ID of the library project file
        :param file_name: The name of the file
        :param library_project_id: The ID of the library project, in which the file will be uploaded
        :param status: The status of the Digital Library project file
        :param uploaded_at: The time on which the file was uploaded
        :param user_id: The ID of the user that uploaded this file
        :param username: The user's unique username
        :param download_url: A signed URL to download the resulting file. Only available when the job is finished
        :param file_size: The size of the uploaded file (in bytes)
        :param status_description: Contains more details about the status, e.g. the cause of failures
        :param upload_url: The one-time use URL where the file must be uploaded to (only if status is uploading)
        :param kwargs: Other keyword arguments that may be included in the response
        """

        self.client_id = client_id  # type: str
        self.content_type = content_type  # type: str
        self.file_id = file_id  # type: str
        self.file_name = file_name  # type: str
        self.library_project_id = library_project_id  # type: str
        self.status = status  # type: str
        self.uploaded_at = self.parseDate(uploaded_at)  # type: datetime
        self.user_id = user_id  # type: str
        self.username = username  # type: str
        self.download_url = download_url  # type: Optional[str]
        self.file_size = file_size  # type: Optional[int]
        self.status_description = status_description  # type: Optional[str]
        self.upload_url = upload_url  # type: Optional[str]
        super().__init__(**kwargs)
