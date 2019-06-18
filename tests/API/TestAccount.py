from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from cura.API import CuraAPI, Account
from cura.OAuth2.AuthorizationService import AuthorizationService
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

    account.login()
    mocked_auth_service.startAuthorizationFlow.assert_called_once_with()

    # Fake a sucesfull login
    account._onLoginStateChanged(True)

    # Attempting to log in again shouldn't change anything.
    account.login()
    mocked_auth_service.startAuthorizationFlow.assert_called_once_with()


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


def test_errorLoginState():
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
