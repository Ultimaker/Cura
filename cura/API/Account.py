# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, TYPE_CHECKING

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, pyqtProperty, QTimer

from UM.Message import Message
from UM.i18n import i18nCatalog
from cura.OAuth2.AuthorizationService import AuthorizationService
from cura.OAuth2.Models import OAuth2Settings
from cura.UltimakerCloud import UltimakerCloudAuthentication

if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication

i18n_catalog = i18nCatalog("cura")


##  The account API provides a version-proof bridge to use Ultimaker Accounts
#
#   Usage:
#       ``from cura.API import CuraAPI
#       api = CuraAPI()
#       api.account.login()
#       api.account.logout()
#       api.account.userProfile # Who is logged in``
#
class Account(QObject):
    # The interval with which the remote clusters are checked
    SYNC_INTERVAL = 30.0  # seconds

    class SyncState(Enum):
        """Caution: values used in qml (eg. SyncState.qml)"""

        SYNCING = "syncing",
        SUCCESS = "success",
        ERROR = "error"

    # Signal emitted when user logged in or out.
    loginStateChanged = pyqtSignal(bool)
    accessTokenChanged = pyqtSignal()
    cloudPrintersDetectedChanged = pyqtSignal(bool)
    syncRequested = pyqtSignal()
    lastSyncDateTimeChanged = pyqtSignal()
    syncStateChanged = pyqtSignal(str)

    def __init__(self, application: "CuraApplication", parent = None) -> None:
        super().__init__(parent)
        self._application = application
        self._new_cloud_printers_detected = False

        self._error_message = None  # type: Optional[Message]
        self._logged_in = False
        self._sync_state = self.SyncState.SUCCESS
        self._last_sync_str = "-"

        self._callback_port = 32118
        self._oauth_root = UltimakerCloudAuthentication.CuraCloudAccountAPIRoot

        self._oauth_settings = OAuth2Settings(
            OAUTH_SERVER_URL= self._oauth_root,
            CALLBACK_PORT=self._callback_port,
            CALLBACK_URL="http://localhost:{}/callback".format(self._callback_port),
            CLIENT_ID="um----------------------------ultimaker_cura",
            CLIENT_SCOPES="account.user.read drive.backup.read drive.backup.write packages.download "
                          "packages.rating.read packages.rating.write connect.cluster.read connect.cluster.write "
                          "cura.printjob.read cura.printjob.write cura.mesh.read cura.mesh.write",
            AUTH_DATA_PREFERENCE_KEY="general/ultimaker_auth_data",
            AUTH_SUCCESS_REDIRECT="{}/app/auth-success".format(self._oauth_root),
            AUTH_FAILED_REDIRECT="{}/app/auth-error".format(self._oauth_root)
        )

        self._authorization_service = AuthorizationService(self._oauth_settings)

        # Create a timer for automatic account sync
        self._update_timer = QTimer()
        self._update_timer.setInterval(int(self.SYNC_INTERVAL * 1000))
        # The timer is restarted explicitly after an update was processed. This prevents 2 concurrent updates
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self.syncRequested)

        self._sync_services = {}  # type: Dict[str, Account.SyncState]
        """contains entries "service_name" : SyncState"""

    def initialize(self) -> None:
        self._authorization_service.initialize(self._application.getPreferences())
        self._authorization_service.onAuthStateChanged.connect(self._onLoginStateChanged)
        self._authorization_service.onAuthenticationError.connect(self._onLoginStateChanged)
        self._authorization_service.accessTokenChanged.connect(self._onAccessTokenChanged)
        self._authorization_service.loadAuthDataFromPreferences()

    def setSyncState(self, service_name: str, state: SyncState) -> None:
        """ Can be used to register sync services and update account sync states

        Example: `setSyncState("PluginSyncService", Account.SyncState.SYNCING)`
        :param service_name: A unique name for your service, such as `plugins` or `backups`
        :param state: One of Account.SyncState
        """

        prev_state = self._sync_state

        self._sync_services[service_name] = state

        if any(val == self.SyncState.SYNCING for val in self._sync_services.values()):
            self._sync_state = self.SyncState.SYNCING
        elif any(val == self.SyncState.ERROR for val in self._sync_services.values()):
            self._sync_state = self.SyncState.ERROR
        else:
            self._sync_state = self.SyncState.SUCCESS

        if self._sync_state != prev_state:
            self.syncStateChanged.emit(self._sync_state.value[0])

            if self._sync_state == self.SyncState.SUCCESS:
                self._last_sync_str = datetime.now().strftime("%d/%m/%Y %H:%M")
                self.lastSyncDateTimeChanged.emit()

            if self._sync_state != self.SyncState.SYNCING:
                # schedule new auto update after syncing completed (for whatever reason)
                if not self._update_timer.isActive():
                    self._update_timer.start()

    def _onAccessTokenChanged(self):
        self.accessTokenChanged.emit()

    ## Returns a boolean indicating whether the given authentication is applied against staging or not.
    @property
    def is_staging(self) -> bool:
        return "staging" in self._oauth_root

    @pyqtProperty(bool, notify=loginStateChanged)
    def isLoggedIn(self) -> bool:
        return self._logged_in

    @pyqtProperty(bool, notify=cloudPrintersDetectedChanged)
    def newCloudPrintersDetected(self) -> bool:
        return self._new_cloud_printers_detected

    def _onLoginStateChanged(self, logged_in: bool = False, error_message: Optional[str] = None) -> None:
        if error_message:
            if self._error_message:
                self._error_message.hide()
            self._error_message = Message(error_message, title = i18n_catalog.i18nc("@info:title", "Login failed"))
            self._error_message.show()
            self._logged_in = False
            self.loginStateChanged.emit(False)
            return

        if self._logged_in != logged_in:
            self._logged_in = logged_in
            self.loginStateChanged.emit(logged_in)

    @pyqtSlot()
    def login(self) -> None:
        if self._logged_in:
            # Nothing to do, user already logged in.
            return
        self._authorization_service.startAuthorizationFlow()

    @pyqtProperty(str, notify=loginStateChanged)
    def userName(self):
        user_profile = self._authorization_service.getUserProfile()
        if not user_profile:
            return None
        return user_profile.username

    @pyqtProperty(str, notify = loginStateChanged)
    def profileImageUrl(self):
        user_profile = self._authorization_service.getUserProfile()
        if not user_profile:
            return None
        return user_profile.profile_image_url

    @pyqtProperty(str, notify=accessTokenChanged)
    def accessToken(self) -> Optional[str]:
        return self._authorization_service.getAccessToken()

    #   Get the profile of the logged in user
    #   @returns None if no user is logged in, a dict containing user_id, username and profile_image_url
    @pyqtProperty("QVariantMap", notify = loginStateChanged)
    def userProfile(self) -> Optional[Dict[str, Optional[str]]]:
        user_profile = self._authorization_service.getUserProfile()
        if not user_profile:
            return None
        return user_profile.__dict__

    @pyqtProperty(str, notify=lastSyncDateTimeChanged)
    def lastSyncDateTime(self) -> str:
        return self._last_sync_str

    @pyqtSlot()
    def sync(self) -> None:
        """Checks for new cloud printers"""

        self.syncRequested.emit()

    @pyqtSlot()
    def logout(self) -> None:
        if not self._logged_in:
            return  # Nothing to do, user isn't logged in.

        self._authorization_service.deleteAuthData()
