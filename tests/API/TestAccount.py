from unittest.mock import MagicMock, patch

import pytest

from cura.API import Account
from cura.API.Account import SyncState
from cura.OAuth2.Models import UserProfile


@pytest.fixture()
def user_profile():
    result = UserProfile()
    result.username = "username!"
    result.profile_image_url = "profile_image_url!"
    result.user_id = "user_id!"
    return result


def test_login():
    account = Account(MagicMock())
    mocked_auth_service = MagicMock()
    account._authorization_service = mocked_auth_service
    account.logout = MagicMock()

    account.login()
    mocked_auth_service.startAuthorizationFlow.assert_called_once_with(False)

    # Fake a successful login
    account._onLoginStateChanged(True)

    # Attempting to log in again shouldn't change anything.
    account.login()
    mocked_auth_service.startAuthorizationFlow.assert_called_once_with(False)

    # Attempting to log in with force_logout_before_login as True should call the logout before calling the
    # startAuthorizationFlow(True).
    account.login(force_logout_before_login=True)
    account.logout.assert_called_once_with()
    mocked_auth_service.startAuthorizationFlow.assert_called_with(True)
    assert mocked_auth_service.startAuthorizationFlow.call_count == 2


def test_initialize():
    account = Account(MagicMock())
    mocked_auth_service = MagicMock()
    account._authorization_service = mocked_auth_service

    account.initialize()
    mocked_auth_service.loadAuthDataFromPreferences.assert_called_once_with()


def test_logout():
    account = Account(MagicMock())
    mocked_auth_service = MagicMock()
    account._authorization_service = mocked_auth_service

    account.logout()
    mocked_auth_service.deleteAuthData.assert_not_called()  # We weren't logged in, so nothing should happen
    assert not account.isLoggedIn

    # Pretend the stage changed
    account._onLoginStateChanged(True)
    assert account.isLoggedIn

    account.logout()
    mocked_auth_service.deleteAuthData.assert_called_once_with()

@patch("UM.Application.Application.getInstance")
def test_errorLoginState(application):
    account = Account(MagicMock())
    mocked_auth_service = MagicMock()
    account._authorization_service = mocked_auth_service
    account.loginStateChanged = MagicMock()

    account._onLoginStateChanged(True, "BLARG!")
    # Even though we said that the login worked, it had an error message, so the login failed.
    account.loginStateChanged.emit.called_with(False)

    account._onLoginStateChanged(True)
    account._onLoginStateChanged(False, "OMGZOMG!")
    account.loginStateChanged.emit.called_with(False)


def test_userName(user_profile):
    account = Account(MagicMock())
    mocked_auth_service = MagicMock()
    account._authorization_service = mocked_auth_service
    mocked_auth_service.getUserProfile = MagicMock(return_value = user_profile)

    assert account.userName == "username!"

    mocked_auth_service.getUserProfile = MagicMock(return_value=None)
    assert account.userName is None


def test_profileImageUrl(user_profile):
    account = Account(MagicMock())
    mocked_auth_service = MagicMock()
    account._authorization_service = mocked_auth_service
    mocked_auth_service.getUserProfile = MagicMock(return_value = user_profile)

    assert account.profileImageUrl == "profile_image_url!"

    mocked_auth_service.getUserProfile = MagicMock(return_value=None)
    assert account.profileImageUrl is None


def test_userProfile(user_profile):
    account = Account(MagicMock())
    mocked_auth_service = MagicMock()
    account._authorization_service = mocked_auth_service
    mocked_auth_service.getUserProfile = MagicMock(return_value=user_profile)

    returned_user_profile = account.userProfile
    assert returned_user_profile["username"] == "username!"
    assert returned_user_profile["profile_image_url"] == "profile_image_url!"
    assert returned_user_profile["user_id"] == "user_id!"

    mocked_auth_service.getUserProfile = MagicMock(return_value=None)
    assert account.userProfile is None


def test_sync_success():
    account = Account(MagicMock())

    service1 = "test_service1"
    service2 = "test_service2"

    account.setSyncState(service1, SyncState.SYNCING)
    assert account.syncState == SyncState.SYNCING

    account.setSyncState(service2, SyncState.SYNCING)
    assert account.syncState == SyncState.SYNCING

    account.setSyncState(service1, SyncState.SUCCESS)
    # service2 still syncing
    assert account.syncState == SyncState.SYNCING

    account.setSyncState(service2, SyncState.SUCCESS)
    assert account.syncState == SyncState.SUCCESS


def test_sync_update_action():
    account = Account(MagicMock())

    service1 = "test_service1"

    mockUpdateCallback = MagicMock()

    account.setSyncState(service1, SyncState.SYNCING)
    assert account.syncState == SyncState.SYNCING

    account.setUpdatePackagesAction(mockUpdateCallback)
    account.onUpdatePackagesClicked()
    mockUpdateCallback.assert_called_once_with()
    account.setSyncState(service1, SyncState.SUCCESS)

    account.sync()  # starting a new sync resets the update action to None

    account.setSyncState(service1, SyncState.SYNCING)
    assert account.syncState == SyncState.SYNCING

    account.onUpdatePackagesClicked()  # Should not be connected to an action anymore
    mockUpdateCallback.assert_called_once_with()  # No additional calls
    assert account.updatePackagesEnabled is False
    account.setSyncState(service1, SyncState.SUCCESS)






