# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

from PyQt5.QtGui import QDesktopServices
from PyQt5.QtNetwork import QNetworkReply

from UM.Preferences import Preferences
from cura.OAuth2.AuthorizationHelpers import AuthorizationHelpers, TOKEN_TIMESTAMP_FORMAT
from cura.OAuth2.AuthorizationService import AuthorizationService, MYCLOUD_LOGOFF_URL
from cura.OAuth2.LocalAuthorizationServer import LocalAuthorizationServer
from cura.OAuth2.Models import OAuth2Settings, AuthenticationResponse, UserProfile

CALLBACK_PORT = 32118
OAUTH_ROOT = "https://account.ultimaker.com"
CLOUD_API_ROOT = "https://api.ultimaker.com"

OAUTH_SETTINGS = OAuth2Settings(
    OAUTH_SERVER_URL= OAUTH_ROOT,
    CALLBACK_PORT=CALLBACK_PORT,
    CALLBACK_URL="http://localhost:{}/callback".format(CALLBACK_PORT),
    CLIENT_ID="",
    CLIENT_SCOPES="",
    AUTH_DATA_PREFERENCE_KEY="test/auth_data",
    AUTH_SUCCESS_REDIRECT="{}/app/auth-success".format(OAUTH_ROOT),
    AUTH_FAILED_REDIRECT="{}/app/auth-error".format(OAUTH_ROOT)
)

FAILED_AUTH_RESPONSE = AuthenticationResponse(
    success = False,
    err_message = "FAILURE!"
)

SUCCESSFUL_AUTH_RESPONSE = AuthenticationResponse(
    access_token = "beep",
    refresh_token = "beep?",
    received_at = datetime.now().strftime(TOKEN_TIMESTAMP_FORMAT),
    expires_in = 300,  # 5 minutes should be more than enough for testing
    success = True
)

EXPIRED_AUTH_RESPONSE = AuthenticationResponse(
    access_token = "expired",
    refresh_token = "beep?",
    received_at = datetime.now().strftime(TOKEN_TIMESTAMP_FORMAT),
    expires_in = 300,  # 5 minutes should be more than enough for testing
    success = True
)

NO_REFRESH_AUTH_RESPONSE = AuthenticationResponse(
    access_token = "beep",
    received_at = datetime.now().strftime(TOKEN_TIMESTAMP_FORMAT),
    expires_in = 300,  # 5 minutes should be more than enough for testing
    success = True
)

MALFORMED_AUTH_RESPONSE = AuthenticationResponse(success=False)


def test_cleanAuthService() -> None:
    """
    Ensure that when setting up an AuthorizationService, no data is set.
    """
    authorization_service = AuthorizationService(OAUTH_SETTINGS, Preferences())
    authorization_service.initialize()

    mock_callback = Mock()
    authorization_service.getUserProfile(mock_callback)
    mock_callback.assert_called_once_with(None)

    assert authorization_service.getAccessToken() is None

def test_refreshAccessTokenSuccess():
    authorization_service = AuthorizationService(OAUTH_SETTINGS, Preferences())
    authorization_service.initialize()
    with patch.object(AuthorizationService, "getUserProfile", return_value=UserProfile()):
        authorization_service._storeAuthData(SUCCESSFUL_AUTH_RESPONSE)
    authorization_service.onAuthStateChanged.emit = MagicMock()

    with patch.object(AuthorizationHelpers, "getAccessTokenUsingRefreshToken", return_value=SUCCESSFUL_AUTH_RESPONSE):
        authorization_service.refreshAccessToken()
        assert authorization_service.onAuthStateChanged.emit.called_with(True)

