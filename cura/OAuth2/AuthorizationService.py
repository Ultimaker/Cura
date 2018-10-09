# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
import webbrowser
from typing import Optional, TYPE_CHECKING
from urllib.parse import urlencode

from UM.Logger import Logger
from UM.Signal import Signal

from cura.OAuth2.LocalAuthorizationServer import LocalAuthorizationServer
from cura.OAuth2.AuthorizationHelpers import AuthorizationHelpers
from cura.OAuth2.Models import AuthenticationResponse

if TYPE_CHECKING:
    from cura.OAuth2.Models import UserProfile, OAuth2Settings
    from UM.Preferences import Preferences


class AuthorizationService:
    """
    The authorization service is responsible for handling the login flow,
    storing user credentials and providing account information.
    """

    # Emit signal when authentication is completed.
    onAuthStateChanged = Signal()

    # Emit signal when authentication failed.
    onAuthenticationError = Signal()

    def __init__(self, settings: "OAuth2Settings", preferences: Optional["Preferences"] = None) -> None:
        self._settings = settings
        self._auth_helpers = AuthorizationHelpers(settings)
        self._auth_url = "{}/authorize".format(self._settings.OAUTH_SERVER_URL)
        self._auth_data = None  # type: Optional[AuthenticationResponse]
        self._user_profile = None  # type: Optional["UserProfile"]
        self._preferences = preferences
        self._server = LocalAuthorizationServer(self._auth_helpers, self._onAuthStateChanged, daemon=True)

    def initialize(self, preferences: Optional["Preferences"] = None) -> None:
        if preferences is not None:
            self._preferences = preferences
        if self._preferences:
            self._preferences.addPreference(self._settings.AUTH_DATA_PREFERENCE_KEY, "{}")

    #   Get the user profile as obtained from the JWT (JSON Web Token).
    #   If the JWT is not yet parsed, calling this will take care of that.
    #   \return UserProfile if a user is logged in, None otherwise.
    #   \sa _parseJWT
    def getUserProfile(self) -> Optional["UserProfile"]:
        if not self._user_profile:
            # If no user profile was stored locally, we try to get it from JWT.
            self._user_profile = self._parseJWT()
        if not self._user_profile:
            # If there is still no user profile from the JWT, we have to log in again.
            return None

        return self._user_profile

    #   Tries to parse the JWT (JSON Web Token) data, which it does if all the needed data is there.
    #   \return UserProfile if it was able to parse, None otherwise.
    def _parseJWT(self) -> Optional["UserProfile"]:
        if not self._auth_data or self._auth_data.access_token is None:
            # If no auth data exists, we should always log in again.
            return None
        user_data = self._auth_helpers.parseJWT(self._auth_data.access_token)
        if user_data:
            # If the profile was found, we return it immediately.
            return user_data
        # The JWT was expired or invalid and we should request a new one.
        if self._auth_data.refresh_token is None:
            return None
        self._auth_data = self._auth_helpers.getAccessTokenUsingRefreshToken(self._auth_data.refresh_token)
        if not self._auth_data or self._auth_data.access_token is None:
            # The token could not be refreshed using the refresh token. We should login again.
            return None

        return self._auth_helpers.parseJWT(self._auth_data.access_token)

    #   Get the access token as provided by the repsonse data.
    def getAccessToken(self) -> Optional[str]:
        if not self.getUserProfile():
            # We check if we can get the user profile.
            # If we can't get it, that means the access token (JWT) was invalid or expired.
            return None

        if self._auth_data is None:
            return None

        return self._auth_data.access_token

    #   Try to refresh the access token. This should be used when it has expired.
    def refreshAccessToken(self) -> None:
        if self._auth_data is None or self._auth_data.refresh_token is None:
            Logger.log("w", "Unable to refresh access token, since there is no refresh token.")
            return
        self._storeAuthData(self._auth_helpers.getAccessTokenUsingRefreshToken(self._auth_data.refresh_token))
        self.onAuthStateChanged.emit(logged_in=True)

    #   Delete the authentication data that we have stored locally (eg; logout)
    def deleteAuthData(self) -> None:
        if self._auth_data is not None:
            self._storeAuthData()
            self.onAuthStateChanged.emit(logged_in=False)

    #   Start the flow to become authenticated. This will start a new webbrowser tap, prompting the user to login.
    def startAuthorizationFlow(self) -> None:
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

    #   Callback method for the authentication flow.
    def _onAuthStateChanged(self, auth_response: AuthenticationResponse) -> None:
        if auth_response.success:
            self._storeAuthData(auth_response)
            self.onAuthStateChanged.emit(logged_in=True)
        else:
            self.onAuthenticationError.emit(logged_in=False, error_message=auth_response.err_message)
        self._server.stop()  # Stop the web server at all times.

    #   Load authentication data from preferences.
    def loadAuthDataFromPreferences(self) -> None:
        if self._preferences is None:
            Logger.log("e", "Unable to load authentication data, since no preference has been set!")
            return
        try:
            preferences_data = json.loads(self._preferences.getValue(self._settings.AUTH_DATA_PREFERENCE_KEY))
            if preferences_data:
                self._auth_data = AuthenticationResponse(**preferences_data)
                self.onAuthStateChanged.emit(logged_in=True)
        except ValueError:
            Logger.logException("w", "Could not load auth data from preferences")

    #   Store authentication data in preferences.
    def _storeAuthData(self, auth_data: Optional[AuthenticationResponse] = None) -> None:
        if self._preferences is None:
            Logger.log("e", "Unable to save authentication data, since no preference has been set!")
            return
        
        self._auth_data = auth_data
        if auth_data:
            self._user_profile = self.getUserProfile()
            self._preferences.setValue(self._settings.AUTH_DATA_PREFERENCE_KEY, json.dumps(vars(auth_data)))
        else:
            self._user_profile = None
            self._preferences.resetPreference(self._settings.AUTH_DATA_PREFERENCE_KEY)
