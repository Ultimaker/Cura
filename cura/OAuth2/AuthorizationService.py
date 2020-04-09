# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import json
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING
from urllib.parse import urlencode

import requests.exceptions
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from UM.Logger import Logger
from UM.Message import Message
from UM.Signal import Signal
from UM.i18n import i18nCatalog
from cura.OAuth2.AuthorizationHelpers import AuthorizationHelpers, TOKEN_TIMESTAMP_FORMAT
from cura.OAuth2.LocalAuthorizationServer import LocalAuthorizationServer
from cura.OAuth2.Models import AuthenticationResponse

i18n_catalog = i18nCatalog("cura")

if TYPE_CHECKING:
    from cura.OAuth2.Models import UserProfile, OAuth2Settings
    from UM.Preferences import Preferences


##  The authorization service is responsible for handling the login flow,
#   storing user credentials and providing account information.
class AuthorizationService:
    # Emit signal when authentication is completed.
    onAuthStateChanged = Signal()

    # Emit signal when authentication failed.
    onAuthenticationError = Signal()

    accessTokenChanged = Signal()

    def __init__(self, settings: "OAuth2Settings", preferences: Optional["Preferences"] = None) -> None:
        self._settings = settings
        self._auth_helpers = AuthorizationHelpers(settings)
        self._auth_url = "{}/authorize".format(self._settings.OAUTH_SERVER_URL)
        self._auth_data = None  # type: Optional[AuthenticationResponse]
        self._user_profile = None  # type: Optional["UserProfile"]
        self._preferences = preferences
        self._server = LocalAuthorizationServer(self._auth_helpers, self._onAuthStateChanged, daemon=True)

        self._unable_to_get_data_message = None  # type: Optional[Message]

        self.onAuthStateChanged.connect(self._authChanged)

    def _authChanged(self, logged_in):
        if logged_in and self._unable_to_get_data_message is not None:
            self._unable_to_get_data_message.hide()

    def initialize(self, preferences: Optional["Preferences"] = None) -> None:
        if preferences is not None:
            self._preferences = preferences
        if self._preferences:
            self._preferences.addPreference(self._settings.AUTH_DATA_PREFERENCE_KEY, "{}")

    ##  Get the user profile as obtained from the JWT (JSON Web Token).
    #   If the JWT is not yet parsed, calling this will take care of that.
    #   \return UserProfile if a user is logged in, None otherwise.
    #   \sa _parseJWT
    def getUserProfile(self) -> Optional["UserProfile"]:
        if not self._user_profile:
            # If no user profile was stored locally, we try to get it from JWT.
            try:
                self._user_profile = self._parseJWT()
            except requests.exceptions.ConnectionError:
                # Unable to get connection, can't login.
                Logger.logException("w", "Unable to validate user data with the remote server.")
                return None

        if not self._user_profile and self._auth_data:
            # If there is still no user profile from the JWT, we have to log in again.
            Logger.log("w", "The user profile could not be loaded. The user must log in again!")
            self.deleteAuthData()
            return None

        return self._user_profile

    ##  Tries to parse the JWT (JSON Web Token) data, which it does if all the needed data is there.
    #   \return UserProfile if it was able to parse, None otherwise.
    def _parseJWT(self) -> Optional["UserProfile"]:
        if not self._auth_data or self._auth_data.access_token is None:
            # If no auth data exists, we should always log in again.
            Logger.log("d", "There was no auth data or access token")
            return None
        user_data = self._auth_helpers.parseJWT(self._auth_data.access_token)
        if user_data:
            # If the profile was found, we return it immediately.
            return user_data
        # The JWT was expired or invalid and we should request a new one.
        if self._auth_data.refresh_token is None:
            Logger.log("w", "There was no refresh token in the auth data.")
            return None
        self._auth_data = self._auth_helpers.getAccessTokenUsingRefreshToken(self._auth_data.refresh_token)
        if not self._auth_data or self._auth_data.access_token is None:
            Logger.log("w", "Unable to use the refresh token to get a new access token.")
            # The token could not be refreshed using the refresh token. We should login again.
            return None
        # Ensure it gets stored as otherwise we only have it in memory. The stored refresh token has been deleted
        # from the server already.
        self._storeAuthData(self._auth_data)
        return self._auth_helpers.parseJWT(self._auth_data.access_token)

    ##  Get the access token as provided by the repsonse data.
    def getAccessToken(self) -> Optional[str]:
        if self._auth_data is None:
            Logger.log("d", "No auth data to retrieve the access_token from")
            return None

        # Check if the current access token is expired and refresh it if that is the case.
        # We have a fallback on a date far in the past for currently stored auth data in cura.cfg.
        received_at = datetime.strptime(self._auth_data.received_at, TOKEN_TIMESTAMP_FORMAT) \
            if self._auth_data.received_at else datetime(2000, 1, 1)
        expiry_date = received_at + timedelta(seconds = float(self._auth_data.expires_in or 0) - 60)
        if datetime.now() > expiry_date:
            self.refreshAccessToken()

        return self._auth_data.access_token if self._auth_data else None

    ##  Try to refresh the access token. This should be used when it has expired.
    def refreshAccessToken(self) -> None:
        if self._auth_data is None or self._auth_data.refresh_token is None:
            Logger.log("w", "Unable to refresh access token, since there is no refresh token.")
            return
        response = self._auth_helpers.getAccessTokenUsingRefreshToken(self._auth_data.refresh_token)
        if response.success:
            self._storeAuthData(response)
            self.onAuthStateChanged.emit(logged_in = True)
        else:
            Logger.log("w", "Failed to get a new access token from the server.")
            self.onAuthStateChanged.emit(logged_in = False)

    ##  Delete the authentication data that we have stored locally (eg; logout)
    def deleteAuthData(self) -> None:
        if self._auth_data is not None:
            self._storeAuthData()
            self.onAuthStateChanged.emit(logged_in = False)

    ##  Start the flow to become authenticated. This will start a new webbrowser tap, prompting the user to login.
    def startAuthorizationFlow(self) -> None:
        Logger.log("d", "Starting new OAuth2 flow...")

        # Create the tokens needed for the code challenge (PKCE) extension for OAuth2.
        # This is needed because the CuraDrivePlugin is a untrusted (open source) client.
        # More details can be found at https://tools.ietf.org/html/rfc7636.
        verification_code = self._auth_helpers.generateVerificationCode()
        challenge_code = self._auth_helpers.generateVerificationCodeChallenge(verification_code)

        state = AuthorizationHelpers.generateVerificationCode()

        # Create the query string needed for the OAuth2 flow.
        query_string = urlencode({
            "client_id": self._settings.CLIENT_ID,
            "redirect_uri": self._settings.CALLBACK_URL,
            "scope": self._settings.CLIENT_SCOPES,
            "response_type": "code",
            "state": state,  # Forever in our Hearts, RIP "(.Y.)" (2018-2020)
            "code_challenge": challenge_code,
            "code_challenge_method": "S512"
        })

        # Start a local web server to receive the callback URL on.
        try:
            self._server.start(verification_code, state)
        except OSError:
            Logger.logException("w", "Unable to create authorization request server")
            Message(i18n_catalog.i18nc("@info", "Unable to start a new sign in process. Check if another sign in attempt is still active."),
                    title=i18n_catalog.i18nc("@info:title", "Warning")).show()
            return

        # Open the authorization page in a new browser window.
        QDesktopServices.openUrl(QUrl("{}?{}".format(self._auth_url, query_string)))


    ##  Callback method for the authentication flow.
    def _onAuthStateChanged(self, auth_response: AuthenticationResponse) -> None:
        if auth_response.success:
            self._storeAuthData(auth_response)
            self.onAuthStateChanged.emit(logged_in = True)
        else:
            self.onAuthenticationError.emit(logged_in = False, error_message = auth_response.err_message)
        self._server.stop()  # Stop the web server at all times.

    ##  Load authentication data from preferences.
    def loadAuthDataFromPreferences(self) -> None:
        if self._preferences is None:
            Logger.log("e", "Unable to load authentication data, since no preference has been set!")
            return
        try:
            preferences_data = json.loads(self._preferences.getValue(self._settings.AUTH_DATA_PREFERENCE_KEY))
            if preferences_data:
                self._auth_data = AuthenticationResponse(**preferences_data)
                # Also check if we can actually get the user profile information.
                user_profile = self.getUserProfile()
                if user_profile is not None:
                    self.onAuthStateChanged.emit(logged_in = True)
                else:
                    if self._unable_to_get_data_message is not None:
                        self._unable_to_get_data_message.hide()

                    self._unable_to_get_data_message = Message(i18n_catalog.i18nc("@info", "Unable to reach the Ultimaker account server."), title = i18n_catalog.i18nc("@info:title", "Warning"))
                    self._unable_to_get_data_message.show()
        except ValueError:
            Logger.logException("w", "Could not load auth data from preferences")

    ##  Store authentication data in preferences.
    def _storeAuthData(self, auth_data: Optional[AuthenticationResponse] = None) -> None:
        Logger.log("d", "Attempting to store the auth data")
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

        self.accessTokenChanged.emit()

