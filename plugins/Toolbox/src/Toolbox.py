# Copyright (c) 2018 Ultimaker B.V.
# Toolbox is released under the terms of the LGPLv3 or higher.
from typing import Dict

from PyQt5.QtCore import QUrl, QObject, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from UM.Application import Application
from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry
from UM.Qt.Bindings.PluginsModel import PluginsModel
from UM.Extension import Extension
from UM.i18n import i18nCatalog

from UM.Version import Version
from UM.Message import Message

import json
import os
import tempfile
import platform
import zipfile

from cura.CuraApplication import CuraApplication
from .CuraPackageModel import CuraPackageModel

i18n_catalog = i18nCatalog("cura")

##  The Toolbox class is responsible of communicating with the server through the API
class Toolbox(QObject, Extension):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._api_version = 1
        self._api_url = "https://api-staging.ultimaker.com/cura-packages/v%s/" % self._api_version

        self._package_list_request = None
        self._download_plugin_request = None

        self._download_plugin_reply = None

        self._network_manager = None
        self._plugin_registry = Application.getInstance().getPluginRegistry()
        self._packages_version_number = self._plugin_registry.APIVersion

        self._packages_metadata = []    # Stores the remote information of the packages
        self._packages_model = None     # Model that list the remote available packages

        # Nowadays can be 'plugins', 'materials' or 'installed'
        self._current_view = "plugins"
        self._detail_view = False
        self._detail_data = {}

        self._restart_required = False

        self._dialog = None
        self._restartDialog = None
        self._download_progress = 0

        self._is_downloading = False

        self._request_header = [b"User-Agent",
                                str.encode("%s/%s (%s %s)" % (Application.getInstance().getApplicationName(),
                                                              Application.getInstance().getVersion(),
                                                              platform.system(),
                                                              platform.machine(),
                                                             )
                                          )
                               ]

        # Installed plugins are really installed after reboot. In order to
        # prevent the user from downloading the same file over and over again,
        # we keep track of the upgraded plugins.

        # NOTE: This will be depreciated in favor of the 'status' system.
        self._newly_installed_plugin_ids = []
        self._newly_uninstalled_plugin_ids = []

        self._plugin_statuses = {} # type: Dict[str, str]

        # variables for the license agreement dialog
        self._license_dialog_plugin_name = ""
        self._license_dialog_license_content = ""
        self._license_dialog_plugin_file_location = ""
        self._restart_dialog_message = ""

    showLicenseDialog = pyqtSignal()
    showRestartDialog = pyqtSignal()
    packagesMetadataChanged = pyqtSignal()
    onDownloadProgressChanged = pyqtSignal()
    onIsDownloadingChanged = pyqtSignal()
    restartRequiredChanged = pyqtSignal()
    viewChanged = pyqtSignal()
    detailViewChanged = pyqtSignal()
    filterChanged = pyqtSignal()

    @pyqtSlot(result = str)
    def getLicenseDialogPluginName(self):
        return self._license_dialog_plugin_name

    @pyqtSlot(result = str)
    def getLicenseDialogPluginFileLocation(self):
        return self._license_dialog_plugin_file_location

    @pyqtSlot(result = str)
    def getLicenseDialogLicenseContent(self):
        return self._license_dialog_license_content

    @pyqtSlot(result = str)
    def getRestartDialogMessage(self):
        return self._restart_dialog_message

    def openLicenseDialog(self, plugin_name, license_content, plugin_file_location):
        self._license_dialog_plugin_name = plugin_name
        self._license_dialog_license_content = license_content
        self._license_dialog_plugin_file_location = plugin_file_location
        self.showLicenseDialog.emit()

    def openRestartDialog(self, message):
        self._restart_dialog_message = message
        self.showRestartDialog.emit()

    @pyqtProperty(bool, notify = onIsDownloadingChanged)
    def isDownloading(self):
        return self._is_downloading

    @pyqtSlot()
    def browsePackages(self):
        self._createNetworkManager()
        self.requestPackageList()

        if not self._dialog:
            self._dialog = self._createDialog("Toolbox.qml")
        self._dialog.show()

    def requestPackageList(self):
        Logger.log("i", "Requesting package list")
        url = QUrl("{base_url}packages?cura_version={version}".format(base_url = self._api_url, version = self._packages_version_number))
        self._package_list_request = QNetworkRequest(url)
        self._package_list_request.setRawHeader(*self._request_header)
        self._network_manager.get(self._package_list_request)

    def _createDialog(self, qml_name):
        Logger.log("d", "Creating dialog [%s]", qml_name)
        path = os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), "resources", "qml", qml_name)
        dialog = Application.getInstance().createQmlComponent(path, {"manager": self})
        return dialog

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

                self._checkPluginLicenseOrInstall(location)
                return

    ##  Checks if the downloaded plugin ZIP file contains a license file or not.
    #   If it does, it will show a popup dialog displaying the license to the user. The plugin will be installed if the
    #   user accepts the license.
    #   If there is no license file, the plugin will be directory installed.
    def _checkPluginLicenseOrInstall(self, file_path):
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            plugin_id = None
            for file in zip_ref.infolist():
                if file.filename.endswith("/"):
                    plugin_id = file.filename.strip("/")
                    break

            if plugin_id is None:
                msg = i18n_catalog.i18nc("@info:status", "Failed to get plugin ID from <filename>{0}</filename>", file_path)
                msg_title = i18n_catalog.i18nc("@info:tile", "Warning")
                self._progress_message = Message(msg, lifetime=0, dismissable=False, title = msg_title)
                return

            # find a potential license file
            plugin_root_dir = plugin_id + "/"
            license_file = None
            for f in zip_ref.infolist():
                # skip directories (with file_size = 0) and files not in the plugin directory
                if f.file_size == 0 or not f.filename.startswith(plugin_root_dir):
                    continue
                file_name = os.path.basename(f.filename).lower()
                file_base_name, file_ext = os.path.splitext(file_name)
                if file_base_name in ["license", "licence"]:
                    license_file = f.filename
                    break

            # show a dialog for user to read and accept/decline the license
            if license_file is not None:
                Logger.log("i", "Found license file for plugin [%s], showing the license dialog to the user", plugin_id)
                license_content = zip_ref.read(license_file).decode('utf-8')
                self.openLicenseDialog(plugin_id, license_content, file_path)
                return

        # there is no license file, directly install the plugin
        self.installPlugin(file_path)

    @pyqtSlot(str)
    def installPlugin(self, file_path):
        # Ensure that it starts with a /, as otherwise it doesn't work on windows.
        if not file_path.startswith("/"):
            location = "/" + file_path
        else:
            location = file_path

        result = PluginRegistry.getInstance().installPlugin("file://" + location)

        self._newly_installed_plugin_ids.append(result["id"])
        self.packagesMetadataChanged.emit()

        self.openRestartDialog(result["message"])
        self._restart_required = True
        self.restartRequiredChanged.emit()

    @pyqtSlot(str)
    def removePlugin(self, plugin_id):
        result = PluginRegistry.getInstance().uninstallPlugin(plugin_id)

        self._newly_uninstalled_plugin_ids.append(result["id"])
        self.packagesMetadataChanged.emit()

        self._restart_required = True
        self.restartRequiredChanged.emit()

        Application.getInstance().messageBox(i18n_catalog.i18nc("@window:title", "Plugin browser"), result["message"])

    @pyqtSlot(str)
    def enablePlugin(self, plugin_id):
        self._plugin_registry.enablePlugin(plugin_id)
        self.packagesMetadataChanged.emit()
        Logger.log("i", "%s was set as 'active'", id)

    @pyqtSlot(str)
    def disablePlugin(self, plugin_id):
        self._plugin_registry.disablePlugin(plugin_id)
        self.packagesMetadataChanged.emit()
        Logger.log("i", "%s was set as 'deactive'", id)

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

    @pyqtSlot(str)
    def filterPackagesByType(self, type):
        if not self._packages_model:
            return
        self._packages_model.setFilter({"type": type})
        self.filterChanged.emit()

    def setCurrentView(self, view = "plugins"):
        self._current_view = view
        self.viewChanged.emit()

    @pyqtProperty(str, fset = setCurrentView, notify = viewChanged)
    def currentView(self):
        return self._current_view

    def setDetailView(self, bool = False):
        self._detail_view = bool
        self.detailViewChanged.emit()

    @pyqtProperty(bool, fset = setDetailView, notify = detailViewChanged)
    def detailView(self):
        return self._detail_view

    # Set the detail data given a plugin ID:
    @pyqtSlot(str)
    def setDetailData(self, id):
        if not self._packages_model:
            return
        for package in self._packages_model.items:
            if package["id"] == id:
                print(package)
                self._detail_data = package
                self.detailViewChanged.emit()

    @pyqtProperty("QVariantMap", notify = detailViewChanged)
    def detailData(self):
        return self._detail_data

    @pyqtProperty(QObject, notify = packagesMetadataChanged)
    def pluginsModel(self):
        self._plugins_model = PluginsModel(None, self._current_view)
        # self._plugins_model.update()

        # Check each plugin the registry for matching plugin from server
        # metadata, and if found, compare the versions. Higher version sets
        # 'can_upgrade' to 'True':
        for plugin in self._plugins_model.items:
            if self._checkCanUpgrade(plugin["id"], plugin["version"]):
                plugin["can_upgrade"] = True

                for item in self._packages_metadata:
                    if item["id"] == plugin["id"]:
                        plugin["update_url"] = item["file_location"]
        if self._current_view == "plugins":
            self.filterPackagesByType("plugin")
        elif self._current_view == "materials":
            self.filterPackagesByType("material")
        return self._plugins_model

    @pyqtProperty(QObject, notify = packagesMetadataChanged)
    def packagesModel(self):
        return self._packages_model

    @pyqtProperty(bool, notify = packagesMetadataChanged)
    def dataReady(self):
        return self._packages_model is not None

    def _checkCanUpgrade(self, id, version):

        # TODO: This could maybe be done more efficiently using a dictionary...

        # Scan plugin server data for plugin with the given id:
        for plugin in self._packages_metadata:
            if id == plugin["id"]:
                reg_version = Version(version)
                new_version = Version(plugin["version"])
                if new_version > reg_version:
                    Logger.log("i", "%s has an update availible: %s", plugin["id"], plugin["version"])
                    return True
        return False

    def _checkAlreadyInstalled(self, id):
        metadata = self._plugin_registry.getMetaData(id)
        # We already installed this plugin, but the registry just doesn't know it yet.
        if id in self._newly_installed_plugin_ids:
            return True
        # We already uninstalled this plugin, but the registry just doesn't know it yet:
        elif id in self._newly_uninstalled_plugin_ids:
            return False
        elif metadata != {}:
            return True
        else:
            return False

    def _checkInstallStatus(self, plugin_id):
        if plugin_id in self._plugin_registry.getInstalledPlugins():
            return "installed"
        else:
            return "uninstalled"

    def _checkEnabled(self, id):
        if id in self._plugin_registry.getActivePlugins():
            return True
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
            if reply_url == "{base_url}packages?cura_version={version}".format(base_url = self._api_url, version = self._packages_version_number):
                try:
                    json_data = json.loads(bytes(reply.readAll()).decode("utf-8"))

                    # Add metadata to the manager:
                    self._packages_metadata = json_data["data"]
                    if not self._packages_model:
                        self._packages_model = CuraPackageModel()
                    self._packages_model.setPackagesMetaData(self._packages_metadata)
                    self.packagesMetadataChanged.emit()
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

    @pyqtProperty(bool, notify = restartRequiredChanged)
    def restartRequired(self):
        return self._restart_required

    @pyqtSlot()
    def restart(self):
        CuraApplication.getInstance().windowClosed()
