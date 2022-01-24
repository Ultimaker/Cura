# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtNetwork import QNetworkRequest

from UM.Logger import Logger
from UM.TaskManagement.HttpRequestScope import DefaultUserAgentScope

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication
    from cura.API.Account import Account


class UltimakerCloudScope(DefaultUserAgentScope):
    """
    Add an Authorization header to the request for Ultimaker Cloud Api requests, if available.
    Also add the user agent headers (see DefaultUserAgentScope).
    """

    def __init__(self, application: "CuraApplication"):
        super().__init__(application)
        api = application.getCuraAPI()
        self._account = api.account  # type: Account

    def requestHook(self, request: QNetworkRequest):
        super().requestHook(request)
        token = self._account.accessToken
        if not self._account.isLoggedIn or token is None:
            Logger.debug("User is not logged in for Cloud API request to {url}".format(url = request.url().toDisplayString()))
            return

        header_dict = {
            "Authorization": "Bearer {}".format(token)
        }
        self.addHeaders(request, header_dict)
