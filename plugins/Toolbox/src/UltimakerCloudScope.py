from PyQt5.QtNetwork import QNetworkRequest

from UM.Logger import Logger
from UM.TaskManagement.HttpRequestScope import DefaultUserAgentScope
from cura.API import Account
from cura.CuraApplication import CuraApplication


## Add a Authorization header to the request for Ultimaker Cloud Api requests.
# When the user is not logged in or a token is not available, a warning will be logged
# Also add the user agent headers (see DefaultUserAgentScope)
class UltimakerCloudScope(DefaultUserAgentScope):
    def __init__(self, application: CuraApplication):
        super().__init__(application)
        api = application.getCuraAPI()
        self._account = api.account  # type: Account

    def request_hook(self, request: QNetworkRequest):
        super().request_hook(request)
        token = self._account.accessToken
        if not self._account.isLoggedIn or token is None:
            Logger.warning("Cannot add authorization to Cloud Api request")
            return

        header_dict = {
            "Authorization": "Bearer {}".format(token)
        }
        self.add_headers(request, header_dict)
