from UM.Logger import Logger
from UM.TaskManagement.HttpRequestManager import HttpRequestManager
from UM.TaskManagement.HttpRequestScope import JsonDecoratorScope
from cura.CuraApplication import CuraApplication
from ..CloudApiModel import CloudApiModel
from ..UltimakerCloudScope import UltimakerCloudScope


class CloudApiClient:
    """Manages Cloud subscriptions

    When a package is added to a user's account, the user is 'subscribed' to that package.
    Whenever the user logs in on another instance of Cura, these subscriptions can be used to sync the user's plugins

    Singleton: use CloudApiClient.getInstance() instead of CloudApiClient()
    """

    __instance = None

    @classmethod
    def getInstance(cls, app: CuraApplication):
        if not cls.__instance:
            cls.__instance = CloudApiClient(app)
        return cls.__instance

    def __init__(self, app: CuraApplication) -> None:
        if self.__instance is not None:
            raise RuntimeError("This is a Singleton. use getInstance()")

        self._scope = JsonDecoratorScope(UltimakerCloudScope(app))  # type: JsonDecoratorScope

        app.getPackageManager().packageInstalled.connect(self._onPackageInstalled)

    def unsubscribe(self, package_id: str) -> None:
        url = CloudApiModel.userPackageUrl(package_id)
        HttpRequestManager.getInstance().delete(url = url, scope = self._scope)

    def _subscribe(self, package_id: str) -> None:
        """You probably don't want to use this directly. All installed packages will be automatically subscribed."""

        Logger.debug("Subscribing to {}", package_id)
        data = "{\"data\": {\"package_id\": \"%s\", \"sdk_version\": \"%s\"}}" % (package_id, CloudApiModel.sdk_version)
        HttpRequestManager.getInstance().put(
            url = CloudApiModel.api_url_user_packages,
            data = data.encode(),
            scope = self._scope
        )

    def _onPackageInstalled(self, package_id: str):
        if CuraApplication.getInstance().getCuraAPI().account.isLoggedIn:
            # We might already be subscribed, but checking would take one extra request. Instead, simply subscribe
            self._subscribe(package_id)
