# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from datetime import datetime
import json
import secrets
from hashlib import sha512
from base64 import b64encode
from typing import Optional
import requests

from UM.i18n import i18nCatalog
from UM.Logger import Logger

from cura.OAuth2.Models import AuthenticationResponse, UserProfile, OAuth2Settings
catalog = i18nCatalog("cura")
TOKEN_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


class AuthorizationHelpers:
    """Class containing several helpers to deal with the authorization flow."""

    def __init__(self, settings: "OAuth2Settings") -> None:
        self._settings = settings
        self._token_url = "{}/token".format(self._settings.OAUTH_SERVER_URL)

    @property
    def settings(self) -> "OAuth2Settings":
        """The OAuth2 settings object."""

        return self._settings

    def getAccessTokenUsingAuthorizationCode(self, authorization_code: str, verification_code: str) -> "AuthenticationResponse":
        """Request the access token from the authorization server.

        :param authorization_code: The authorization code from the 1st step.
        :param verification_code: The verification code needed for the PKCE extension.
        :return: An AuthenticationResponse object.
        """

        data = {
            "client_id": self._settings.CLIENT_ID if self._settings.CLIENT_ID is not None else "",
            "redirect_uri": self._settings.CALLBACK_URL if self._settings.CALLBACK_URL is not None else "",
            "grant_type": "authorization_code",
            "code": authorization_code,
            "code_verifier": verification_code,
            "scope": self._settings.CLIENT_SCOPES if self._settings.CLIENT_SCOPES is not None else "",
            }
        try:
            return self.parseTokenResponse(requests.post(self._token_url, data = data))  # type: ignore
        except requests.exceptions.ConnectionError as connection_error:
            return AuthenticationResponse(success = False, err_message = f"Unable to connect to remote server: {connection_error}")

    def getAccessTokenUsingRefreshToken(self, refresh_token: str) -> "AuthenticationResponse":
        """Request the access token from the authorization server using a refresh token.

        :param refresh_token:
        :return: An AuthenticationResponse object.
        """

        Logger.log("d", "Refreshing the access token for [%s]", self._settings.OAUTH_SERVER_URL)
        data = {
            "client_id": self._settings.CLIENT_ID if self._settings.CLIENT_ID is not None else "",
            "redirect_uri": self._settings.CALLBACK_URL if self._settings.CALLBACK_URL is not None else "",
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": self._settings.CLIENT_SCOPES if self._settings.CLIENT_SCOPES is not None else "",
        }
        try:
            return self.parseTokenResponse(requests.post(self._token_url, data = data))  # type: ignore
        except requests.exceptions.ConnectionError:
            return AuthenticationResponse(success = False, err_message = "Unable to connect to remote server")
        except OSError as e:
            return AuthenticationResponse(success = False, err_message = "Operating system is unable to set up a secure connection: {err}".format(err = str(e)))

    @staticmethod
    def parseTokenResponse(token_response: requests.models.Response) -> "AuthenticationResponse":
        """Parse the token response from the authorization server into an AuthenticationResponse object.

        :param token_response: The JSON string data response from the authorization server.
        :return: An AuthenticationResponse object.
        """

        token_data = None

        try:
            token_data = json.loads(token_response.text)
        except ValueError:
            Logger.log("w", "Could not parse token response data: %s", token_response.text)

        if not token_data:
            return AuthenticationResponse(success = False, err_message = catalog.i18nc("@message", "Could not read response."))

        if token_response.status_code not in (200, 201):
            return AuthenticationResponse(success = False, err_message = token_data["error_description"])

        return AuthenticationResponse(success=True,
                                      token_type=token_data["token_type"],
                                      access_token=token_data["access_token"],
                                      refresh_token=token_data["refresh_token"],
                                      expires_in=token_data["expires_in"],
                                      scope=token_data["scope"],
                                      received_at=datetime.now().strftime(TOKEN_TIMESTAMP_FORMAT))

    def parseJWT(self, access_token: str) -> Optional["UserProfile"]:
        """Calls the authentication API endpoint to get the token data.

        :param access_token: The encoded JWT token.
        :return: Dict containing some profile data.
        """

        try:
            check_token_url = "{}/check-token".format(self._settings.OAUTH_SERVER_URL)
            Logger.log("d", "Checking the access token for [%s]", check_token_url)
            token_request = requests.get(check_token_url, headers = {
                "Authorization": "Bearer {}".format(access_token)
            })
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            # Connection was suddenly dropped. Nothing we can do about that.
            Logger.logException("w", "Something failed while attempting to parse the JWT token")
            return None
        if token_request.status_code not in (200, 201):
            Logger.log("w", "Could not retrieve token data from auth server: %s", token_request.text)
            return None
        user_data = token_request.json().get("data")
        if not user_data or not isinstance(user_data, dict):
            Logger.log("w", "Could not parse user data from token: %s", user_data)
            return None

        return UserProfile(
            user_id = user_data["user_id"],
            username = user_data["username"],
            profile_image_url = user_data.get("profile_image_url", ""),
            organization_id = user_data.get("organization", {}).get("organization_id"),
            subscriptions = user_data.get("subscriptions", [])
        )

    @staticmethod
    def generateVerificationCode(code_length: int = 32) -> str:
        """Generate a verification code of arbitrary length.

        :param code_length:: How long should the code be in bytes? This should never be lower than 16, but it's probably
        better to leave it at 32
        """

        return secrets.token_hex(code_length)

    @staticmethod
    def generateVerificationCodeChallenge(verification_code: str) -> str:
        """Generates a base64 encoded sha512 encrypted version of a given string.

        :param verification_code:
        :return: The encrypted code in base64 format.
        """

        encoded = sha512(verification_code.encode()).digest()
        return b64encode(encoded, altchars = b"_-").decode()
