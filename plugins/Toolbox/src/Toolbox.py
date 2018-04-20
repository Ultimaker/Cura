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
from UM.Version import Version

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
        self._packages_version = self._plugin_registry.APIVersion
        self._api_version = 1
        self._api_url = "https://api-staging.ultimaker.com/cura-packages/v{api_version}/cura/v{package_version}".format( api_version = self._api_version, package_version = self._packages_version)

        # Network:
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
        self._request_urls = {
            "authors": None,
            "packages": QUrl("{base_url}/packages".format(base_url = self._api_url)),
            "plugins_showcase": QUrl("{base_url}/showcase".format(base_url = self._api_url)),
            "materials_showcase": None
        }

        # Data:
        self._metadata = {
            "authors": [],
            "packages": [],
            "plugins_showcase": [],
            "plugins_installed": [],
            # TODO: Replace this with a proper API call:
            "materials_showcase": [
                {
                    "name": "Ultimaker",
                    "email": "ian.paschal@gmail.com",
                    "website": "ultimaker.com",
                    "type": "material",
                    "icon": None,
                    "packages_count": 7
                },
                {
                    "name": "DSM",
                    "email": "contact@dsm.nl",
                    "website": "www.dsm.nl",
                    "type": "material",
                    "icon": None,
                    "packages_count": 0
                },
                {
                    "name": "BASF",
                    "email": "contact@basf.de",
                    "website": "www.basf.de",
                    "type": "material",
                    "icon": None,
                    "packages_count": 0
                }
            ],
            "materials_installed": []
        }

        # Models:
        self._models = {
            "authors": AuthorsModel(self),
            "packages": PackagesModel(self),
            "plugins_showcase": PackagesModel(self),
            "plugins_installed": PackagesModel(self),
            "materials_showcase": AuthorsModel(self),
            "materials_installed": PackagesModel(self)
        }

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

        self._dialog = None
        self._restart_required = False

        # variables for the license agreement dialog
        self._license_dialog_plugin_name = ""
        self._license_dialog_license_content = ""
        self._license_dialog_plugin_file_location = ""
        self._restart_dialog_message = ""

        Application.getInstance().initializationFinished.connect(self._onAppInitialized)



    # Signals:
    # --------------------------------------------------------------------------
    # Downloading changes
    activePackageChanged = pyqtSignal()
    onDownloadProgressChanged = pyqtSignal()
    onIsDownloadingChanged = pyqtSignal()
    restartRequiredChanged = pyqtSignal()
    installChanged = pyqtSignal()
    enabledChanged = pyqtSignal()

    # UI changes
    viewChanged = pyqtSignal()
    detailViewChanged = pyqtSignal()
    filterChanged = pyqtSignal()
    metadataChanged = pyqtSignal()
    showLicenseDialog = pyqtSignal()

    @pyqtSlot(result = str)
    def getLicenseDialogPluginName(self) -> str:
        return self._license_dialog_plugin_name

    @pyqtSlot(result = str)
    def getLicenseDialogPluginFileLocation(self) -> str:
        return self._license_dialog_plugin_file_location

    @pyqtSlot(result = str)
    def getLicenseDialogLicenseContent(self) -> str:
        return self._license_dialog_license_content

    def openLicenseDialog(self, plugin_name: str, license_content: str, plugin_file_location: str):
        self._license_dialog_plugin_name = plugin_name
        self._license_dialog_license_content = license_content
        self._license_dialog_plugin_file_location = plugin_file_location
        self.showLicenseDialog.emit()

    # This is a plugin, so most of the components required are not ready when
    # this is initialized. Therefore, we wait until the application is ready.
    def _onAppInitialized(self):
        self._package_manager = Application.getInstance().getCuraPackageManager()

    @pyqtSlot()
    def browsePackages(self):
        # Create the network manager:
        # This was formerly its own function but really had no reason to be as
        # it was never called more than once ever.
        if self._network_manager:
            self._network_manager.finished.disconnect(self._onRequestFinished)
            self._network_manager.networkAccessibleChanged.disconnect(self._onNetworkAccesibleChanged)
        self._network_manager = QNetworkAccessManager()
        self._network_manager.finished.connect(self._onRequestFinished)
        self._network_manager.networkAccessibleChanged.connect(self._onNetworkAccesibleChanged)

        # Make remote requests:
        self._makeRequestByType("packages")
        self._makeRequestByType("plugins_showcase")

        # Gather installed packages:
        self._updateInstalledModels()

        if not self._dialog:
            self._dialog = self._createDialog("Toolbox.qml")
        self._dialog.show()

        # Apply enabled/disabled state to installed plugins
        self.enabledChanged.emit()

    def _createDialog(self, qml_name: str):
        Logger.log("d", "Toolbox: Creating dialog [%s].", qml_name)
        path = os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), "resources", "qml", qml_name)
        dialog = Application.getInstance().createQmlComponent(path, {"toolbox": self})
        return dialog

    @pyqtSlot()
    def _updateInstalledModels(self):
        all_packages = self._package_manager.getAllInstalledPackagesInfo()
        if "plugin" in all_packages:
            self._metadata["plugins_installed"] = all_packages["plugin"]
            self._models["plugins_installed"].setMetadata(self._metadata["plugins_installed"])
            self.metadataChanged.emit()
        if "material" in all_packages:
            self._metadata["materials_installed"] = all_packages["material"]
            self._models["materials_installed"].setMetadata(self._metadata["materials_installed"])
            self.metadataChanged.emit()

    @pyqtSlot(str)
    def install(self, file_path: str):
        self._package_manager.installPackage(file_path)
        self.installChanged.emit()
        self._updateInstalledModels()
        self.metadataChanged.emit()
        self._restart_required = True
        self.restartRequiredChanged.emit()

    @pyqtSlot(str)
    def uninstall(self, plugin_id: str):
        self._package_manager.removePackage(plugin_id)
        self.installChanged.emit()
        self._updateInstalledModels()
        self.metadataChanged.emit()
        self._restart_required = True
        self.restartRequiredChanged.emit()

    @pyqtSlot(str)
    def enable(self, plugin_id: str):
        self._plugin_registry.enablePlugin(plugin_id)
        self.enabledChanged.emit()
        Logger.log("i", "%s was set as 'active'.", plugin_id)
        self._restart_required = True
        self.restartRequiredChanged.emit()

    @pyqtSlot(str)
    def disable(self, plugin_id: str):
        self._plugin_registry.disablePlugin(plugin_id)
        self.enabledChanged.emit()
        Logger.log("i", "%s was set as 'deactive'.", plugin_id)
        self._restart_required = True
        self.restartRequiredChanged.emit()

    @pyqtProperty(bool, notify = metadataChanged)
    def dataReady(self):
        return self._packages_model is not None

    @pyqtProperty(bool, notify = restartRequiredChanged)
    def restartRequired(self):
        return self._restart_required

    @pyqtSlot()
    def restart(self):
        self._package_manager._removeAllScheduledPackages()
        CuraApplication.getInstance().windowClosed()



    # Checks
    # --------------------------------------------------------------------------
    @pyqtSlot(str, result = bool)
    def canUpdate(self, package_id: str) -> bool:
        local_package = self._package_manager.getInstalledPackageInfo(package_id)
        if local_package is None:
            return False

        remote_package = None
        for package in self._metadata["packages"]:
            if package["package_id"] == package_id:
                remote_package = package
        if remote_package is None:
            return False

        local_version = local_package["package_version"]
        remote_version = remote_package["package_version"]
        return Version(remote_version) > Version(local_version)

    @pyqtSlot(str, result = bool)
    def isInstalled(self, package_id: str) -> bool:
        return self._package_manager.isPackageInstalled(package_id)

    @pyqtSlot(str, result = bool)
    def isEnabled(self, package_id: str) -> bool:
        if package_id in self._plugin_registry.getActivePlugins():
            return True
        return False



    # Make API Calls
    # --------------------------------------------------------------------------
    def _makeRequestByType(self, type: str):
        Logger.log("i", "Toolbox: Requesting %s metadata from server.", type)
        request = QNetworkRequest(self._request_urls[type])
        request.setRawHeader(*self._request_header)
        self._network_manager.get(request)
    # TODO: Request authors and request material showcase

    @pyqtSlot(str)
    def startDownload(self, url: str):
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



    # Handlers for Network Events
    # --------------------------------------------------------------------------
    def _onNetworkAccesibleChanged(self, accessible: int):
        if accessible == 0:
            self.setDownloadProgress(0)
            self.setIsDownloading(False)
            if self._download_reply:
                self._download_reply.downloadProgress.disconnect(self._onDownloadProgress)
                self._download_reply.abort()
                self._download_reply = None

    def _onRequestFinished(self, reply: QNetworkReply):

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

        if reply.error() == QNetworkReply.HostNotFoundError:
            Logger.log("w", "Unable to reach server.")
            return

        if reply.operation() == QNetworkAccessManager.GetOperation:
            # TODO: In the future use the following to build any model from any
            # request. Right now this doesn't work because the packages request
            # is also responsible for populating other models.
            # for type, url in self._request_urls.items():
            #     if reply.url() == url:
            #         try:
            #             json_data = json.loads(bytes(reply.readAll()).decode("utf-8"))
            #
            #             # Check for errors:
            #             if "errors" in json_data:
            #                 for error in json_data["errors"]:
            #                     Logger.log("e", "%s", error["title"])
            #                 return
            #
            #             # Create model and apply metadata:
            #             if not self._models[type]:
            #                 Logger.log("e", "Could not find the %s model.", type)
            #                 break
            #             self._metadata[type] = json_data["data"]
            #             self._models[type].setMetadata(self._metadata[type])
            #             self.metadataChanged.emit()
            #             self.setViewPage("overview")
            #             return
            #         except json.decoder.JSONDecodeError:
            #             Logger.log("w", "Toolbox: Received invalid JSON for %s.", type)
            #             break

            if reply.url() == self._request_urls["packages"]:
                try:
                    json_data = json.loads(bytes(reply.readAll()).decode("utf-8"))

                    # Check for errors:
                    if "errors" in json_data:
                        for error in json_data["errors"]:
                            Logger.log("e", "%s", error["title"])
                        return

                    # Create packages model with all packages:
                    if not self._models["packages"]:
                        self._models["packages"] = PackagesModel(self)
                    self._metadata["packages"] = json_data["data"]
                    self._models["packages"].setMetadata(self._metadata["packages"])
                    self.metadataChanged.emit()

                    # Create authors model with all authors:
                    if not self._models["authors"]:
                        self._models["authors"] = AuthorsModel()
                    # TODO: Replace this with a proper API call:
                    for package in self._metadata["packages"]:
                        if package["author"] not in self._metadata["authors"]:
                            self._metadata["authors"].append(package["author"])

                    for author in self._metadata["authors"]:
                        if "package_count" not in author:
                            author["package_count"] = 0

                        for package in self._metadata["packages"]:
                            if package["author"]["name"] == author["name"]:
                                author["package_count"] += 1
                                author["type"] = package["package_type"]
                                if "icon_url" in package:
                                    author["icon_url"] = package["icon_url"]

                    self._models["authors"].setMetadata(self._metadata["authors"])
                    self.metadataChanged.emit()

                    if not self._models["materials_showcase"]:
                        self._models["materials_showcase"] = AuthorsModel(self)
                    # TODO: Replace this with a proper API call:
                    self._models["materials_showcase"].setMetadata(self._metadata["materials_showcase"])

                    # This part is also needed for comparing downloaded packages to
                    # installed packages.
                    self._models["packages"].setMetadata(self._metadata["packages"])
                    self._models["packages"].setFilter({"type": "plugin"})

                    self.metadataChanged.emit()

                    self.setViewPage("overview")
                    return

                except json.decoder.JSONDecodeError:
                    Logger.log("w", "Toolbox: Received invalid JSON for package list.")
                    return

            if reply.url() == self._request_urls["plugins_showcase"]:
                try:
                    json_data = json.loads(bytes(reply.readAll()).decode("utf-8"))

                    # Check for errors:
                    if "errors" in json_data:
                        for error in json_data["errors"]:
                            Logger.log("e", "%s", error["title"])
                        return

                    # Create packages model with all packages:
                    if not self._models["plugins_showcase"]:
                        self._models["plugins_showcase"] = PackagesModel()
                    self._metadata["plugins_showcase"] = json_data["data"]
                    self._models["plugins_showcase"].setMetadata(self._metadata["plugins_showcase"])
                    self.metadataChanged.emit()

                    self.setViewPage("overview")
                    return

                except json.decoder.JSONDecodeError:
                    Logger.log("w", "Toolbox: Received invalid JSON for showcase.")
                    return


        else:
            # Ignore any operation that is not a get operation
            pass

    def _onDownloadProgress(self, bytes_sent: int, bytes_total: int):
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

    def _onDownloadComplete(self, file_path: str):
        Logger.log("i", "Toolbox: Download complete.")
        try:
            package_info = self._package_manager.getPackageInfo(file_path)
        except:
            Logger.logException("w", "Toolbox: Package file [%s] was not a valid CuraPackage.", file_path)
            return

        license_content = self._package_manager.getPackageLicense(file_path)
        if license_content is not None:
            self.openLicenseDialog(package_info["package_id"], license_content, file_path)
            return

        self.install(file_path)
        return


    # Getter & Setters for Properties:
    # --------------------------------------------------------------------------
    def setDownloadProgress(self, progress: int):
        if progress != self._download_progress:
            self._download_progress = progress
            self.onDownloadProgressChanged.emit()
    @pyqtProperty(int, fset = setDownloadProgress, notify = onDownloadProgressChanged)
    def downloadProgress(self) -> int:
        return self._download_progress

    def setIsDownloading(self, is_downloading: bool):
        if self._is_downloading != is_downloading:
            self._is_downloading = is_downloading
            self.onIsDownloadingChanged.emit()
    @pyqtProperty(bool, fset = setIsDownloading, notify = onIsDownloadingChanged)
    def isDownloading(self) -> bool:
        return self._is_downloading

    def setActivePackage(self, package: dict):
        self._active_package = package
        self.activePackageChanged.emit()
    @pyqtProperty(QObject, fset = setActivePackage, notify = activePackageChanged)
    def activePackage(self) -> dict:
        return self._active_package

    def setViewCategory(self, category: str = "plugins"):
        self._view_category = category
        self.viewChanged.emit()
    @pyqtProperty(str, fset = setViewCategory, notify = viewChanged)
    def viewCategory(self) -> str:
        return self._view_category

    def setViewPage(self, page: str = "overview"):
        self._view_page = page
        self.viewChanged.emit()
    @pyqtProperty(str, fset = setViewPage, notify = viewChanged)
    def viewPage(self) -> str:
        return self._view_page

    def setViewSelection(self, selection: str = ""):
        self._view_selection = selection
        self.viewChanged.emit()
    @pyqtProperty(str, fset = setViewSelection, notify = viewChanged)
    def viewSelection(self) -> str:
        return self._view_selection



    # Expose Models:
    # --------------------------------------------------------------------------
    # TODO: Maybe replace this with simply exposing self._models to Qt and then
    # setting model: toolbox.models.foobar instead of toolbox.foobarModel
    @pyqtProperty(QObject, notify = metadataChanged)
    def authorsModel(self) -> AuthorsModel:
        return self._models["authors"]

    @pyqtProperty(QObject, notify = metadataChanged)
    def packagesModel(self) -> PackagesModel:
        return self._models["packages"]

    @pyqtProperty(QObject, notify = metadataChanged)
    def pluginsShowcaseModel(self) -> PackagesModel:
        return self._models["plugins_showcase"]

    @pyqtProperty(QObject, notify = metadataChanged)
    def pluginsInstalledModel(self) -> PackagesModel:
        return self._models["plugins_installed"]

    @pyqtProperty(QObject, notify = metadataChanged)
    def materialsShowcaseModel(self) -> PackagesModel:
        return self._models["materials_showcase"]

    @pyqtProperty(QObject, notify = metadataChanged)
    def materialsInstalledModel(self) -> PackagesModel:
        return self._models["materials_installed"]



    # Filter Models:
    # --------------------------------------------------------------------------
    @pyqtSlot(str, str, str)
    def filterModelByProp(self, modelType: str, filterType: str, parameter: str):
        if not self._models[modelType]:
            Logger.log("w", "Toolbox: Couldn't filter %s model because it doesn't exist.", modelType)
            return
        self._models[modelType].setFilter({ filterType: parameter })
        self.filterChanged.emit()

    @pyqtSlot()
    def removeFilters(self, modelType: str):
        if not self._models[modelType]:
            Logger.log("w", "Toolbox: Couldn't remove filters on %s model because it doesn't exist.", modelType)
            return
        self._models[modelType].setFilter({})
        self.filterChanged.emit()