def test__parseJWTNoRefreshToken():
    """
    Tests parsing the user profile if there is no refresh token stored, but there is a normal authentication token.

    The request for the user profile using the authentication token should still work normally.
    """
    authorization_service = AuthorizationService(OAUTH_SETTINGS, Preferences())
    with patch.object(AuthorizationService, "getUserProfile", return_value = UserProfile()):
        authorization_service._storeAuthData(NO_REFRESH_AUTH_RESPONSE)

    mock_callback = Mock()  # To log the final profile response.
    mock_reply = Mock()  # The user profile that the service should respond with.
    mock_reply.error = Mock(return_value = QNetworkReply.NetworkError.NoError)
    http_mock = Mock()
    http_mock.get = lambda url, headers_dict, callback, error_callback: callback(mock_reply)
    http_mock.readJSON = Mock(return_value = {"data": {"user_id": "id_ego_or_superego", "username": "Ghostkeeper"}})

    with patch("UM.TaskManagement.HttpRequestManager.HttpRequestManager.getInstance", MagicMock(return_value = http_mock)):
        authorization_service._parseJWT(mock_callback)
    mock_callback.assert_called_once()
    profile_reply = mock_callback.call_args_list[0][0][0]
    assert profile_reply.user_id == "id_ego_or_superego"
    assert profile_reply.username == "Ghostkeeper"

def test__parseJWTFailOnRefresh():
    """
    Tries to refresh the authentication token using an invalid refresh token. The request should fail.
    """
    authorization_service = AuthorizationService(OAUTH_SETTINGS, Preferences())
    with patch.object(AuthorizationService, "getUserProfile", return_value = UserProfile()):
        authorization_service._storeAuthData(SUCCESSFUL_AUTH_RESPONSE)

    mock_callback = Mock()  # To log the final profile response.
    mock_reply = Mock()  # The response that the request should give, containing an error about it failing to authenticate.
    mock_reply.error = Mock(return_value = QNetworkReply.NetworkError.AuthenticationRequiredError)  # The reply is 403: Authentication required, meaning the server responded with a "Can't do that, Dave".
    http_mock = Mock()
    http_mock.get = lambda url, headers_dict, callback, error_callback: callback(mock_reply)
    http_mock.post = lambda url, data, headers_dict, callback, error_callback: callback(mock_reply)

    with patch("UM.TaskManagement.HttpRequestManager.HttpRequestManager.readJSON", Mock(return_value = {"error_description": "Mock a failed request!"})):
        with patch("UM.TaskManagement.HttpRequestManager.HttpRequestManager.getInstance", MagicMock(return_value = http_mock)):
            authorization_service._parseJWT(mock_callback)
    mock_callback.assert_called_once_with(None)

def test__parseJWTSucceedOnRefresh():
    """
    Tries to refresh the authentication token using a valid refresh token. The request should succeed.
    """
    authorization_service = AuthorizationService(OAUTH_SETTINGS, Preferences())
    authorization_service.initialize()
    with patch.object(AuthorizationService, "getUserProfile", return_value = UserProfile()):
        authorization_service._storeAuthData(EXPIRED_AUTH_RESPONSE)

    mock_callback = Mock()  # To log the final profile response.
    mock_reply_success = Mock()  # The reply should be a failure when using the expired access token, but succeed when using the refresh token.
    mock_reply_success.error = Mock(return_value = QNetworkReply.NetworkError.NoError)
    mock_reply_failure = Mock()
    mock_reply_failure.error = Mock(return_value = QNetworkReply.NetworkError.AuthenticationRequiredError)
    http_mock = Mock()
    def mock_get(url, headers_dict, callback, error_callback):
        if(headers_dict == {"Authorization": "Bearer beep"}):
            callback(mock_reply_success)
        else:
            callback(mock_reply_failure)
    http_mock.get = mock_get
    http_mock.readJSON = Mock(return_value = {"data": {"user_id": "user_idea", "username": "Ghostkeeper"}})
    def mock_refresh(self, refresh_token, callback):  # Refreshing gives a valid token.
        callback(SUCCESSFUL_AUTH_RESPONSE)

    with patch("cura.OAuth2.AuthorizationHelpers.AuthorizationHelpers.getAccessTokenUsingRefreshToken", mock_refresh):
        with patch("UM.TaskManagement.HttpRequestManager.HttpRequestManager.getInstance", MagicMock(return_value = http_mock)):
            authorization_service._parseJWT(mock_callback)

    mock_callback.assert_called_once()
    profile_reply = mock_callback.call_args_list[0][0][0]
    assert profile_reply.user_id == "user_idea"
    assert profile_reply.username == "Ghostkeeper"

