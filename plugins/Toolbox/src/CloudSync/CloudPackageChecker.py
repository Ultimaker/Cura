# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import json
from typing import List, Dict, Any
from typing import Optional

from PyQt5.QtCore import QObject
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest

from UM import i18nCatalog
from UM.Logger import Logger
from UM.Message import Message
from UM.Signal import Signal
from UM.TaskManagement.HttpRequestScope import JsonDecoratorScope
from cura.CuraApplication import CuraApplication, ApplicationMetadata
from cura.UltimakerCloud.UltimakerCloudScope import UltimakerCloudScope
from .SubscribedPackagesModel import SubscribedPackagesModel
from ..CloudApiModel import CloudApiModel


class CloudPackageChecker(QObject):

    SYNC_SERVICE_NAME = "CloudPackageChecker"

    def __init__(self, application: CuraApplication) -> None:
        super().__init__()

        self.discrepancies = Signal()  # Emits SubscribedPackagesModel
        self._application = application  # type: CuraApplication
        self._scope = JsonDecoratorScope(UltimakerCloudScope(application))
        self._model = SubscribedPackagesModel()
        self._message = None  # type: Optional[Message]

        self._application.initializationFinished.connect(self._onAppInitialized)
        self._i18n_catalog = i18nCatalog("cura")
        self._sdk_version = ApplicationMetadata.CuraSDKVersion

    # This is a plugin, so most of the components required are not ready when
    # this is initialized. Therefore, we wait until the application is ready.
    def _onAppInitialized(self) -> None:
        self._package_manager = self._application.getPackageManager()
        # initial check
        self._getPackagesIfLoggedIn()

        self._application.getCuraAPI().account.loginStateChanged.connect(self._getPackagesIfLoggedIn)
        self._application.getCuraAPI().account.manualSyncRequested.connect(self._getPackagesIfLoggedIn)

    def _getPackagesIfLoggedIn(self) -> None:
        if self._application.getCuraAPI().account.isLoggedIn:
            self._getUserSubscribedPackages()
        else:
            self._hideSyncMessage()

    def _getUserSubscribedPackages(self) -> None:
        self._application.getCuraAPI().account.setSyncState(self.SYNC_SERVICE_NAME, "syncing")
        Logger.debug("Requesting subscribed packages metadata from server.")
        url = CloudApiModel.api_url_user_packages
        self._application.getHttpRequestManager().get(url,
                                                      callback = self._onUserPackagesRequestFinished,
                                                      error_callback = self._onUserPackagesRequestFinished,
                                                      scope = self._scope)

    def _onUserPackagesRequestFinished(self, reply: "QNetworkReply", error: Optional["QNetworkReply.NetworkError"] = None) -> None:
        if error is not None or reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) != 200:
            Logger.log("w",
                       "Requesting user packages failed, response code %s while trying to connect to %s",
                       reply.attribute(QNetworkRequest.HttpStatusCodeAttribute), reply.url())
            self._application.getCuraAPI().account.setSyncState(self.SYNC_SERVICE_NAME, "error")
            return

        try:
            json_data = json.loads(bytes(reply.readAll()).decode("utf-8"))
            # Check for errors:
            if "errors" in json_data:
                for error in json_data["errors"]:
                    Logger.log("e", "%s", error["title"])
                    self._application.getCuraAPI().account.setSyncState(self.SYNC_SERVICE_NAME, "error")
                return
            self._handleCompatibilityData(json_data["data"])
        except json.decoder.JSONDecodeError:
            Logger.log("w", "Received invalid JSON for user subscribed packages from the Web Marketplace")

        self._application.getCuraAPI().account.setSyncState(self.SYNC_SERVICE_NAME, "success")

    def _handleCompatibilityData(self, subscribed_packages_payload: List[Dict[str, Any]]) -> None:
        user_subscribed_packages = [plugin["package_id"] for plugin in subscribed_packages_payload]
        user_installed_packages = self._package_manager.getUserInstalledPackages()

        # We need to re-evaluate the dismissed packages
        # (i.e. some package might got updated to the correct SDK version in the meantime,
        # hence remove them from the Dismissed Incompatible list)
        self._package_manager.reEvaluateDismissedPackages(subscribed_packages_payload, self._sdk_version)
        user_dismissed_packages = self._package_manager.getDismissedPackages()
        if user_dismissed_packages:
            user_installed_packages += user_dismissed_packages

        # We check if there are packages installed in Web Marketplace but not in Cura marketplace
        package_discrepancy = list(set(user_subscribed_packages).difference(user_installed_packages))
        if package_discrepancy:
            Logger.log("d", "Discrepancy found between Cloud subscribed packages and Cura installed packages")
            self._model.addDiscrepancies(package_discrepancy)
            self._model.initialize(self._package_manager, subscribed_packages_payload)
            self._showSyncMessage()

    def _showSyncMessage(self) -> None:
        """Show the message if it is not already shown"""

        if self._message is not None:
            self._message.show()
            return

        sync_message = Message(self._i18n_catalog.i18nc(
            "@info:generic",
            "Do you want to sync material and software packages with your account?"),
            title = self._i18n_catalog.i18nc("@info:title", "Changes detected from your Ultimaker account", ),
            lifetime = 0)
        sync_message.addAction("sync",
                               name = self._i18n_catalog.i18nc("@action:button", "Sync"),
                               icon = "",
                               description = "Sync your Cloud subscribed packages to your local environment.",
                               button_align = Message.ActionButtonAlignment.ALIGN_RIGHT)
        sync_message.actionTriggered.connect(self._onSyncButtonClicked)
        sync_message.show()
        self._message = sync_message

    def _hideSyncMessage(self) -> None:
        """Hide the message if it is showing"""

        if self._message is not None:
            self._message.hide()
            self._message = None

    def _onSyncButtonClicked(self, sync_message: Message, sync_message_action: str) -> None:
        sync_message.hide()
        self._hideSyncMessage()  # Should be the same message, but also sets _message to None
        self.discrepancies.emit(self._model)
