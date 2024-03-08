# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from base64 import b64encode
from datetime import datetime
from hashlib import sha512
from PyQt6.QtNetwork import QNetworkReply
import secrets
from typing import Callable, Optional
import urllib.parse

from cura.OAuth2.Models import AuthenticationResponse, UserProfile, OAuth2Settings
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.TaskManagement.HttpRequestManager import HttpRequestManager  # To download log-in tokens.

catalog = i18nCatalog("cura")
TOKEN_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
REQUEST_TIMEOUT = 5 # Seconds


class AuthorizationHelpers:
    """Class containing several helpers to deal with the authorization flow."""

    def __init__(self, settings: "OAuth2Settings") -> None:
        self._settings = settings
        self._token_url = "{}/token".format(self._settings.OAUTH_SERVER_URL)

    @property
    def settings(self) -> "OAuth2Settings":
        """The OAuth2 settings object."""

        return self._settings

    def getAccessTokenUsingAuthorizationCode(self, authorization_code: str, verification_code: str, callback: Callable[[AuthenticationResponse], None]) -> None:
        """
        Request the access token from the authorization server.
        :param authorization_code: The authorization code from the 1st step.
        :param verification_code: The verification code needed for the PKCE extension.
        :param callback: Once the token has been obtained, this function will be called with the response.
        """
        data = {
            "client_id": self._settings.CLIENT_ID if self._settings.CLIENT_ID is not None else "",
            "client_secret": self._settings.CLIENT_SECRET if self._settings.CLIENT_SECRET is not None else "",
            "redirect_uri": self._settings.CALLBACK_URL if self._settings.CALLBACK_URL is not None else "",
            "grant_type": "authorization_code",
            "code": authorization_code,
            "code_verifier": verification_code,
            "scope": self._settings.CLIENT_SCOPES if self._settings.CLIENT_SCOPES is not None else "",
            }
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        HttpRequestManager.getInstance().post(
            self._token_url,
            data = urllib.parse.urlencode(data).encode("UTF-8"),
            headers_dict = headers,
            callback = lambda response: self.parseTokenResponse(response, callback),
            error_callback = lambda response, _: self.parseTokenResponse(response, callback),
            timeout = REQUEST_TIMEOUT
        )

    def getAccessTokenUsingRefreshToken(self, refresh_token: str, callback: Callable[[AuthenticationResponse], None]) -> None:
        """
        Request the access token from the authorization server using a refresh token.
        :param refresh_token: A long-lived token used to refresh the authentication token.
        :param callback: Once the token has been obtained, this function will be called with the response.
        """
        Logger.log("d", "Refreshing the access token for [%s]", self._settings.OAUTH_SERVER_URL)
        data = {
            "client_id": self._settings.CLIENT_ID if self._settings.CLIENT_ID is not None else "",
            "client_secret": self._settings.CLIENT_SECRET if self._settings.CLIENT_SECRET is not None else "",
            "redirect_uri": self._settings.CALLBACK_URL if self._settings.CALLBACK_URL is not None else "",
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": self._settings.CLIENT_SCOPES if self._settings.CLIENT_SCOPES is not None else "",
        }
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        HttpRequestManager.getInstance().post(
            self._token_url,
            data = urllib.parse.urlencode(data).encode("UTF-8"),
            headers_dict = headers,
            callback = lambda response: self.parseTokenResponse(response, callback),
            error_callback = lambda response, _: self.parseTokenResponse(response, callback),
            urgent = True,
            timeout = REQUEST_TIMEOUT
        )

    def parseTokenResponse(self, token_response: QNetworkReply, callback: Callable[[AuthenticationResponse], None]) -> None:
        """Parse the token response from the authorization server into an AuthenticationResponse object.

        :param token_response: The JSON string data response from the authorization server.
        :return: An AuthenticationResponse object.
        """
        token_data = HttpRequestManager.readJSON(token_response)
        if not token_data:
            callback(AuthenticationResponse(success = False, err_message = catalog.i18nc("@message", "Could not read response.")))
            return

        if token_response.error() != QNetworkReply.NetworkError.NoError:
            callback(AuthenticationResponse(success = False, err_message = token_data["error_description"]))
            return

        callback(AuthenticationResponse(success = True,
                                        token_type = token_data["token_type"],
                                        access_token = token_data["access_token"],
                                        refresh_token = token_data["refresh_token"],
                                        expires_in = token_data["expires_in"],
                                        scope = token_data["scope"],
                                        received_at = datetime.now().strftime(TOKEN_TIMESTAMP_FORMAT)))
        return

    def checkToken(self, access_token: str, success_callback: Optional[Callable[[UserProfile], None]] = None, failed_callback: Optional[Callable[[], None]] = None) -> None:
        """Calls the authentication API endpoint to get the token data.

        The API is called asynchronously. When a response is given, the callback is called with the user's profile.
        :param access_token: The encoded JWT token.
        :param success_callback: When a response is given, this function will be called with a user profile. If None,
        there will not be a callback.
        :param failed_callback: When the request failed or the response didn't parse, this function will be called.
        """
        check_token_url = "{}/check-token".format(self._settings.OAUTH_SERVER_URL)
        Logger.log("d", "Checking the access token for [%s]", check_token_url)
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        HttpRequestManager.getInstance().get(
            check_token_url,
            headers_dict = headers,
            callback = lambda reply: self._parseUserProfile(reply, success_callback, failed_callback),
            error_callback = lambda _, _2: failed_callback() if failed_callback is not None else None,
            timeout = REQUEST_TIMEOUT
        )

    def _parseUserProfile(self, reply: QNetworkReply, success_callback: Optional[Callable[[UserProfile], None]], failed_callback: Optional[Callable[[], None]] = None) -> None:
        """
        Parses the user profile from a reply to /check-token.

        If the response is valid, the callback will be called to return the user profile to the caller.
        :param reply: A network reply to a request to the /check-token URL.
        :param success_callback: A function to call once a user profile was successfully obtained.
        :param failed_callback: A function to call if parsing the profile failed.
        """
        if reply.error() != QNetworkReply.NetworkError.NoError:
            Logger.warning(f"Could not access account information. QNetworkError {reply.errorString()}")
            if failed_callback is not None:
                failed_callback()
            return

        profile_data = HttpRequestManager.getInstance().readJSON(reply)
        if profile_data is None or "data" not in profile_data:
            Logger.warning("Could not parse user data from token.")
            if failed_callback is not None:
                failed_callback()
            return
        profile_data = profile_data["data"]

        required_fields = {"user_id", "username"}
        if "user_id" not in profile_data or "username" not in profile_data:
            Logger.warning(f"User data missing required field(s): {required_fields - set(profile_data.keys())}")
            if failed_callback is not None:
                failed_callback()
            return

        if success_callback is not None:
            success_callback(UserProfile(
                user_id = profile_data["user_id"],
                username = profile_data["username"],
                profile_image_url = profile_data.get("profile_image_url", ""),
                organization_id = profile_data.get("organization", {}).get("organization_id"),
                subscriptions = profile_data.get("subscriptions", [])
            ))

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
