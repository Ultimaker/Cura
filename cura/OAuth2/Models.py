# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional, Dict, Any


class BaseModel:
    def __init__(self, **kwargs: Any) -> None:
        self.__dict__.update(kwargs)


class OAuth2Settings(BaseModel):
    """OAuth OAuth2Settings data template."""

    CALLBACK_PORT = None  # type: Optional[int]
    OAUTH_SERVER_URL = None  # type: Optional[str]
    CLIENT_ID = None  # type: Optional[str]
    CLIENT_SCOPES = None  # type: Optional[str]
    CALLBACK_URL = None  # type: Optional[str]
    AUTH_DATA_PREFERENCE_KEY = ""  # type: str
    AUTH_SUCCESS_REDIRECT = "https://ultimaker.com"  # type: str
    AUTH_FAILED_REDIRECT = "https://ultimaker.com"  # type: str


class UserProfile(BaseModel):
    """User profile data template."""

    user_id = None  # type: Optional[str]
    username = None  # type: Optional[str]
    profile_image_url = None  # type: Optional[str]


class AuthenticationResponse(BaseModel):
    """Authentication data template."""

    # Data comes from the token response with success flag and error message added.
    success = True  # type: bool
    token_type = None  # type: Optional[str]
    access_token = None  # type: Optional[str]
    refresh_token = None  # type: Optional[str]
    expires_in = None  # type: Optional[str]
    scope = None  # type: Optional[str]
    err_message = None  # type: Optional[str]
    received_at = None  # type: Optional[str]


class ResponseStatus(BaseModel):
    """Response status template."""

    code = 200  # type: int
    message = ""  # type: str


class ResponseData(BaseModel):
    """Response data template."""

    status = None  # type: ResponseStatus
    data_stream = None  # type: Optional[bytes]
    redirect_uri = None  # type: Optional[str]
    content_type = "text/html"  # type: str


HTTP_STATUS = {
"""Possible HTTP responses."""

    "OK": ResponseStatus(code = 200, message = "OK"),
    "NOT_FOUND": ResponseStatus(code = 404, message = "NOT FOUND"),
    "REDIRECT": ResponseStatus(code = 302, message = "REDIRECT")
}  # type: Dict[str, ResponseStatus]
