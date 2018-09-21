# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
import webbrowser
from typing import Optional
from urllib.parse import urlencode

# As this module is specific for Cura plugins, we can rely on these imports.
from UM.Logger import Logger
from UM.Signal import Signal

# Plugin imports need to be relative to work in final builds.
from .LocalAuthorizationServer import LocalAuthorizationServer
from .AuthorizationHelpers import AuthorizationHelpers
from .models import OAuth2Settings, AuthenticationResponse, UserProfile


class AuthorizationService:
    """
    The authorization service is responsible for handling the login flow,
    storing user credentials and providing account information.
    """

    # Emit signal when authentication is completed.
    onAuthStateChanged = Signal()

    # Emit signal when authentication failed.
    onAuthenticationError = Signal()

    def __init__(self, preferences, settings: "OAuth2Settings"):
        self._settings = settings
        self._auth_helpers = AuthorizationHelpers(settings)
        self._auth_url = "{}/authorize".format(self._settings.OAUTH_SERVER_URL)
        self._auth_data = None  # type: Optional[AuthenticationResponse]
        self._user_profile = None  # type: Optional[UserProfile]
        self._cura_preferences = preferences
        self._server = LocalAuthorizationServer(self._auth_helpers, self._onAuthStateChanged, daemon=True)
        self._loadAuthData()

    def getUserProfile(self) -> Optional["UserProfile"]:
        """
        Get the user data that is stored in the JWT token.
        :return: Dict containing some user data.
        """
        if not self._user_profile:
            # If no user profile was stored locally, we try to get it from JWT.
            self._user_profile = self._parseJWT()
        if not self._user_profile:
            # If there is still no user profile from the JWT, we have to log in again.
            return None
        return self._user_profile

    def _parseJWT(self) -> Optional["UserProfile"]:
        """
        Tries to parse the JWT if all the needed data exists.
        :return: UserProfile if found, otherwise None.
        """
        if not self._auth_data:
            # If no auth data exists, we should always log in again.
            return None
        user_data = self._auth_helpers.parseJWT(self._auth_data.access_token)
        if user_data:
            # If the profile was found, we return it immediately.
            return user_data
        # The JWT was expired or invalid and we should request a new one.
        self._auth_data = self._auth_helpers.getAccessTokenUsingRefreshToken(self._auth_data.refresh_token)
        if not self._auth_data:
            # The token could not be refreshed using the refresh token. We should login again.
            return None
        return self._auth_helpers.parseJWT(self._auth_data.access_token)

    def getAccessToken(self) -> Optional[str]:
        """
        Get the access token response data.
        :return: Dict containing token data.
        """
        if not self.getUserProfile():
            # We check if we can get the user profile.
            # If we can't get it, that means the access token (JWT) was invalid or expired.
            return None
        return self._auth_data.access_token

    def refreshAccessToken(self) -> None:
        """
        Refresh the access token when it expired.
        """
        self._storeAuthData(self._auth_helpers.getAccessTokenUsingRefreshToken(self._auth_data.refresh_token))
        self.onAuthStateChanged.emit(logged_in=True)

    def deleteAuthData(self):
        """Delete authentication data from preferences and locally."""
        self._storeAuthData()
        self.onAuthStateChanged.emit(logged_in=False)

    def startAuthorizationFlow(self) -> None:
        """Start a new OAuth2 authorization flow."""

        Logger.log("d", "Starting new OAuth2 flow...")

        # Create the tokens needed for the code challenge (PKCE) extension for OAuth2.
        # This is needed because the CuraDrivePlugin is a untrusted (open source) client.
        # More details can be found at https://tools.ietf.org/html/rfc7636.
        verification_code = self._auth_helpers.generateVerificationCode()
        challenge_code = self._auth_helpers.generateVerificationCodeChallenge(verification_code)

        # Create the query string needed for the OAuth2 flow.
        query_string = urlencode({
            "client_id": self._settings.CLIENT_ID,
            "redirect_uri": self._settings.CALLBACK_URL,
            "scope": self._settings.CLIENT_SCOPES,
            "response_type": "code",
            "state": "CuraDriveIsAwesome",
            "code_challenge": challenge_code,
            "code_challenge_method": "S512"
        })

        # Open the authorization page in a new browser window.
        webbrowser.open_new("{}?{}".format(self._auth_url, query_string))

        # Start a local web server to receive the callback URL on.
        self._server.start(verification_code)

    def _onAuthStateChanged(self, auth_response: "AuthenticationResponse") -> None:
        """Callback method for an authentication flow."""
        if auth_response.success:
            self._storeAuthData(auth_response)
            self.onAuthStateChanged.emit(logged_in=True)
        else:
            self.onAuthenticationError.emit(logged_in=False, error_message=auth_response.err_message)
        self._server.stop()  # Stop the web server at all times.

    def _loadAuthData(self) -> None:
        """Load authentication data from preferences if available."""
        self._cura_preferences.addPreference(self._settings.AUTH_DATA_PREFERENCE_KEY, "{}")
        try:
            preferences_data = json.loads(self._cura_preferences.getValue(self._settings.AUTH_DATA_PREFERENCE_KEY))
            if preferences_data:
                self._auth_data = AuthenticationResponse(**preferences_data)
                self.onAuthStateChanged.emit(logged_in=True)
        except ValueError as err:
            Logger.log("w", "Could not load auth data from preferences: %s", err)

    def _storeAuthData(self, auth_data: Optional["AuthenticationResponse"] = None) -> None:
        """Store authentication data in preferences and locally."""
        self._auth_data = auth_data
        if auth_data:
            self._user_profile = self.getUserProfile()
            self._cura_preferences.setValue(self._settings.AUTH_DATA_PREFERENCE_KEY, json.dumps(vars(auth_data)))
        else:
            self._user_profile = None
            self._cura_preferences.resetPreference(self._settings.AUTH_DATA_PREFERENCE_KEY)
