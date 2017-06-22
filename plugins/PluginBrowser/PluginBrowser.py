# Copyright (c) 2017 Ultimaker B.V.
# PluginBrowser is released under the terms of the AGPLv3 or higher.
from UM.Extension import Extension
from UM.i18n import i18nCatalog
from UM.Logger import Logger

from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtCore import QUrl

import json

i18n_catalog = i18nCatalog("cura")


class PluginBrowser(Extension):
    def __init__(self):
        super().__init__()
        self.addMenuItem(i18n_catalog.i18n("Browse plugins"), self.browsePlugins)
        self._api_version = 1
        self._api_url = "http://software.ultimaker.com/cura/v%s/" % self._api_version

        self._plugin_list_request = None
        self._network_manager = None

        self._plugins_metadata = []

    def browsePlugins(self):
        self._createNetworkManager()
        self.requestPluginList()
        #TODO: Show popup with populated plugin data.

    def requestPluginList(self):
        url = QUrl(self._api_url + "plugins")
        self._plugin_list_request = QNetworkRequest(url)
        self._network_manager.get(self._plugin_list_request)

    def _onRequestFinished(self, reply):
        reply_url = reply.url().toString()
        if reply.operation() == QNetworkAccessManager.GetOperation:
            if reply_url == self._api_url + "plugins":
                try:
                    json_data = json.loads(bytes(reply.readAll()).decode("utf-8"))
                    self._plugins_metadata = json_data
                except json.decoder.JSONDecodeError:
                    Logger.log("w", "Received an invalid print job state message: Not valid JSON.")
                    return
        else:
            # Ignore any operation that is not a get operation
            pass

    def _createNetworkManager(self):
        if self._network_manager:
            self._network_manager.finished.disconnect(self._onRequestFinished)

        self._network_manager = QNetworkAccessManager()
        self._network_manager.finished.connect(self._onRequestFinished)