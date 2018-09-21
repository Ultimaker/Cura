# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
import random
from _sha512 import sha512
from base64 import b64encode
from typing import Optional

import requests

from UM.Logger import Logger

from cura.OAuth2.Models import AuthenticationResponse, UserProfile, OAuth2Settings


class AuthorizationHelpers:
    """Class containing several helpers to deal with the authorization flow."""

    def __init__(self, settings: "OAuth2Settings"):
        self._settings = settings
        self._token_url = "{}/token".format(self._settings.OAUTH_SERVER_URL)

    @property
    def settings(self) -> "OAuth2Settings":
        """Get the OAuth2 settings object."""
        return self._settings

    def getAccessTokenUsingAuthorizationCode(self, authorization_code: str, verification_code: str)->\
            Optional["AuthenticationResponse"]:
        """
        Request the access token from the authorization server.
        :param authorization_code: The authorization code from the 1st step.
        :param verification_code: The verification code needed for the PKCE extension.
        :return: An AuthenticationResponse object.
        """
        return self.parseTokenResponse(requests.post(self._token_url, data={
            "client_id": self._settings.CLIENT_ID,
            "redirect_uri": self._settings.CALLBACK_URL,
            "grant_type": "authorization_code",
            "code": authorization_code,
            "code_verifier": verification_code,
            "scope": self._settings.CLIENT_SCOPES
        }))

    def getAccessTokenUsingRefreshToken(self, refresh_token: str) -> Optional["AuthenticationResponse"]:
        """
        Request the access token from the authorization server using a refresh token.
        :param refresh_token:
        :return: An AuthenticationResponse object.
        """
        return self.parseTokenResponse(requests.post(self._token_url, data={
            "client_id": self._settings.CLIENT_ID,
            "redirect_uri": self._settings.CALLBACK_URL,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": self._settings.CLIENT_SCOPES
        }))

    @staticmethod
    def parseTokenResponse(token_response: "requests.request") -> Optional["AuthenticationResponse"]:
        """
        Parse the token response from the authorization server into an AuthenticationResponse object.
        :param token_response: The JSON string data response from the authorization server.
        :return: An AuthenticationResponse object.
        """
        token_data = None

        try:
            token_data = json.loads(token_response.text)
        except ValueError:
            Logger.log("w", "Could not parse token response data: %s", token_response.text)

        if not token_data:
            return AuthenticationResponse(success=False, err_message="Could not read response.")

        if token_response.status_code not in (200, 201):
            return AuthenticationResponse(success=False, err_message=token_data["error_description"])

        return AuthenticationResponse(success=True,
                                      token_type=token_data["token_type"],
                                      access_token=token_data["access_token"],
                                      refresh_token=token_data["refresh_token"],
                                      expires_in=token_data["expires_in"],
                                      scope=token_data["scope"])

    def parseJWT(self, access_token: str) -> Optional["UserProfile"]:
        """
        Calls the authentication API endpoint to get the token data.
        :param access_token: The encoded JWT token.
        :return: Dict containing some profile data.
        """
        token_request = requests.get("{}/check-token".format(self._settings.OAUTH_SERVER_URL), headers = {
            "Authorization": "Bearer {}".format(access_token)
        })
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
            profile_image_url = user_data.get("profile_image_url", "")
        )

    @staticmethod
    def generateVerificationCode(code_length: int = 16) -> str:
        """
        Generate a 16-character verification code.
        :param code_length:
        :return:
        """
        return "".join(random.choice("0123456789ABCDEF") for i in range(code_length))

    @staticmethod
    def generateVerificationCodeChallenge(verification_code: str) -> str:
        """
        Generates a base64 encoded sha512 encrypted version of a given string.
        :param verification_code:
        :return: The encrypted code in base64 format.
        """
        encoded = sha512(verification_code.encode()).digest()
        return b64encode(encoded, altchars = b"_-").decode()
