import json
import os
import platform
from typing import Dict, Optional

from PyQt5.QtCore import QObject
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest

from UM.Extension import Extension
from UM.Logger import Logger
from UM.Message import Message
from UM.PluginRegistry import PluginRegistry
from cura.CuraApplication import CuraApplication
from plugins.Toolbox.src.CloudApiModel import CloudApiModel
from plugins.Toolbox.src.SubscribedPackagesModel import SubscribedPackagesModel
from plugins.Toolbox.src.Toolbox import i18n_catalog


class SubscriptionChecker(QObject, Extension):

    def __init__(self, application: CuraApplication) -> None:
        super().__init__()

        self._application = application  # type: CuraApplication
        self._model = SubscribedPackagesModel()

        self._application.initializationFinished.connect(self._onAppInitialized)
        self._application.getCuraAPI().account.accessTokenChanged.connect(self._updateRequestHeader)

    # This is a plugin, so most of the components required are not ready when
    # this is initialized. Therefore, we wait until the application is ready.
    def _onAppInitialized(self) -> None:
        self._package_manager = self._application.getPackageManager()

        # initial check
        self._fetchUserSubscribedPackages()
        # check again whenever the login state changes
        self._application.getCuraAPI().account.loginStateChanged.connect(self._fetchUserSubscribedPackages)

    def _fetchUserSubscribedPackages(self):
        if self._application.getCuraAPI().account.isLoggedIn:
            self._getUserPackages("subscribed_packages")

    def _handleCompatibilityData(self, json_data) -> None:
        user_subscribed_packages = [plugin["package_id"] for plugin in json_data]
        user_installed_packages = self._package_manager.getUserInstalledPackages()

        # We check if there are packages installed in Cloud Marketplace but not in Cura marketplace (discrepancy)
        package_discrepancy = list(set(user_subscribed_packages).difference(user_installed_packages))

        self._model.setMetadata(json_data)
        self._model.addValue(package_discrepancy)
        self._model.update()

        if package_discrepancy:
            self._handlePackageDiscrepancies(package_discrepancy)

    def _handlePackageDiscrepancies(self, package_discrepancy):
        Logger.log("d", "Discrepancy found between Cloud subscribed packages and Cura installed packages")
        sync_message = Message(i18n_catalog.i18nc(
            "@info:generic",
            "\nDo you want to sync material and software packages with your account?"),
            lifetime=0,
            title=i18n_catalog.i18nc("@info:title", "Changes detected from your Ultimaker account", ))
        sync_message.addAction("sync",
                               name=i18n_catalog.i18nc("@action:button", "Sync"),
                               icon="",
                               description="Sync your Cloud subscribed packages to your local environment.",
                               button_align=Message.ActionButtonAlignment.ALIGN_RIGHT)
        sync_message.actionTriggered.connect(self._onSyncButtonClicked)
        sync_message.show()

    def _onSyncButtonClicked(self, sync_message: Message, sync_message_action: str) -> None:
        sync_message.hide()
        compatibility_dialog_path = "resources/qml/dialogs/CompatibilityDialog.qml"
        plugin_path_prefix = PluginRegistry.getInstance().getPluginPath(self.getPluginId())
        if plugin_path_prefix:
            path = os.path.join(plugin_path_prefix, compatibility_dialog_path)
            self.compatibility_dialog_view = self._application.getInstance().createQmlComponent(path, {"toolbox": self})

    def _getUserPackages(self, request_type: str) -> None:
        Logger.log("d", "Requesting [%s] metadata from server.", request_type)
        self._updateRequestHeader()
        url = CloudApiModel.api_url_user_packages

        self._application.getHttpRequestManager().get(url,
                                                      headers_dict = self._request_headers,
                                                      callback = self._onUserPackagesRequestFinished,
                                                      error_callback = self._onUserPackagesRequestFinished)

    def _onUserPackagesRequestFinished(self,
                                      reply: "QNetworkReply",
                                      error: Optional["QNetworkReply.NetworkError"] = None) -> None:
        if error is not None or reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) != 200:
            Logger.log("w",
                       "Requesting user packages failed, response code %s while trying to connect to %s",
                       reply.attribute(QNetworkRequest.HttpStatusCodeAttribute), reply.url())
            return

        try:
            json_data = json.loads(bytes(reply.readAll()).decode("utf-8"))

            # Check for errors:
            if "errors" in json_data:
                for error in json_data["errors"]:
                    Logger.log("e", "%s", error["title"])
                return

            self._handleCompatibilityData(json_data["data"])
        except json.decoder.JSONDecodeError:
            Logger.log("w", "Received invalid JSON for user packages")

    def _updateRequestHeader(self):
        # todo DRY, copied from Toolbox. To RequestManager?
        self._request_headers = {
            "User-Agent": "%s/%s (%s %s)" % (self._application.getApplicationName(),
                                             self._application.getVersion(),
                                             platform.system(),
                                             platform.machine())
        }
        access_token = self._application.getCuraAPI().account.accessToken
        if access_token:
            self._request_headers["Authorization"] = "Bearer {}".format(access_token)