def test_initialize():
    original_preference = MagicMock()
    initialize_preferences = MagicMock()
    authorization_service = AuthorizationService(OAUTH_SETTINGS, original_preference)
    authorization_service.initialize(initialize_preferences)
    initialize_preferences.addPreference.assert_called_once_with("test/auth_data", "{}")
    original_preference.addPreference.assert_not_called()

def test_refreshAccessTokenFailed():
    """
    Test if the authentication is reset once the refresh token fails to refresh access.
    """
    authorization_service = AuthorizationService(OAUTH_SETTINGS, Preferences())
    authorization_service.initialize()

    def mock_refresh(self, refresh_token, callback):  # Refreshing gives a valid token.
        callback(FAILED_AUTH_RESPONSE)
    mock_reply = Mock()  # The response that the request should give, containing an error about it failing to authenticate.
    mock_reply.error = Mock(return_value = QNetworkReply.NetworkError.AuthenticationRequiredError)  # The reply is 403: Authentication required, meaning the server responded with a "Can't do that, Dave".
    http_mock = Mock()
    http_mock.get = lambda url, headers_dict, callback, error_callback: callback(mock_reply)
    http_mock.post = lambda url, data, headers_dict, callback, error_callback: callback(mock_reply)

    with patch("UM.TaskManagement.HttpRequestManager.HttpRequestManager.readJSON", Mock(return_value = {"error_description": "Mock a failed request!"})):
        with patch("UM.TaskManagement.HttpRequestManager.HttpRequestManager.getInstance", MagicMock(return_value = http_mock)):
            authorization_service._storeAuthData(SUCCESSFUL_AUTH_RESPONSE)
            authorization_service.onAuthStateChanged.emit = MagicMock()
            with patch("cura.OAuth2.AuthorizationHelpers.AuthorizationHelpers.getAccessTokenUsingRefreshToken", mock_refresh):
                authorization_service.refreshAccessToken()
                assert authorization_service.onAuthStateChanged.emit.called_with(False)

def test_refreshAccesTokenWithoutData():
    authorization_service = AuthorizationService(OAUTH_SETTINGS, Preferences())
    authorization_service.initialize()
    authorization_service.onAuthStateChanged.emit = MagicMock()
    authorization_service.refreshAccessToken()
    authorization_service.onAuthStateChanged.emit.assert_not_called()

def test_failedLogin() -> None:
    authorization_service = AuthorizationService(OAUTH_SETTINGS, Preferences())
    authorization_service.onAuthenticationError.emit = MagicMock()
    authorization_service.onAuthStateChanged.emit = MagicMock()
    authorization_service.initialize()

    # Let the service think there was a failed response
    authorization_service._onAuthStateChanged(FAILED_AUTH_RESPONSE)

    # Check that the error signal was triggered
    assert authorization_service.onAuthenticationError.emit.call_count == 1

    # Since nothing changed, this should still be 0.
    assert authorization_service.onAuthStateChanged.emit.call_count == 0

    # Validate that there is no user profile or token
    assert authorization_service.getUserProfile() is None
    assert authorization_service.getAccessToken() is None

@patch.object(AuthorizationService, "getUserProfile")
def test_storeAuthData(get_user_profile) -> None:
    preferences = Preferences()
    authorization_service = AuthorizationService(OAUTH_SETTINGS, preferences)
    authorization_service.initialize()

    # Write stuff to the preferences.
    authorization_service._storeAuthData(SUCCESSFUL_AUTH_RESPONSE)
    preference_value = preferences.getValue(OAUTH_SETTINGS.AUTH_DATA_PREFERENCE_KEY)
    # Check that something was actually put in the preferences
    assert preference_value is not None and preference_value != {}

    # Create a second auth service, so we can load the data.
    second_auth_service = AuthorizationService(OAUTH_SETTINGS, preferences)
    second_auth_service.initialize()
    second_auth_service.loadAuthDataFromPreferences()
    assert second_auth_service.getAccessToken() == SUCCESSFUL_AUTH_RESPONSE.access_token

