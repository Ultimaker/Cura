# Copyright (c) 2024 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import json
from datetime import datetime, timedelta
from typing import Callable, Dict, Optional, TYPE_CHECKING, Union
from urllib.parse import urlencode, quote_plus

from PyQt6.QtCore import QUrl, QTimer
from PyQt6.QtGui import QDesktopServices

from UM.Logger import Logger
from UM.Message import Message
from UM.Signal import Signal
from UM.i18n import i18nCatalog
from UM.TaskManagement.HttpRequestManager import HttpRequestManager  # To download log-in tokens.
from cura.OAuth2.AuthorizationHelpers import AuthorizationHelpers, TOKEN_TIMESTAMP_FORMAT
from cura.OAuth2.LocalAuthorizationServer import LocalAuthorizationServer
from cura.OAuth2.Models import AuthenticationResponse, BaseModel

i18n_catalog = i18nCatalog("cura")

if TYPE_CHECKING:
    from cura.OAuth2.Models import UserProfile, OAuth2Settings
    from UM.Preferences import Preferences

MYCLOUD_LOGOFF_URL = "https://account.ultimaker.com/logoff?utm_source=cura&utm_medium=software&utm_campaign=change-account-before-adding-printers"

REFRESH_TOKEN_MAX_RETRIES = 15
REFRESH_TOKEN_RETRY_INTERVAL = 1000

