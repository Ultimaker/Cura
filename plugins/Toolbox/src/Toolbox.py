# Copyright (c) 2018 Ultimaker B.V.
# Toolbox is released under the terms of the LGPLv3 or higher.

from typing import Dict
import json
import os
import tempfile
import platform

from PyQt5.QtCore import QUrl, QObject, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from UM.Application import Application
from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry
from UM.Qt.Bindings.PluginsModel import PluginsModel
from UM.Extension import Extension
from UM.i18n import i18nCatalog
from cura.Utils.VersionTools import compareSemanticVersions

from cura.CuraApplication import CuraApplication
from .AuthorsModel import AuthorsModel
from .PackagesModel import PackagesModel

i18n_catalog = i18nCatalog("cura")


##  The Toolbox class is responsible of communicating with the server through the API
class Toolbox(QObject, Extension):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._application = Application.getInstance()
        self._package_manager = None
        self._plugin_registry = Application.getInstance().getPluginRegistry()
        self._package_manager = None
        self._packages_version = self._plugin_registry.APIVersion
        self._api_version = 1
        self._api_url = "https://api-staging.ultimaker.com/cura-packages/v{api_version}/cura/v{package_version}".format( api_version = self._api_version, package_version = self._packages_version)

        self._get_packages_request = None
        self._get_showcase_request = None

        self._download_request = None
        self._download_reply = None
        self._download_progress = 0
        self._is_downloading = False

        self._network_manager = None
        self._request_header = [
            b"User-Agent",
            str.encode(
                "%s/%s (%s %s)" % (
                    Application.getInstance().getApplicationName(),
                    Application.getInstance().getVersion(),
                    platform.system(),
                    platform.machine(),
                )
            )
        ]

        self._packages_metadata = []
        self._packages_model = None
        self._plugins_showcase_model = None
        self._plugins_installed_model = None
        self._materials_showcase_model = None
        self._materials_installed_model = None
        self._authors_model = None

        # These properties are for keeping track of the UI state:
        # ----------------------------------------------------------------------
        # View category defines which filter to use, and therefore effectively
        # which category is currently being displayed. For example, possible
        # values include "plugin" or "material", but also "installed".
        self._view_category = "plugin"

        # View page defines which type of page layout to use. For example,
        # possible values include "overview", "detail" or "author".
        self._view_page = "loading"

        # View selection defines what is currently selected and should be
        # used in filtering. This could be an author name (if _view_page is set
        # to "author" or a plugin name if it is set to "detail").
        self._view_selection = ""

        # Active package refers to which package is currently being downloaded,
        # installed, or otherwise modified.
        self._active_package = None

        # Nowadays can be 'plugins', 'materials' or 'installed'
        self._current_view = "plugins"
        self._detail_data = {} # Extraneous since can just use the data prop of the model.

        self._dialog = None
        self._restartDialog = None
        self._restart_required = False

        # Installed plugins are really installed after reboot. In order to
        # prevent the user from downloading the same file over and over again,
        # we keep track of the upgraded plugins.
        self._newly_installed_plugin_ids = []
        self._newly_uninstalled_plugin_ids = []
        self._plugin_statuses = {} # type: Dict[str, str]

        # variables for the license agreement dialog
        self._license_dialog_plugin_name = ""
        self._license_dialog_license_content = ""
        self._license_dialog_plugin_file_location = ""
        self._restart_dialog_message = ""

        Application.getInstance().initializationFinished.connect(self._onAppInitialized)

    def _onAppInitialized(self):
        self._package_manager = Application.getInstance().getCuraPackageManager()

    packagesMetadataChanged = pyqtSignal()
    authorsMetadataChanged = pyqtSignal()
    pluginsShowcaseMetadataChanged = pyqtSignal()
    materialsShowcaseMetadataChanged = pyqtSignal()
    metadataChanged = pyqtSignal()

    # Downloading changes
    activePackageChanged = pyqtSignal()
    onDownloadProgressChanged = pyqtSignal()
    onIsDownloadingChanged = pyqtSignal()
    restartRequiredChanged = pyqtSignal()

    # UI changes
    viewChanged = pyqtSignal()
    detailViewChanged = pyqtSignal()
    filterChanged = pyqtSignal()
    showLicenseDialog = pyqtSignal()
    showRestartDialog = pyqtSignal()

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

    @pyqtSlot()
    def browsePackages(self):
        self._package_manager = Application.getInstance().getCuraPackageManager()
        # Create the network manager:
        # This was formerly its own function but really had no reason to be as
        # it was never called more than once ever.
        if self._network_manager:
            self._network_manager.finished.disconnect(self._onRequestFinished)
            self._network_manager.networkAccessibleChanged.disconnect(self._onNetworkAccesibleChanged)
        self._network_manager = QNetworkAccessManager()
        self._network_manager.finished.connect(self._onRequestFinished)
        self._network_manager.networkAccessibleChanged.connect(self._onNetworkAccesibleChanged)

        self._requestShowcase()
        self._requestPackages()
        if not self._dialog:
            self._dialog = self._createDialog("Toolbox.qml")
        self._dialog.show()

    def _createDialog(self, qml_name):
        Logger.log("d", "Toolbox: Creating dialog [%s].", qml_name)
        path = os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), "resources", "qml", qml_name)
        dialog = Application.getInstance().createQmlComponent(path, {"manager": self})
        return dialog

    @pyqtSlot(str)
    def installPlugin(self, file_path):
        self._package_manager.installPackage(file_path)
        self.metadataChanged.emit()
        self.openRestartDialog("TODO")
        self._restart_required = True
        self.restartRequiredChanged.emit()

    @pyqtSlot(str)
    def removePlugin(self, plugin_id):
        self._package_manager.removePackage(plugin_id)
        self.metadataChanged.emit()
        self._restart_required = True
        self.restartRequiredChanged.emit()

        Application.getInstance().messageBox(i18n_catalog.i18nc("@window:title", "Plugin browser"), "TODO")

    @pyqtSlot(str)
    def enablePlugin(self, plugin_id):
        self._plugin_registry.enablePlugin(plugin_id)
        self.metadataChanged.emit()
        Logger.log("i", "%s was set as 'active'", id)

    @pyqtSlot(str)
    def disablePlugin(self, plugin_id):
        self._plugin_registry.disablePlugin(plugin_id)
        self.metadataChanged.emit()
        Logger.log("i", "%s was set as 'deactive'", id)

    @pyqtProperty(QObject, notify = metadataChanged)
    def pluginsModel(self):
        self._plugins_model = PluginsModel(None, self._view_category)
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
        return self._plugins_model

    @pyqtProperty(QObject, notify = metadataChanged)
    def pluginsShowcaseModel(self):
        return self._plugins_showcase_model

    @pyqtProperty(QObject, notify = metadataChanged)
    def materialsShowcaseModel(self):
        return self._materials_showcase_model

    @pyqtProperty(QObject, notify = metadataChanged)
    def packagesModel(self):
        return self._packages_model

    @pyqtProperty(QObject, notify = metadataChanged)
    def authorsModel(self):
        return self._authors_model

    @pyqtProperty(bool, notify = metadataChanged)
    def dataReady(self):
        return self._packages_model is not None

    @pyqtProperty(bool, notify = restartRequiredChanged)
    def restartRequired(self):
        return self._restart_required

    @pyqtSlot()
    def restart(self):
        CuraApplication.getInstance().windowClosed()



    # Checks
    # --------------------------------------------------------------------------
    def _checkCanUpgrade(self, package_id: str, version: str) -> bool:
        installed_plugin_data = self._package_manager.getInstalledPackageInfo(package_id)
        if installed_plugin_data is None:
            return False

        installed_version = installed_plugin_data["package_version"]
        return compareSemanticVersions(version, installed_version) > 0

    def _checkInstalled(self, package_id: str):
        return self._package_manager.isPackageInstalled(package_id)

    def _checkEnabled(self, id):
        if id in self._plugin_registry.getActivePlugins():
            return True
        return False

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



    # Make API Calls
    # --------------------------------------------------------------------------
    def _requestPackages(self):
        Logger.log("i", "Toolbox: Requesting package list from server.")
        url = QUrl("{base_url}/packages".format(base_url = self._api_url))
        self._get_packages_request = QNetworkRequest(url)
        self._get_packages_request.setRawHeader(*self._request_header)
        self._network_manager.get(self._get_packages_request)

    def _requestShowcase(self):
        Logger.log("i", "Toolbox: Requesting showcase list from server.")
        url = QUrl("{base_url}/showcase".format(base_url = self._api_url))
        self._get_showcase_request = QNetworkRequest(url)
        self._get_showcase_request.setRawHeader(*self._request_header)
        self._network_manager.get(self._get_showcase_request)

    @pyqtSlot(str)
    def startDownload(self, url):
        Logger.log("i", "Toolbox: Attempting to download & install package from %s.", url)
        url = QUrl(url)
        self._download_request = QNetworkRequest(url)
        self._download_request.setAttribute(QNetworkRequest.RedirectPolicyAttribute, QNetworkRequest.NoLessSafeRedirectPolicy)
        self._download_request.setRawHeader(*self._request_header)
        self._download_reply = self._network_manager.get(self._download_request)
        self.setDownloadProgress(0)
        self.setIsDownloading(True)
        self._download_reply.downloadProgress.connect(self._onDownloadProgress)

    @pyqtSlot()
    def cancelDownload(self):
        Logger.log("i", "Toolbox: User cancelled the download of a plugin.")
        self._download_reply.abort()
        self._download_reply.downloadProgress.disconnect(self._onDownloadProgress)
        self._download_reply = None
        self._download_request = None
        self.setDownloadProgress(0)
        self.setIsDownloading(False)



    # Handlers for Download Events
    # --------------------------------------------------------------------------
    def _onNetworkAccesibleChanged(self, accessible):
        if accessible == 0:
            self.setDownloadProgress(0)
            self.setIsDownloading(False)
            if self._download_reply:
                self._download_reply.downloadProgress.disconnect(self._onDownloadProgress)
                self._download_reply.abort()
                self._download_reply = None

    # TODO: This function is sooooo ugly. Needs a rework:
    def _onRequestFinished(self, reply):
        reply_url = reply.url().toString()
        if reply.error() == QNetworkReply.TimeoutError:
            Logger.log("w", "Got a timeout.")
            # Reset everything.
            self.setDownloadProgress(0)
            self.setIsDownloading(False)
            if self._download_plugin_reply:
                self._download_plugin_reply.downloadProgress.disconnect(self._onDownloadProgress)
                self._download_plugin_reply.abort()
                self._download_plugin_reply = None
            return
        elif reply.error() == QNetworkReply.HostNotFoundError:
            Logger.log("w", "Unable to reach server.")
            return

        if reply.operation() == QNetworkAccessManager.GetOperation:
            if reply_url == "{base_url}/packages".format(base_url = self._api_url):
                try:
                    json_data = json.loads(bytes(reply.readAll()).decode("utf-8"))
                    print(json_data)
                    # Create packages model with all packages:
                    if not self._packages_model:
                        self._packages_model = PackagesModel()
                    self._packages_metadata = json_data["data"]
                    self._packages_model.setPackagesMetaData(self._packages_metadata)
                    self.metadataChanged.emit()

                    # Create authors model with all authors:
                    if not self._authors_model:
                        self._authors_model = AuthorsModel()
                    # TODO: Remove this hacky code once there's an API call for this.
                    self._authors_metadata = []
                    for package in self._packages_metadata:
                        package["author"]["type"] = package["package_type"]
                        if package["author"] not in self._authors_metadata:
                            self._authors_metadata.append(package["author"])
                    self._authors_model.setMetaData(self._authors_metadata)
                    self.metadataChanged.emit()
                    self.setViewPage("overview")

                    # TODO: Also replace this with a proper API call:
                    if not self._materials_showcase_model:
                        self._materials_showcase_model = AuthorsModel()
                    # TODO: Remove this hacky code once there's an API call for this.
                    self._materials_showcase_model.setMetaData([
                        {
                            "name": "DSM",
                            "email": "contact@dsm.nl",
                            "website": "www.dsm.nl",
                            "type": "material"
                        },
                        {
                            "name": "BASF",
                            "email": "contact@basf.de",
                            "website": "www.basf.de",
                            "type": "material"
                        }
                    ])
                    self.metadataChanged.emit()
                    self.setViewPage("overview")

                except json.decoder.JSONDecodeError:
                    Logger.log("w", "Toolbox: Received invalid JSON for package list.")
                    return


            elif reply_url == "{base_url}/showcase".format(base_url = self._api_url):
                try:
                    json_data = json.loads(bytes(reply.readAll()).decode("utf-8"))
                    # Create packages model with all packages:
                    if not self._plugins_showcase_model:
                        self._plugins_showcase_model = PackagesModel()
                    self._showcase_metadata = json_data["data"]
                    print(self._showcase_metadata)
                    self._plugins_showcase_model.setPackagesMetaData(self._showcase_metadata)
                    for package in self._plugins_showcase_model.items:
                        print(package)
                    self.metadataChanged.emit()
                except json.decoder.JSONDecodeError:
                    Logger.log("w", "Toolbox: Received invalid JSON for showcase.")
                    return
        else:
            # Ignore any operation that is not a get operation
            pass

    def _onDownloadProgress(self, bytes_sent, bytes_total):
        if bytes_total > 0:
            new_progress = bytes_sent / bytes_total * 100
            self.setDownloadProgress(new_progress)
            if new_progress == 100.0:
                self.setIsDownloading(False)
                self._download_reply.downloadProgress.disconnect(self._onDownloadProgress)
                # must not delete the temporary file on Windows
                self._temp_plugin_file = tempfile.NamedTemporaryFile(mode = "w+b", suffix = ".curapackage", delete = False)
                file_path = self._temp_plugin_file.name
                # write first and close, otherwise on Windows, it cannot read the file
                self._temp_plugin_file.write(self._download_reply.readAll())
                self._temp_plugin_file.close()
                self._onDownloadComplete(file_path)
                return

    def _onDownloadComplete(self, file_path):
        Logger.log("i", "Toolbox: Download complete.")
        print(file_path)
        try:
            package_info = self._package_manager.getPackageInfo(file_path)
        except:
            Logger.logException("w", "Toolbox: Package file [%s] was not a valid CuraPackage.", file_path)
            return

        license_content = self._package_manager.getPackageLicense(file_path)
        if license_content is not None:
            self.openLicenseDialog(package_info["package_id"], license_content, file_path)
            return

        self.installPlugin(file_path)
        return


    # Getter & Setters
    # --------------------------------------------------------------------------
    def setDownloadProgress(self, progress):
        if progress != self._download_progress:
            self._download_progress = progress
            self.onDownloadProgressChanged.emit()
    @pyqtProperty(int, fset = setDownloadProgress, notify = onDownloadProgressChanged)
    def downloadProgress(self):
        return self._download_progress

    def setIsDownloading(self, is_downloading):
        if self._is_downloading != is_downloading:
            self._is_downloading = is_downloading
            self.onIsDownloadingChanged.emit()
    @pyqtProperty(bool, fset = setIsDownloading, notify = onIsDownloadingChanged)
    def isDownloading(self):
        return self._is_downloading

    def setActivePackage(self, package):
        self._active_package = package
        self.activePackageChanged.emit()
    @pyqtProperty(QObject, fset = setActivePackage, notify = activePackageChanged)
    def activePackage(self):
        return self._active_package

    def setViewCategory(self, category = "plugins"):
        self._view_category = category
        self.viewChanged.emit()
    @pyqtProperty(str, fset = setViewCategory, notify = viewChanged)
    def viewCategory(self):
        return self._view_category

    def setViewPage(self, page = "overview"):
        self._view_page = page
        self.viewChanged.emit()
    @pyqtProperty(str, fset = setViewPage, notify = viewChanged)
    def viewPage(self):
        return self._view_page

    def setViewSelection(self, selection = ""):
        self._view_selection = selection
        self.viewChanged.emit()
    @pyqtProperty(str, fset = setViewSelection, notify = viewChanged)
    def viewSelection(self):
        return self._view_selection



    # Model Filtering
    # --------------------------------------------------------------------------
    @pyqtSlot(str, str)
    def filterPackages(self, filterType, parameter):
        if not self._packages_model:
            return
        self._packages_model.setFilter({ filterType: parameter })
        self.filterChanged.emit()

    @pyqtSlot()
    def unfilterPackages(self):
        if not self._packages_model:
            return
        self._packages_model.setFilter({})
        self.filterChanged.emit()

    @pyqtSlot(str, str)
    def filterAuthors(self, filterType, parameter):
        if not self._authors_model:
            return
        self._authors_model.setFilter({ filterType: parameter })
        self.filterChanged.emit()

    @pyqtSlot()
    def unfilterAuthors(self):
        if not self._authors_model:
            return
        self._authors_model.setFilter({})
        self.filterChanged.emit()