@patch.object(LocalAuthorizationServer, "stop")
@patch.object(LocalAuthorizationServer, "start")
@patch.object(QDesktopServices, "openUrl")
def test_localAuthServer(QDesktopServices_openUrl, start_auth_server, stop_auth_server) -> None:
    preferences = Preferences()
    authorization_service = AuthorizationService(OAUTH_SETTINGS, preferences)
    authorization_service.startAuthorizationFlow()
    assert QDesktopServices_openUrl.call_count == 1

    # Ensure that the Authorization service tried to start the server.
    assert start_auth_server.call_count == 1
    assert stop_auth_server.call_count == 0
    authorization_service._onAuthStateChanged(FAILED_AUTH_RESPONSE)

    # Ensure that it stopped the server.
    assert stop_auth_server.call_count == 1

def test_loginAndLogout() -> None:
    preferences = Preferences()
    authorization_service = AuthorizationService(OAUTH_SETTINGS, preferences)
    authorization_service.onAuthenticationError.emit = MagicMock()
    authorization_service.onAuthStateChanged.emit = MagicMock()
    authorization_service.initialize()

    mock_reply = Mock()  # The user profile that the service should respond with.
    mock_reply.error = Mock(return_value = QNetworkReply.NetworkError.NoError)
    http_mock = Mock()
    http_mock.get = lambda url, headers_dict, callback, error_callback: callback(mock_reply)
    http_mock.readJSON = Mock(return_value = {"data": {"user_id": "di_resu", "username": "Emanresu"}})

    # Let the service think there was a successful response
    with patch("UM.TaskManagement.HttpRequestManager.HttpRequestManager.getInstance", MagicMock(return_value = http_mock)):
        authorization_service._onAuthStateChanged(SUCCESSFUL_AUTH_RESPONSE)

    # Ensure that the error signal was not triggered
    assert authorization_service.onAuthenticationError.emit.call_count == 0

    # Since we said that it went right this time, validate that we got a signal.
    assert authorization_service.onAuthStateChanged.emit.call_count == 1
    with patch("UM.TaskManagement.HttpRequestManager.HttpRequestManager.getInstance", MagicMock(return_value = http_mock)):
        def callback(profile):
            assert profile is not None
        authorization_service.getUserProfile(callback)
    assert authorization_service.getAccessToken() == "beep"

    # Check that we stored the authentication data, so next time the user won't have to log in again.
    assert preferences.getValue("test/auth_data") is not None

    # We're logged in now, also check if logging out works
    authorization_service.deleteAuthData()
    assert authorization_service.onAuthStateChanged.emit.call_count == 2
    with patch("UM.TaskManagement.HttpRequestManager.HttpRequestManager.getInstance", MagicMock(return_value = http_mock)):
        def callback(profile):
            assert profile is None
        authorization_service.getUserProfile(callback)

    # Ensure the data is gone after we logged out.
    assert preferences.getValue("test/auth_data") == "{}"

def test_wrongServerResponses() -> None:
    authorization_service = AuthorizationService(OAUTH_SETTINGS, Preferences())
    authorization_service.initialize()
    authorization_service._onAuthStateChanged(MALFORMED_AUTH_RESPONSE)

    def callback(profile):
        assert profile is None
    authorization_service.getUserProfile(callback)

def test__generate_auth_url() -> None:
    preferences = Preferences()
    authorization_service = AuthorizationService(OAUTH_SETTINGS, preferences)
    query_parameters_dict = {
        "client_id": "",
        "redirect_uri": OAUTH_SETTINGS.CALLBACK_URL,
        "scope": OAUTH_SETTINGS.CLIENT_SCOPES,
        "response_type": "code"
    }
    auth_url = authorization_service._generate_auth_url(query_parameters_dict, force_browser_logout = False)
    assert MYCLOUD_LOGOFF_URL + "&next=" not in auth_url

    auth_url = authorization_service._generate_auth_url(query_parameters_dict, force_browser_logout = True)
    assert MYCLOUD_LOGOFF_URL + "&next=" in auth_url
