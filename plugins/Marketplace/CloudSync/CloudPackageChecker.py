#  Copyright (c) 2022 UltiMaker
#  Cura is released under the terms of the LGPLv3 or higher.

import json
from typing import List, Dict, Any, Set
from typing import Optional

from PyQt6.QtCore import QObject
from PyQt6.QtNetwork import QNetworkReply

from UM import i18nCatalog
from UM.Logger import Logger
from UM.Message import Message
from UM.Signal import Signal
from UM.TaskManagement.HttpRequestManager import HttpRequestManager
from UM.TaskManagement.HttpRequestScope import JsonDecoratorScope
from cura.API.Account import SyncState
from cura.CuraApplication import CuraApplication, ApplicationMetadata
from cura.UltimakerCloud.UltimakerCloudScope import UltimakerCloudScope
from .SubscribedPackagesModel import SubscribedPackagesModel
from ..CloudApiModel import CloudApiModel


class CloudPackageChecker(QObject):

    SYNC_SERVICE_NAME = "CloudPackageChecker"

    def __init__(self, application: CuraApplication) -> None:
        super().__init__()

        self.discrepancies = Signal()  # Emits SubscribedPackagesModel
        self._application: CuraApplication = application
        self._scope = JsonDecoratorScope(UltimakerCloudScope(application))
        self._model = SubscribedPackagesModel()
        self._message: Optional[Message] = None

        self._application.initializationFinished.connect(self._onAppInitialized)
        self._i18n_catalog = i18nCatalog("cura")
        self._sdk_version = ApplicationMetadata.CuraSDKVersion

        self._last_notified_packages = set()  # type: Set[str]
        """Packages for which a notification has been shown. No need to bother the user twice for equal content"""

    # This is a plugin, so most of the components required are not ready when
    # this is initialized. Therefore, we wait until the application is ready.
    def _onAppInitialized(self) -> None:
        self._package_manager = self._application.getPackageManager()
        # initial check
        self._getPackagesIfLoggedIn()

        self._application.getCuraAPI().account.loginStateChanged.connect(self._onLoginStateChanged)
        self._application.getCuraAPI().account.syncRequested.connect(self._getPackagesIfLoggedIn)

    def _onLoginStateChanged(self) -> None:
        # reset session
        self._last_notified_packages = set()
        self._getPackagesIfLoggedIn()

    def _getPackagesIfLoggedIn(self) -> None:
        if self._application.getCuraAPI().account.isLoggedIn:
            self._getUserSubscribedPackages()
        else:
            self._hideSyncMessage()

    def _getUserSubscribedPackages(self) -> None:
        self._application.getCuraAPI().account.setSyncState(self.SYNC_SERVICE_NAME, SyncState.SYNCING)
        url = CloudApiModel.api_url_user_packages
        self._application.getHttpRequestManager().get(url,
                                                      callback=self._onUserPackagesRequestFinished,
                                                      error_callback=self._onUserPackagesRequestFinished,
                                                      timeout=10,
                                                      scope=self._scope)

    def _onUserPackagesRequestFinished(self, reply: "QNetworkReply", error: Optional["QNetworkReply.NetworkError"] = None) -> None:
        if error is not None or HttpRequestManager.safeHttpStatus(reply) != 200:
            Logger.log("w",
                       "Requesting user packages failed, response code %s while trying to connect to %s",
                       HttpRequestManager.safeHttpStatus(reply), reply.url())
            self._application.getCuraAPI().account.setSyncState(self.SYNC_SERVICE_NAME, SyncState.ERROR)
            return

        try:
            json_data = json.loads(bytes(reply.readAll()).decode("utf-8"))
            # Check for errors:
            if "errors" in json_data:
                for error in json_data["errors"]:
                    Logger.log("e", "%s", error["title"])
                    self._application.getCuraAPI().account.setSyncState(self.SYNC_SERVICE_NAME, SyncState.ERROR)
                return
            self._handleCompatibilityData(json_data["data"])
        except json.decoder.JSONDecodeError:
            Logger.log("w", "Received invalid JSON for user subscribed packages from the Web Marketplace")

        self._application.getCuraAPI().account.setSyncState(self.SYNC_SERVICE_NAME, SyncState.SUCCESS)

    def _handleCompatibilityData(self, subscribed_packages_payload: List[Dict[str, Any]]) -> None:
        user_subscribed_packages = {plugin["package_id"] for plugin in subscribed_packages_payload}
        user_installed_packages = self._package_manager.getAllInstalledPackageIDs()

        # We need to re-evaluate the dismissed packages
        # (i.e. some package might got updated to the correct SDK version in the meantime,
        # hence remove them from the Dismissed Incompatible list)
        self._package_manager.reEvaluateDismissedPackages(subscribed_packages_payload, self._sdk_version)
        user_dismissed_packages = self._package_manager.getDismissedPackages()
        if user_dismissed_packages:
            user_installed_packages.update(user_dismissed_packages)

        # We check if there are packages installed in Web Marketplace but not in Cura marketplace
        package_discrepancy = list(user_subscribed_packages.difference(user_installed_packages))

        if user_subscribed_packages != self._last_notified_packages:
            # scenario:
            # 1. user subscribes to a package
            # 2. dismisses the license/unsubscribes
            # 3. subscribes to the same package again
            # in this scenario we want to notify the user again. To capture that there was a change during
            # step 2, we clear the last_notified after step 2. This way, the user will be notified after
            # step 3 even though the list of packages for step 1 and 3 are equal
            self._last_notified_packages = set()

        if package_discrepancy:
            account = self._application.getCuraAPI().account
            account.setUpdatePackagesAction(lambda: self._onSyncButtonClicked(None, None))

            if user_subscribed_packages == self._last_notified_packages:
                # already notified user about these
                return

            Logger.log("d", "Discrepancy found between Cloud subscribed packages and Cura installed packages")
            self._model.addDiscrepancies(package_discrepancy)
            self._model.initialize(self._package_manager, subscribed_packages_payload)
            self._showSyncMessage()
            self._last_notified_packages = user_subscribed_packages

    def _showSyncMessage(self) -> None:
        """Show the message if it is not already shown"""

        if self._message is not None:
            self._message.show()
            return

        sync_message = Message(self._i18n_catalog.i18nc(
            "@info:generic",
            "Do you want to sync material and software packages with your account?"),
            title=self._i18n_catalog.i18nc("@info:title", "Changes detected from your UltiMaker account", ))
        sync_message.addAction("sync",
                               name=self._i18n_catalog.i18nc("@action:button", "Sync"),
                               icon="",
                               description="Sync your plugins and print profiles to Ultimaker Cura.",
                               button_align=Message.ActionButtonAlignment.ALIGN_RIGHT)
        sync_message.actionTriggered.connect(self._onSyncButtonClicked)
        sync_message.show()
        self._message = sync_message

    def _hideSyncMessage(self) -> None:
        """Hide the message if it is showing"""

        if self._message is not None:
            self._message.hide()
            self._message = None

    def _onSyncButtonClicked(self, sync_message: Optional[Message], sync_message_action: Optional[str]) -> None:
        if sync_message is not None:
            sync_message.hide()
        self._hideSyncMessage()  # Should be the same message, but also sets _message to None
        self.discrepancies.emit(self._model)
