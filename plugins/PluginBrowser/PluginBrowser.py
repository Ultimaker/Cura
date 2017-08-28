# Copyright (c) 2017 Ultimaker B.V.
# PluginBrowser is released under the terms of the AGPLv3 or higher.
from UM.Extension import Extension
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Qt.ListModel import ListModel
from UM.PluginRegistry import PluginRegistry
from UM.Application import Application
from UM.Version import Version

from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtCore import QUrl, QObject, Qt, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt5.QtQml import QQmlComponent, QQmlContext

import json
import os
import tempfile
import platform

i18n_catalog = i18nCatalog("cura")


class PluginBrowser(QObject, Extension):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.addMenuItem(i18n_catalog.i18nc("@menuitem", "Browse plugins"), self.browsePlugins)
        self._api_version = 1
        self._api_url = "http://software.ultimaker.com/cura/v%s/" % self._api_version

        self._plugin_list_request = None
        self._download_plugin_request = None

        self._download_plugin_reply = None

        self._network_manager = None

        self._plugins_metadata = []
        self._plugins_model = None

        self._qml_component = None
        self._qml_context = None
        self._dialog = None
        self._download_progress = 0

        self._is_downloading = False

        self._request_header = [b"User-Agent",
                                str.encode("%s\%s (%s %s)" % (Application.getInstance().getApplicationName(),
                                                              Application.getInstance().getVersion(),
                                                              platform.system(),
                                                              platform.machine(),
                                                             )
                                          )
                               ]

        # Installed plugins are really installed after reboot. In order to prevent the user from downloading the
        # same file over and over again, we keep track of the upgraded plugins.
        self._newly_installed_plugin_ids = []


    pluginsMetadataChanged = pyqtSignal()
    onDownloadProgressChanged = pyqtSignal()
    onIsDownloadingChanged = pyqtSignal()

    @pyqtProperty(bool, notify = onIsDownloadingChanged)
    def isDownloading(self):
        return self._is_downloading

    def browsePlugins(self):
        self._createNetworkManager()
        self.requestPluginList()

        if not self._dialog:
            self._createDialog()
        self._dialog.show()

    @pyqtSlot()
    def requestPluginList(self):
        Logger.log("i", "Requesting plugin list")
        url = QUrl(self._api_url + "plugins")
        self._plugin_list_request = QNetworkRequest(url)
        self._plugin_list_request.setRawHeader(*self._request_header)
        self._network_manager.get(self._plugin_list_request)

    def _createDialog(self):
        Logger.log("d", "PluginBrowser")

        path = QUrl.fromLocalFile(os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), "PluginBrowser.qml"))
        self._qml_component = QQmlComponent(Application.getInstance()._engine, path)

        # We need access to engine (although technically we can't)
        self._qml_context = QQmlContext(Application.getInstance()._engine.rootContext())
        self._qml_context.setContextProperty("manager", self)
        self._dialog = self._qml_component.create(self._qml_context)
        if self._dialog is None:
            Logger.log("e", "QQmlComponent status %s", self._qml_component.status())
            Logger.log("e", "QQmlComponent errorString %s", self._qml_component.errorString())

    def setIsDownloading(self, is_downloading):
        if self._is_downloading != is_downloading:
            self._is_downloading = is_downloading
            self.onIsDownloadingChanged.emit()

    def _onDownloadPluginProgress(self, bytes_sent, bytes_total):
        if bytes_total > 0:
            new_progress = bytes_sent / bytes_total * 100
            self.setDownloadProgress(new_progress)
            if new_progress == 100.0:
                self.setIsDownloading(False)
                self._download_plugin_reply.downloadProgress.disconnect(self._onDownloadPluginProgress)

                # must not delete the temporary file on Windows
                self._temp_plugin_file = tempfile.NamedTemporaryFile(mode = "w+b", suffix = ".curaplugin", delete = False)
                location = self._temp_plugin_file.name

                # write first and close, otherwise on Windows, it cannot read the file
                self._temp_plugin_file.write(self._download_plugin_reply.readAll())
                self._temp_plugin_file.close()

                # open as read
                if not location.startswith("/"):
                    location = "/" + location # Ensure that it starts with a /, as otherwise it doesn't work on windows.
                result = PluginRegistry.getInstance().installPlugin("file://" + location)

                self._newly_installed_plugin_ids.append(result["id"])
                self.pluginsMetadataChanged.emit()

                Application.getInstance().messageBox(i18n_catalog.i18nc("@window:title", "Plugin browser"), result["message"])

                self._temp_plugin_file.close()  # Plugin was installed, delete temp file

    @pyqtProperty(int, notify = onDownloadProgressChanged)
    def downloadProgress(self):
        return self._download_progress

    def setDownloadProgress(self, progress):
        if progress != self._download_progress:
            self._download_progress = progress
            self.onDownloadProgressChanged.emit()

    @pyqtSlot(str)
    def downloadAndInstallPlugin(self, url):
        Logger.log("i", "Attempting to download & install plugin from %s", url)
        url = QUrl(url)
        self._download_plugin_request = QNetworkRequest(url)
        self._download_plugin_request.setRawHeader(*self._request_header)
        self._download_plugin_reply = self._network_manager.get(self._download_plugin_request)
        self.setDownloadProgress(0)
        self.setIsDownloading(True)
        self._download_plugin_reply.downloadProgress.connect(self._onDownloadPluginProgress)

    @pyqtSlot()
    def cancelDownload(self):
        Logger.log("i", "user cancelled the download of a plugin")
        self._download_plugin_reply.abort()
        self._download_plugin_reply.downloadProgress.disconnect(self._onDownloadPluginProgress)
        self._download_plugin_reply = None
        self._download_plugin_request = None

        self.setDownloadProgress(0)
        self.setIsDownloading(False)

    @pyqtProperty(QObject, notify=pluginsMetadataChanged)
    def pluginsModel(self):
        if self._plugins_model is None:
            self._plugins_model = ListModel()
            self._plugins_model.addRoleName(Qt.UserRole + 1, "name")
            self._plugins_model.addRoleName(Qt.UserRole + 2, "version")
            self._plugins_model.addRoleName(Qt.UserRole + 3, "short_description")
            self._plugins_model.addRoleName(Qt.UserRole + 4, "author")
            self._plugins_model.addRoleName(Qt.UserRole + 5, "already_installed")
            self._plugins_model.addRoleName(Qt.UserRole + 6, "file_location")
            self._plugins_model.addRoleName(Qt.UserRole + 7, "can_upgrade")
        else:
            self._plugins_model.clear()
        items = []
        for metadata in self._plugins_metadata:
            items.append({
                "name": metadata["label"],
                "version": metadata["version"],
                "short_description": metadata["short_description"],
                "author": metadata["author"],
                "already_installed": self._checkAlreadyInstalled(metadata["id"]),
                "file_location": metadata["file_location"],
                "can_upgrade": self._checkCanUpgrade(metadata["id"], metadata["version"])
            })
        self._plugins_model.setItems(items)
        return self._plugins_model

    def _checkCanUpgrade(self, id, version):
        plugin_registry = PluginRegistry.getInstance()
        metadata = plugin_registry.getMetaData(id)
        if metadata != {}:
            if id in self._newly_installed_plugin_ids:
                return False  # We already updated this plugin.
            current_version = Version(metadata["plugin"]["version"])
            new_version = Version(version)
            if new_version > current_version:
                return True
        return False

    def _checkAlreadyInstalled(self, id):
        plugin_registry = PluginRegistry.getInstance()
        metadata = plugin_registry.getMetaData(id)
        if metadata != {}:
            return True
        else:
            if id in self._newly_installed_plugin_ids:
                return True  # We already installed this plugin, but the registry just doesn't know it yet.
            return False

    def _onRequestFinished(self, reply):
        reply_url = reply.url().toString()
        if reply.error() == QNetworkReply.TimeoutError:
            Logger.log("w", "Got a timeout.")
            # Reset everything.
            self.setDownloadProgress(0)
            self.setIsDownloading(False)
            if self._download_plugin_reply:
                self._download_plugin_reply.downloadProgress.disconnect(self._onDownloadPluginProgress)
                self._download_plugin_reply.abort()
                self._download_plugin_reply = None
            return
        elif reply.error() == QNetworkReply.HostNotFoundError:
            Logger.log("w", "Unable to reach server.")
            return

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

    def _onNetworkAccesibleChanged(self, accessible):
        if accessible == 0:
            self.setDownloadProgress(0)
            self.setIsDownloading(False)
            if self._download_plugin_reply:
                self._download_plugin_reply.downloadProgress.disconnect(self._onDownloadPluginProgress)
                self._download_plugin_reply.abort()
                self._download_plugin_reply = None

    def _createNetworkManager(self):
        if self._network_manager:
            self._network_manager.finished.disconnect(self._onRequestFinished)
            self._network_manager.networkAccessibleChanged.disconnect(self._onNetworkAccesibleChanged)

        self._network_manager = QNetworkAccessManager()
        self._network_manager.finished.connect(self._onRequestFinished)
        self._network_manager.networkAccessibleChanged.connect(self._onNetworkAccesibleChanged)
