# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from datetime import datetime
from typing import Optional

from .BaseModel import BaseModel

DIGITAL_FACTORY_RESPONSE_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class DigitalFactoryFileResponse(BaseModel):
    """Class representing a file in a digital factory project."""

    def __init__(self, client_id: str, content_type: str, file_id: str, file_name: str, library_project_id: str,
                 status: str, user_id: str, username: str,  uploaded_at: str, download_url: Optional[str] = "", status_description: Optional[str] = "",
                 file_size: Optional[int] = 0, upload_url: Optional[str] = "", **kwargs) -> None:
        """
        Creates a new DF file response object

        :param client_id:
        :param content_type:
        :param file_id:
        :param file_name:
        :param library_project_id:
        :param status:
        :param user_id:
        :param username:
        :param download_url:
        :param status_description:
        :param file_size:
        :param upload_url:
        :param kwargs:
        """

        self.client_id = client_id
        self.content_type = content_type
        self.download_url = download_url
        self.file_id = file_id
        self.file_name = file_name
        self.file_size = file_size
        self.library_project_id = library_project_id
        self.status = status
        self.status_description = status_description
        self.upload_url = upload_url
        self.user_id = user_id
        self.username = username
        self.uploaded_at = datetime.strptime(uploaded_at, DIGITAL_FACTORY_RESPONSE_DATETIME_FORMAT)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return "File: {}, from: {}, File ID: {}, Project ID: {}, Download URL: {}".format(self.file_name, self.username, self.file_id, self.library_project_id, self.download_url)

    # Validates the model, raising an exception if the model is invalid.
    def validate(self) -> None:
        super().validate()
        if not self.file_id:
            raise ValueError("file_id is required in Digital Library file")
