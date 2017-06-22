# Copyright (c) 2017 Ultimaker B.V.
# PluginBrowser is released under the terms of the AGPLv3 or higher.
from UM.Extension import Extension
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Qt.ListModel import ListModel
from UM.PluginRegistry import PluginRegistry

from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtCore import QUrl, QObject, Qt, pyqtProperty, pyqtSignal

import json

i18n_catalog = i18nCatalog("cura")


class PluginBrowser(QObject, Extension):
    def __init__(self, parent = None):
        super().__init__()
        self.addMenuItem(i18n_catalog.i18n("Browse plugins"), self.browsePlugins)
        self._api_version = 1
        self._api_url = "http://software.ultimaker.com/cura/v%s/" % self._api_version

        self._plugin_list_request = None
        self._network_manager = None

        self._plugins_metadata = []
        self._plugins_model = None

    pluginsMetadataChanged = pyqtSignal()

    def browsePlugins(self):
        self._createNetworkManager()
        self.requestPluginList()
        #TODO: Show popup with populated plugin data.

    def requestPluginList(self):
        url = QUrl(self._api_url + "plugins")
        self._plugin_list_request = QNetworkRequest(url)
        self._network_manager.get(self._plugin_list_request)

    @pyqtProperty(QObject, notify=pluginsMetadataChanged)
    def pluginsModel(self):
        if self._plugins_model is None:
            self._plugins_model = ListModel()
            self._plugins_model.addRoleName(Qt.UserRole + 1, "name")
            self._plugins_model.addRoleName(Qt.UserRole + 2, "version")
            self._plugins_model.addRoleName(Qt.UserRole + 3, "short_description")
            self._plugins_model.addRoleName(Qt.UserRole + 4, "author")
            self._plugins_model.addRoleName(Qt.UserRole + 5, "already_installed")
        else:
            self._plugins_model.clear()
        items = []
        plugin_registry = PluginRegistry.getInstance()
        for metadata in self._plugins_metadata:
            items.append({
                "name": metadata["label"],
                "version": metadata["version"],
                "short_description": metadata["short_description"],
                "author": metadata["author"],
                "already_installed": plugin_registry.getMetaData(metadata["id"]) != {}
            })
        self._plugins_model.setItems(items)
        return self._plugins_model

    def _onRequestFinished(self, reply):
        reply_url = reply.url().toString()
        if reply.operation() == QNetworkAccessManager.GetOperation:
            if reply_url == self._api_url + "plugins":
                try:
                    json_data = json.loads(bytes(reply.readAll()).decode("utf-8"))
                    self._plugins_metadata = json_data
                    self.pluginsMetadataChanged.emit()
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