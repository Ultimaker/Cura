import json
from typing import Optional

from PyQt5.QtCore import QObject
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest

from UM import i18nCatalog
from UM.Logger import Logger
from UM.Message import Message
from UM.Signal import Signal
from cura.CuraApplication import CuraApplication, ApplicationMetadata
from ..CloudApiModel import CloudApiModel
from .SubscribedPackagesModel import SubscribedPackagesModel
from ..UltimakerCloudScope import UltimakerCloudScope

from typing import List, Dict, Any

class CloudPackageChecker(QObject):
    def __init__(self, application: CuraApplication) -> None:
        super().__init__()

        self.discrepancies = Signal()  # Emits SubscribedPackagesModel
        self._application = application  # type: CuraApplication
        self._scope = UltimakerCloudScope(application)
        self._model = SubscribedPackagesModel()

        self._application.initializationFinished.connect(self._onAppInitialized)
        self._i18n_catalog = i18nCatalog("cura")
        self._sdk_version = ApplicationMetadata.CuraSDKVersion

    # This is a plugin, so most of the components required are not ready when
    # this is initialized. Therefore, we wait until the application is ready.
    def _onAppInitialized(self) -> None:
        self._package_manager = self._application.getPackageManager()
        # initial check
        self._fetchUserSubscribedPackages()
        # check again whenever the login state changes
        self._application.getCuraAPI().account.loginStateChanged.connect(self._fetchUserSubscribedPackages)

    def _fetchUserSubscribedPackages(self) -> None:
        if self._application.getCuraAPI().account.isLoggedIn:
            self._getUserSubscribedPackages()

    def _getUserSubscribedPackages(self) -> None:
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
            Logger.log("w", "Received invalid JSON for user subscribed packages from the Web Marketplace")

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
            self._model.addDiscrepancies(package_discrepancy)
            self._model.initialize(self._package_manager, subscribed_packages_payload)
            self._handlePackageDiscrepancies()

    def _handlePackageDiscrepancies(self) -> None:
        Logger.log("d", "Discrepancy found between Cloud subscribed packages and Cura installed packages")
        sync_message = Message(self._i18n_catalog.i18nc(
            "@info:generic",
            "\nDo you want to sync material and software packages with your account?"),
            title=self._i18n_catalog.i18nc("@info:title", "Changes detected from your Ultimaker account", ),
            lifetime=0)
        sync_message.addAction("sync",
                               name=self._i18n_catalog.i18nc("@action:button", "Sync"),
                               icon="",
                               description="Sync your Cloud subscribed packages to your local environment.",
                               button_align=Message.ActionButtonAlignment.ALIGN_RIGHT)
        sync_message.actionTriggered.connect(self._onSyncButtonClicked)
        sync_message.show()

    def _onSyncButtonClicked(self, sync_message: Message, sync_message_action: str) -> None:
        sync_message.hide()
        self.discrepancies.emit(self._model)