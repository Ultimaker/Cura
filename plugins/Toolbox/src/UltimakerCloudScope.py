from PyQt5.QtNetwork import QNetworkRequest

from UM.TaskManagement.HttpRequestScope import DefaultUserAgentScope
from cura.API import Account
from cura.CuraApplication import CuraApplication


class UltimakerCloudScope(DefaultUserAgentScope):
    def __init__(self, application: CuraApplication):
        super().__init__(application)
        api = application.getCuraAPI()
        self._account = api.account  # type: Account

    def request_hook(self, request: QNetworkRequest):
        super().request_hook(request)
        token = self._account.accessToken
        header_dict = {
            "Authorization": "Bearer {}".format(token)
        }
        self.add_headers(request, header_dict)