class AuthorizationService:
    """The authorization service is responsible for handling the login flow, storing user credentials and providing
    account information.
    """

    def __init__(self,
                 settings: "OAuth2Settings",
                 preferences: Optional["Preferences"] = None,
                 get_user_profile: bool = True) -> None:
        # Emit signal when authentication is completed.
        self.onAuthStateChanged = Signal()

        # Emit signal when authentication failed.
        self.onAuthenticationError = Signal()

        self.accessTokenChanged = Signal()

        self._settings = settings
        self._auth_helpers = AuthorizationHelpers(settings)
        self._auth_url = "{}/authorize".format(self._settings.OAUTH_SERVER_URL)
        self._auth_data: Optional[AuthenticationResponse] = None
        self._user_profile: Optional["UserProfile"] = None
        self._get_user_profile: bool = get_user_profile
        self._preferences = preferences
        self._server = LocalAuthorizationServer(self._auth_helpers, self._onAuthStateChanged, daemon=True)
        self._currently_refreshing_token = False  # Whether we are currently in the process of refreshing auth. Don't make new requests while busy.

        self._unable_to_get_data_message: Optional[Message] = None

        self.onAuthStateChanged.connect(self._authChanged)

        self._refresh_token_retries = 0
        self._refresh_token_retry_timer = QTimer()
        self._refresh_token_retry_timer.setInterval(REFRESH_TOKEN_RETRY_INTERVAL)
        self._refresh_token_retry_timer.setSingleShot(True)
        self._refresh_token_retry_timer.timeout.connect(self.refreshAccessToken)

    def _authChanged(self, logged_in):
        if logged_in and self._unable_to_get_data_message is not None:
            self._unable_to_get_data_message.hide()

    def initialize(self, preferences: Optional["Preferences"] = None) -> None:
        if preferences is not None:
            self._preferences = preferences
        if self._preferences:
            self._preferences.addPreference(self._settings.AUTH_DATA_PREFERENCE_KEY, "{}")

    def getUserProfile(self, callback: Optional[Callable[[Optional["UserProfile"]], None]] = None) -> None:
        """
        Get the user profile as obtained from the JWT (JSON Web Token).

        If the JWT is not yet checked and parsed, calling this will take care of that.
        :param callback: Once the user profile is obtained, this function will be called with the given user profile. If
        the profile fails to be obtained, this function will be called with None.

        See also: :py:method:`cura.OAuth2.AuthorizationService.AuthorizationService._parseJWT`
        """
        if self._user_profile:
            # We already obtained the profile. No need to make another request for it.
            if callback is not None:
                callback(self._user_profile)
            return

        # If no user profile was stored locally, we try to get it from JWT.
        def store_profile(profile: Optional["UserProfile"]) -> None:
            if profile is not None:
                self._user_profile = profile
                if callback is not None:
                    callback(profile)
            elif self._auth_data:
                # If there is no user profile from the JWT, we have to log in again.
                Logger.warning("The user profile could not be loaded. The user must log in again!")
                self.deleteAuthData()
                if callback is not None:
                    callback(None)
            else:
                if callback is not None:
                    callback(None)

        self._parseJWT(callback = store_profile)

    def _parseJWT(self, callback: Callable[[Optional["UserProfile"]], None]) -> None:
        """
        Tries to parse the JWT (JSON Web Token) data, which it does if all the needed data is there.
        :param callback: A function to call asynchronously once the user profile has been obtained. It will be called
        with `None` if it failed to obtain a user profile.
        """

        if not self._auth_data or self._auth_data.access_token is None:
            # If no auth data exists, we should always log in again.
            Logger.debug("There was no auth data or access token")
            callback(None)
            return

        # When we checked the token we may get a user profile. This callback checks if that is a valid one and tries to refresh the token if it's not.
        def check_user_profile(user_profile: Optional["UserProfile"]) -> None:
            if user_profile:
                # If the profile was found, we call it back immediately.
                callback(user_profile)
                return
            # The JWT was expired or invalid and we should request a new one.
            if self._auth_data is None or self._auth_data.refresh_token is None:
                Logger.warning("There was no refresh token in the auth data.")
                callback(None)
                return

            def process_auth_data(auth_data: AuthenticationResponse) -> None:
                if auth_data.access_token is None:
                    Logger.warning("Unable to use the refresh token to get a new access token.")
                    callback(None)
                    return
                # Ensure it gets stored as otherwise we only have it in memory. The stored refresh token has been
                # deleted from the server already. Do not store the auth_data if we could not get new auth_data (e.g.
                # due to a network error), since this would cause an infinite loop trying to get new auth-data.
                if auth_data.success:
                    self._storeAuthData(auth_data)
                self._auth_helpers.checkToken(auth_data.access_token, callback, lambda: callback(None))

            self._auth_helpers.getAccessTokenUsingRefreshToken(self._auth_data.refresh_token, process_auth_data)

        self._auth_helpers.checkToken(self._auth_data.access_token, check_user_profile, lambda: check_user_profile(None))

    def getAccessToken(self) -> Optional[str]:
        """Get the access token as provided by the response data."""

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

    def refreshAccessToken(self) -> None:
        """Try to refresh the access token. This should be used when it has expired."""

        if self._auth_data is None or self._auth_data.refresh_token is None:
            Logger.log("w", "Unable to refresh access token, since there is no refresh token.")
            return

        def process_auth_data(response: AuthenticationResponse) -> None:
            self._currently_refreshing_token = False

            if response.success:
                self._refresh_token_retries = 0
                self._storeAuthData(response)
                HttpRequestManager.getInstance().setDelayRequests(False)
                self.onAuthStateChanged.emit(logged_in = True)
            else:
                if self._refresh_token_retries >= REFRESH_TOKEN_MAX_RETRIES:
                    self._refresh_token_retries = 0
                    Logger.warning("Failed to get a new access token from the server, giving up.")
                    HttpRequestManager.getInstance().setDelayRequests(False)
                    self.onAuthStateChanged.emit(logged_in = False)
                else:
                    # Retry a bit later, network may be offline right now and will hopefully be back soon
                    Logger.warning("Failed to get a new access token from the server, retrying later.")
                    self._refresh_token_retries += 1
                    self._refresh_token_retry_timer.start()

        if self._currently_refreshing_token:
            Logger.debug("Was already busy refreshing token. Do not start a new request.")
            return
        HttpRequestManager.getInstance().setDelayRequests(True)
        self._currently_refreshing_token = True
        self._auth_helpers.getAccessTokenUsingRefreshToken(self._auth_data.refresh_token, process_auth_data)

    def deleteAuthData(self) -> None:
        """Delete the authentication data that we have stored locally (eg; logout)"""

        if self._auth_data is not None:
            self._storeAuthData()
            self.onAuthStateChanged.emit(logged_in = False)

    def startAuthorizationFlow(self, force_browser_logout: bool = False) -> None:
        """Start the flow to become authenticated. This will start a new webbrowser tap, prompting the user to login."""

        Logger.log("d", "Starting new OAuth2 flow...")

        # Create the tokens needed for the code challenge (PKCE) extension for OAuth2.
        # This is needed because the CuraDrivePlugin is a untrusted (open source) client.
        # More details can be found at https://tools.ietf.org/html/rfc7636.
        verification_code = self._auth_helpers.generateVerificationCode()
        challenge_code = self._auth_helpers.generateVerificationCodeChallenge(verification_code)

        state = AuthorizationHelpers.generateVerificationCode()

        # Create the query dict needed for the OAuth2 flow.
        query_parameters_dict = {
            "client_id": self._settings.CLIENT_ID,
            "redirect_uri": self._settings.CALLBACK_URL,
            "scope": self._settings.CLIENT_SCOPES,
            "response_type": "code",
            "state": state,  # Forever in our Hearts, RIP "(.Y.)" (2018-2020)
            "code_challenge": challenge_code,
            "code_challenge_method": "S512"
        }

        # Start a local web server to receive the callback URL on.
        try:
            self._server.start(verification_code, state)
        except OSError:
            Logger.logException("w", "Unable to create authorization request server")
            Message(i18n_catalog.i18nc("@info",
                                       "Unable to start a new sign in process. Check if another sign in attempt is still active."),
                    title=i18n_catalog.i18nc("@info:title", "Warning"),
                    message_type = Message.MessageType.WARNING).show()
            return

        auth_url = self._generate_auth_url(query_parameters_dict, force_browser_logout)
        # Open the authorization page in a new browser window.
        QDesktopServices.openUrl(QUrl(auth_url))

    def _generate_auth_url(self, query_parameters_dict: Dict[str, Optional[str]], force_browser_logout: bool) -> str:
        """
        Generates the authentications url based on the original auth_url and the query_parameters_dict to be included.
        If there is a request to force logging out of mycloud in the browser, the link to logoff from mycloud is
        prepended in order to force the browser to logoff from mycloud and then redirect to the authentication url to
        login again. This case is used to sync the accounts between Cura and the browser.

        :param query_parameters_dict: A dictionary with the query parameters to be url encoded and added to the
                                      authentication link
        :param force_browser_logout: If True, Cura will prepend the MYCLOUD_LOGOFF_URL link before the authentication
                                     link to force the a browser logout from mycloud.ultimaker.com
        :return: The authentication URL, properly formatted and encoded
        """
        auth_url = f"{self._auth_url}?{urlencode(query_parameters_dict)}"
        if force_browser_logout:
            connecting_char = "&" if "?" in MYCLOUD_LOGOFF_URL else "?"
            # The url after 'next=' should be urlencoded
            auth_url = f"{MYCLOUD_LOGOFF_URL}{connecting_char}next={quote_plus(auth_url)}"
        return auth_url

    def _onAuthStateChanged(self, auth_response: AuthenticationResponse) -> None:
        """Callback method for the authentication flow."""
        if auth_response.success:
            Logger.log("d", "Got callback from Authorization state. The user should now be logged in!")
            self._storeAuthData(auth_response)
            self.onAuthStateChanged.emit(logged_in = True)
        else:
            Logger.log("d", "Got callback from Authorization state. Something went wrong: [%s]", auth_response.err_message)
            self.onAuthenticationError.emit(logged_in = False, error_message = auth_response.err_message)
        self._server.stop()  # Stop the web server at all times.

    def loadAuthDataFromPreferences(self) -> None:
        """Load authentication data from preferences."""
        Logger.log("d", "Attempting to load the auth data from preferences.")
        if self._preferences is None:
            Logger.log("e", "Unable to load authentication data, since no preference has been set!")
            return
        try:
            preferences_data = json.loads(self._preferences.getValue(self._settings.AUTH_DATA_PREFERENCE_KEY))
            if preferences_data:
                self._auth_data = AuthenticationResponse(**preferences_data)

                # Also check if we can actually get the user profile information.
                def callback(profile: Optional["UserProfile"]) -> None:
                    if profile is not None:
                        self.onAuthStateChanged.emit(logged_in = True)
                        Logger.debug("Auth data was successfully loaded")
                    else:
                        if self._unable_to_get_data_message is not None:
                            self._unable_to_get_data_message.show()
                        else:
                            self._unable_to_get_data_message = Message(i18n_catalog.i18nc("@info",
                                                                                          "Unable to reach the UltiMaker account server."),
                                                                       title = i18n_catalog.i18nc("@info:title", "Log-in failed"),
                                                                       message_type = Message.MessageType.ERROR)
                            Logger.warning("Unable to get user profile using auth data from preferences.")
                            self._unable_to_get_data_message.show()
                if self._get_user_profile:
                    self.getUserProfile(callback)
        except (ValueError, TypeError):
            Logger.logException("w", "Could not load auth data from preferences")

    def _storeAuthData(self, auth_data: Optional[AuthenticationResponse] = None) -> None:
        """Store authentication data in preferences."""

        Logger.log("d", "Attempting to store the auth data for [%s]", self._settings.OAUTH_SERVER_URL)
        if self._preferences is None:
            Logger.log("e", "Unable to save authentication data, since no preference has been set!")
            return

        self._auth_data = auth_data
        self._currently_refreshing_token = False
        if auth_data:
            if self._get_user_profile:
                self.getUserProfile()
            self._preferences.setValue(self._settings.AUTH_DATA_PREFERENCE_KEY, json.dumps(auth_data.dump()))
        else:
            Logger.log("d", "Clearing the user profile")
            self._user_profile = None
            self._preferences.resetPreference(self._settings.AUTH_DATA_PREFERENCE_KEY)

        self.accessTokenChanged.emit()
