# Copyright (c) 2018 Ultimaker B.V.
# Toolbox is released under the terms of the LGPLv3 or higher.

import json
import os
import tempfile
import platform
from typing import cast, Any, Dict, List, Set, TYPE_CHECKING, Tuple, Optional, Union

from PyQt5.QtCore import QUrl, QObject, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry
from UM.Extension import Extension
from UM.Qt.ListModel import ListModel
from UM.i18n import i18nCatalog
from UM.Version import Version

import cura
from cura.CuraApplication import CuraApplication

from .AuthorsModel import AuthorsModel
from .PackagesModel import PackagesModel

if TYPE_CHECKING:
    from cura.Settings.GlobalStack import GlobalStack

i18n_catalog = i18nCatalog("cura")


##  The Toolbox class is responsible of communicating with the server through the API
class Toolbox(QObject, Extension):
    DEFAULT_CLOUD_API_ROOT = "https://api.ultimaker.com" #type: str
    DEFAULT_CLOUD_API_VERSION = 1 #type: int

    def __init__(self, application: CuraApplication) -> None:
        super().__init__()

        self._application = application  # type: CuraApplication

        self._sdk_version = None  # type: Optional[Union[str, int]]
        self._cloud_api_version = None  # type: Optional[int]
        self._cloud_api_root = None  # type: Optional[str]
        self._api_url = None  # type: Optional[str]

        # Network:
        self._download_request = None  # type: Optional[QNetworkRequest]
        self._download_reply = None  # type: Optional[QNetworkReply]
        self._download_progress = 0  # type: float
        self._is_downloading = False  # type: bool
        self._network_manager = None  # type: Optional[QNetworkAccessManager]
        self._request_header = [
            b"User-Agent",
            str.encode(
                "%s/%s (%s %s)" % (
                    self._application.getApplicationName(),
                    self._application.getVersion(),
                    platform.system(),
                    platform.machine(),
                )
            )
        ]
        self._request_urls = {}  # type: Dict[str, QUrl]
        self._to_update = []  # type: List[str] # Package_ids that are waiting to be updated
        self._old_plugin_ids = set()  # type: Set[str]
        self._old_plugin_metadata = dict()  # type: Dict[str, Dict[str, Any]]

        # Data:
        self._metadata = {
            "authors":             [],
            "packages":            [],
            "plugins_showcase":    [],
            "plugins_available":   [],
            "plugins_installed":   [],
            "materials_showcase":  [],
            "materials_available": [],
            "materials_installed": [],
            "materials_generic":   []
        }  # type: Dict[str, List[Any]]

        # Models:
        self._models = {
            "authors":             AuthorsModel(self),
            "packages":            PackagesModel(self),
            "plugins_showcase":    PackagesModel(self),
            "plugins_available":   PackagesModel(self),
            "plugins_installed":   PackagesModel(self),
            "materials_showcase":  AuthorsModel(self),
            "materials_available": AuthorsModel(self),
            "materials_installed": PackagesModel(self),
            "materials_generic":   PackagesModel(self)
        }  # type: Dict[str, ListModel]

        # These properties are for keeping track of the UI state:
        # ----------------------------------------------------------------------
        # View category defines which filter to use, and therefore effectively
        # which category is currently being displayed. For example, possible
        # values include "plugin" or "material", but also "installed".
        self._view_category = "plugin"  # type: str

        # View page defines which type of page layout to use. For example,
        # possible values include "overview", "detail" or "author".
        self._view_page = "loading"  # type: str

        # Active package refers to which package is currently being downloaded,
        # installed, or otherwise modified.
        self._active_package = None  # type: Optional[Dict[str, Any]]

        self._dialog = None  # type: Optional[QObject]
        self._confirm_reset_dialog = None  # type: Optional[QObject]
        self._resetUninstallVariables()

        self._restart_required = False  # type: bool

        # variables for the license agreement dialog
        self._license_dialog_plugin_name = ""  # type: str
        self._license_dialog_license_content = ""  # type: str
        self._license_dialog_plugin_file_location = ""  # type: str
        self._restart_dialog_message = ""  # type: str

        self._application.initializationFinished.connect(self._onAppInitialized)

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
    uninstallVariablesChanged = pyqtSignal()

    def _resetUninstallVariables(self) -> None:
        self._package_id_to_uninstall = None  # type: Optional[str]
        self._package_name_to_uninstall = ""
        self._package_used_materials = []  # type: List[Tuple[GlobalStack, str, str]]
        self._package_used_qualities = []  # type: List[Tuple[GlobalStack, str, str]]

    @pyqtSlot(result = str)
    def getLicenseDialogPluginName(self) -> str:
        return self._license_dialog_plugin_name

    @pyqtSlot(result = str)
    def getLicenseDialogPluginFileLocation(self) -> str:
        return self._license_dialog_plugin_file_location

    @pyqtSlot(result = str)
    def getLicenseDialogLicenseContent(self) -> str:
        return self._license_dialog_license_content

    def openLicenseDialog(self, plugin_name: str, license_content: str, plugin_file_location: str) -> None:
        self._license_dialog_plugin_name = plugin_name
        self._license_dialog_license_content = license_content
        self._license_dialog_plugin_file_location = plugin_file_location
        self.showLicenseDialog.emit()

    # This is a plugin, so most of the components required are not ready when
    # this is initialized. Therefore, we wait until the application is ready.
    def _onAppInitialized(self) -> None:
        self._plugin_registry = self._application.getPluginRegistry()
        self._package_manager = self._application.getPackageManager()
        self._sdk_version = self._getSDKVersion()
        self._cloud_api_version = self._getCloudAPIVersion()
        self._cloud_api_root = self._getCloudAPIRoot()
        self._api_url = "{cloud_api_root}/cura-packages/v{cloud_api_version}/cura/v{sdk_version}".format(
            cloud_api_root=self._cloud_api_root,
            cloud_api_version=self._cloud_api_version,
            sdk_version=self._sdk_version
        )
        self._request_urls = {
            "authors": QUrl("{base_url}/authors".format(base_url=self._api_url)),
            "packages": QUrl("{base_url}/packages".format(base_url=self._api_url)),
            "plugins_showcase": QUrl("{base_url}/showcase".format(base_url=self._api_url)),
            "plugins_available": QUrl("{base_url}/packages?package_type=plugin".format(base_url=self._api_url)),
            "materials_showcase": QUrl("{base_url}/showcase".format(base_url=self._api_url)),
            "materials_available": QUrl("{base_url}/packages?package_type=material".format(base_url=self._api_url)),
            "materials_generic": QUrl("{base_url}/packages?package_type=material&tags=generic".format(base_url=self._api_url))
        }

    # Get the API root for the packages API depending on Cura version settings.
    def _getCloudAPIRoot(self) -> str:
        if not hasattr(cura, "CuraVersion"):
            return self.DEFAULT_CLOUD_API_ROOT
        if not hasattr(cura.CuraVersion, "CuraCloudAPIRoot"): # type: ignore
            return self.DEFAULT_CLOUD_API_ROOT
        if not cura.CuraVersion.CuraCloudAPIRoot: # type: ignore
            return self.DEFAULT_CLOUD_API_ROOT
        return cura.CuraVersion.CuraCloudAPIRoot # type: ignore

    # Get the cloud API version from CuraVersion
    def _getCloudAPIVersion(self) -> int:
        if not hasattr(cura, "CuraVersion"):
            return self.DEFAULT_CLOUD_API_VERSION
        if not hasattr(cura.CuraVersion, "CuraCloudAPIVersion"): # type: ignore
            return self.DEFAULT_CLOUD_API_VERSION
        if not cura.CuraVersion.CuraCloudAPIVersion: # type: ignore
            return self.DEFAULT_CLOUD_API_VERSION
        return cura.CuraVersion.CuraCloudAPIVersion # type: ignore

    # Get the packages version depending on Cura version settings.
    def _getSDKVersion(self) -> Union[int, str]:
        if not hasattr(cura, "CuraVersion"):
            return self._plugin_registry.APIVersion
        if not hasattr(cura.CuraVersion, "CuraSDKVersion"):  # type: ignore
            return self._plugin_registry.APIVersion
        if not cura.CuraVersion.CuraSDKVersion:  # type: ignore
            return self._plugin_registry.APIVersion
        return cura.CuraVersion.CuraSDKVersion  # type: ignore

    @pyqtSlot()
    def browsePackages(self) -> None:
        # Create the network manager:
        # This was formerly its own function but really had no reason to be as
        # it was never called more than once ever.
        if self._network_manager is not None:
            self._network_manager.finished.disconnect(self._onRequestFinished)
            self._network_manager.networkAccessibleChanged.disconnect(self._onNetworkAccessibleChanged)
        self._network_manager = QNetworkAccessManager()
        self._network_manager.finished.connect(self._onRequestFinished)
        self._network_manager.networkAccessibleChanged.connect(self._onNetworkAccessibleChanged)

        # Make remote requests:
        self._makeRequestByType("packages")
        self._makeRequestByType("authors")
        # TODO: Uncomment in the future when the tag-filtered api calls work in the cloud server
        # self._makeRequestByType("plugins_showcase")
        # self._makeRequestByType("plugins_available")
        # self._makeRequestByType("materials_showcase")
        # self._makeRequestByType("materials_available")
        # self._makeRequestByType("materials_generic")

        # Gather installed packages:
        self._updateInstalledModels()

        if not self._dialog:
            self._dialog = self._createDialog("Toolbox.qml")

        if not self._dialog:
            Logger.log("e", "Unexpected error trying to create the 'Toolbox' dialog.")
            return

        self._dialog.show()

        # Apply enabled/disabled state to installed plugins
        self.enabledChanged.emit()

    def _createDialog(self, qml_name: str) -> Optional[QObject]:
        Logger.log("d", "Toolbox: Creating dialog [%s].", qml_name)
        plugin_path = PluginRegistry.getInstance().getPluginPath(self.getPluginId())
        if not plugin_path:
            return None
        path = os.path.join(plugin_path, "resources", "qml", qml_name)
        
        dialog = self._application.createQmlComponent(path, {"toolbox": self})
        if not dialog:
            raise Exception("Failed to create toolbox dialog")
        return dialog

    def _convertPluginMetadata(self, plugin: Dict[str, Any]) -> Dict[str, Any]:
        formatted = {
            "package_id": plugin["id"],
            "package_type": "plugin",
            "display_name": plugin["plugin"]["name"],
            "package_version": plugin["plugin"]["version"],
            "sdk_version": plugin["plugin"]["api"],
            "author": {
                "author_id": plugin["plugin"]["author"],
                "display_name": plugin["plugin"]["author"]
            },
            "is_installed": True,
            "description": plugin["plugin"]["description"]
        }
        return formatted

    @pyqtSlot()
    def _updateInstalledModels(self) -> None:
        # This is moved here to avoid code duplication and so that after installing plugins they get removed from the
        # list of old plugins
        old_plugin_ids = self._plugin_registry.getInstalledPlugins()
        installed_package_ids = self._package_manager.getAllInstalledPackageIDs()
        scheduled_to_remove_package_ids = self._package_manager.getToRemovePackageIDs()

        self._old_plugin_ids = set()
        self._old_plugin_metadata = dict()

        for plugin_id in old_plugin_ids:
            # Neither the installed packages nor the packages that are scheduled to remove are old plugins
            if plugin_id not in installed_package_ids and plugin_id not in scheduled_to_remove_package_ids:
                Logger.log('i', 'Found a plugin that was installed with the old plugin browser: %s', plugin_id)

                old_metadata = self._plugin_registry.getMetaData(plugin_id)
                new_metadata = self._convertPluginMetadata(old_metadata)

                self._old_plugin_ids.add(plugin_id)
                self._old_plugin_metadata[new_metadata["package_id"]] = new_metadata

        all_packages = self._package_manager.getAllInstalledPackagesInfo()
        if "plugin" in all_packages:
            # For old plugins, we only want to include the old custom plugin that were installed via the old toolbox.
            # The bundled plugins will be included in JSON files in the "bundled_packages" folder, so the bundled
            # plugins should be excluded from the old plugins list/dict.
            all_plugin_package_ids = set(package["package_id"] for package in all_packages["plugin"])
            self._old_plugin_ids = set(plugin_id for plugin_id in self._old_plugin_ids
                                    if plugin_id not in all_plugin_package_ids)
            self._old_plugin_metadata = {k: v for k, v in self._old_plugin_metadata.items() if k in self._old_plugin_ids}

            self._metadata["plugins_installed"] = all_packages["plugin"] + list(self._old_plugin_metadata.values())
            self._models["plugins_installed"].setMetadata(self._metadata["plugins_installed"])
            self.metadataChanged.emit()
        if "material" in all_packages:
            self._metadata["materials_installed"] = all_packages["material"]
            # TODO: ADD MATERIALS HERE ONCE MATERIALS PORTION OF TOOLBOX IS LIVE
            self._models["materials_installed"].setMetadata(self._metadata["materials_installed"])
            self.metadataChanged.emit()

    @pyqtSlot(str)
    def install(self, file_path: str) -> None:
        self._package_manager.installPackage(file_path)
        self.installChanged.emit()
        self._updateInstalledModels()
        self.metadataChanged.emit()
        self._restart_required = True
        self.restartRequiredChanged.emit()

    ##  Check package usage and uninstall
    #   If the package is in use, you'll get a confirmation dialog to set everything to default
    @pyqtSlot(str)
    def checkPackageUsageAndUninstall(self, package_id: str) -> None:
        package_used_materials, package_used_qualities = self._package_manager.getMachinesUsingPackage(package_id)
        if package_used_materials or package_used_qualities:
            # Set up "uninstall variables" for resetMaterialsQualitiesAndUninstall
            self._package_id_to_uninstall = package_id
            package_info = self._package_manager.getInstalledPackageInfo(package_id)
            self._package_name_to_uninstall = package_info.get("display_name", package_info.get("package_id"))
            self._package_used_materials = package_used_materials
            self._package_used_qualities = package_used_qualities
            # Ask change to default material / profile
            if self._confirm_reset_dialog is None:
                self._confirm_reset_dialog = self._createDialog("ToolboxConfirmUninstallResetDialog.qml")
            self.uninstallVariablesChanged.emit()
            if self._confirm_reset_dialog is None:
                Logger.log("e", "ToolboxConfirmUninstallResetDialog should have been initialized, but it is not. Not showing dialog and not uninstalling package.")
            else:
                self._confirm_reset_dialog.show()
        else:
            # Plain uninstall
            self.uninstall(package_id)

    @pyqtProperty(str, notify = uninstallVariablesChanged)
    def pluginToUninstall(self) -> str:
        return self._package_name_to_uninstall

    @pyqtProperty(str, notify = uninstallVariablesChanged)
    def uninstallUsedMaterials(self) -> str:
        return "\n".join(["%s (%s)" % (str(global_stack.getName()), material) for global_stack, extruder_nr, material in self._package_used_materials])

    @pyqtProperty(str, notify = uninstallVariablesChanged)
    def uninstallUsedQualities(self) -> str:
        return "\n".join(["%s (%s)" % (str(global_stack.getName()), quality) for global_stack, extruder_nr, quality in self._package_used_qualities])

    @pyqtSlot()
    def closeConfirmResetDialog(self) -> None:
        if self._confirm_reset_dialog is not None:
            self._confirm_reset_dialog.close()

    ##  Uses "uninstall variables" to reset qualities and materials, then uninstall
    #   It's used as an action on Confirm reset on Uninstall
    @pyqtSlot()
    def resetMaterialsQualitiesAndUninstall(self) -> None:
        application = CuraApplication.getInstance()
        material_manager = application.getMaterialManager()
        quality_manager = application.getQualityManager()
        machine_manager = application.getMachineManager()

        for global_stack, extruder_nr, container_id in self._package_used_materials:
            default_material_node = material_manager.getDefaultMaterial(global_stack, extruder_nr, global_stack.extruders[extruder_nr].variant.getName())
            machine_manager.setMaterial(extruder_nr, default_material_node, global_stack = global_stack)
        for global_stack, extruder_nr, container_id in self._package_used_qualities:
            default_quality_group = quality_manager.getDefaultQualityType(global_stack)
            machine_manager.setQualityGroup(default_quality_group, global_stack = global_stack)

        if self._package_id_to_uninstall is not None:
            self._markPackageMaterialsAsToBeUninstalled(self._package_id_to_uninstall)
            self.uninstall(self._package_id_to_uninstall)
        self._resetUninstallVariables()
        self.closeConfirmResetDialog()

    def _markPackageMaterialsAsToBeUninstalled(self, package_id: str) -> None:
        container_registry = self._application.getContainerRegistry()

        all_containers = self._package_manager.getPackageContainerIds(package_id)
        for container_id in all_containers:
            containers = container_registry.findInstanceContainers(id = container_id)
            if not containers:
                continue
            container = containers[0]
            if container.getMetaDataEntry("type") != "material":
                continue
            root_material_id = container.getMetaDataEntry("base_file")
            root_material_containers = container_registry.findInstanceContainers(id = root_material_id)
            if not root_material_containers:
                continue
            root_material_container = root_material_containers[0]
            root_material_container.setMetaDataEntry("removed", True)

    @pyqtSlot(str)
    def uninstall(self, package_id: str) -> None:
        self._package_manager.removePackage(package_id, force_add = True)
        self.installChanged.emit()
        self._updateInstalledModels()
        self.metadataChanged.emit()
        self._restart_required = True
        self.restartRequiredChanged.emit()

    ##  Actual update packages that are in self._to_update
    def _update(self) -> None:
        if self._to_update:
            plugin_id = self._to_update.pop(0)
            remote_package = self.getRemotePackage(plugin_id)
            if remote_package:
                download_url = remote_package["download_url"]
                Logger.log("d", "Updating package [%s]..." % plugin_id)
                self.startDownload(download_url)
            else:
                Logger.log("e", "Could not update package [%s] because there is no remote package info available.", plugin_id)

        if self._to_update:
            self._application.callLater(self._update)

    ##  Update a plugin by plugin_id
    @pyqtSlot(str)
    def update(self, plugin_id: str) -> None:
        self._to_update.append(plugin_id)
        self._application.callLater(self._update)

    @pyqtSlot(str)
    def enable(self, plugin_id: str) -> None:
        self._plugin_registry.enablePlugin(plugin_id)
        self.enabledChanged.emit()
        Logger.log("i", "%s was set as 'active'.", plugin_id)
        self._restart_required = True
        self.restartRequiredChanged.emit()

    @pyqtSlot(str)
    def disable(self, plugin_id: str) -> None:
        self._plugin_registry.disablePlugin(plugin_id)
        self.enabledChanged.emit()
        Logger.log("i", "%s was set as 'deactive'.", plugin_id)
        self._restart_required = True
        self.restartRequiredChanged.emit()

    @pyqtProperty(bool, notify = metadataChanged)
    def dataReady(self) -> bool:
        return self._packages_model is not None

    @pyqtProperty(bool, notify = restartRequiredChanged)
    def restartRequired(self) -> bool:
        return self._restart_required

    @pyqtSlot()
    def restart(self) -> None:
        self._application.windowClosed()

    def getRemotePackage(self, package_id: str) -> Optional[Dict]:
        # TODO: make the lookup in a dict, not a loop. canUpdate is called for every item.
        remote_package = None
        for package in self._metadata["packages"]:
            if package["package_id"] == package_id:
                remote_package = package
                break
        return remote_package

    # Checks
    # --------------------------------------------------------------------------
    @pyqtSlot(str, result = bool)
    def canUpdate(self, package_id: str) -> bool:
        local_package = self._package_manager.getInstalledPackageInfo(package_id)
        if local_package is None:
            Logger.log("i", "Could not find package [%s] as installed in the package manager, fall back to check the old plugins",
                       package_id)
            local_package = self.getOldPluginPackageMetadata(package_id)
            if local_package is None:
                Logger.log("i", "Could not find package [%s] in the old plugins", package_id)
                return False

        remote_package = self.getRemotePackage(package_id)
        if remote_package is None:
            return False

        local_version = Version(local_package["package_version"])
        remote_version = Version(remote_package["package_version"])
        can_upgrade = False
        if remote_version > local_version:
            can_upgrade = True
        # A package with the same version can be built to have different SDK versions. So, for a package with the same
        # version, we also need to check if the current one has a lower SDK version. If so, this package should also
        # be upgradable.
        elif remote_version == local_version:
            can_upgrade = local_package.get("sdk_version", 0) < remote_package.get("sdk_version", 0)

        return can_upgrade

    @pyqtSlot(str, result = bool)
    def canDowngrade(self, package_id: str) -> bool:
        # If the currently installed version is higher than the bundled version (if present), the we can downgrade
        # this package.
        local_package = self._package_manager.getInstalledPackageInfo(package_id)
        if local_package is None:
            return False

        bundled_package = self._package_manager.getBundledPackageInfo(package_id)
        if bundled_package is None:
            return False

        local_version = Version(local_package["package_version"])
        bundled_version = Version(bundled_package["package_version"])
        return bundled_version < local_version

    @pyqtSlot(str, result = bool)
    def isInstalled(self, package_id: str) -> bool:
        result = self._package_manager.isPackageInstalled(package_id)
        # Also check the old plugins list if it's not found in the package manager.
        if not result:
            result = self.isOldPlugin(package_id)
        return result

    @pyqtSlot(str, result = int)
    def getNumberOfInstalledPackagesByAuthor(self, author_id: str) -> int:
        count = 0
        for package in self._metadata["materials_installed"]:
            if package["author"]["author_id"] == author_id:
                count += 1
        return count

    # This slot is only used to get the number of material packages by author, not any other type of packages.
    @pyqtSlot(str, result = int)
    def getTotalNumberOfMaterialPackagesByAuthor(self, author_id: str) -> int:
        count = 0
        for package in self._metadata["packages"]:
            if package["package_type"] == "material":
                if package["author"]["author_id"] == author_id:
                    count += 1
        return count

    @pyqtSlot(str, result = bool)
    def isEnabled(self, package_id: str) -> bool:
        if package_id in self._plugin_registry.getActivePlugins():
            return True
        return False

    # Check for plugins that were installed with the old plugin browser
    def isOldPlugin(self, plugin_id: str) -> bool:
        if plugin_id in self._old_plugin_ids:
            return True
        return False

    def getOldPluginPackageMetadata(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        return self._old_plugin_metadata.get(plugin_id)

    def loadingComplete(self) -> bool:
        populated = 0
        for list in self._metadata.items():
            if len(list) > 0:
                populated += 1
        if populated == len(self._metadata.items()):
            return True
        return False

    # Make API Calls
    # --------------------------------------------------------------------------
    def _makeRequestByType(self, type: str) -> None:
        Logger.log("i", "Toolbox: Requesting %s metadata from server.", type)
        request = QNetworkRequest(self._request_urls[type])
        request.setRawHeader(*self._request_header)
        if self._network_manager:
            self._network_manager.get(request)

    @pyqtSlot(str)
    def startDownload(self, url: str) -> None:
        Logger.log("i", "Toolbox: Attempting to download & install package from %s.", url)
        url = QUrl(url)
        self._download_request = QNetworkRequest(url)
        if hasattr(QNetworkRequest, "FollowRedirectsAttribute"):
            # Patch for Qt 5.6-5.8
            cast(QNetworkRequest, self._download_request).setAttribute(QNetworkRequest.FollowRedirectsAttribute, True)
        if hasattr(QNetworkRequest, "RedirectPolicyAttribute"):
            # Patch for Qt 5.9+
            cast(QNetworkRequest, self._download_request).setAttribute(QNetworkRequest.RedirectPolicyAttribute, True)
        cast(QNetworkRequest, self._download_request).setRawHeader(*self._request_header)
        self._download_reply = cast(QNetworkAccessManager, self._network_manager).get(self._download_request)
        self.setDownloadProgress(0)
        self.setIsDownloading(True)
        cast(QNetworkReply, self._download_reply).downloadProgress.connect(self._onDownloadProgress)

    @pyqtSlot()
    def cancelDownload(self) -> None:
        Logger.log("i", "Toolbox: User cancelled the download of a plugin.")
        self.resetDownload()

    def resetDownload(self) -> None:
        if self._download_reply:
            try:
                self._download_reply.downloadProgress.disconnect(self._onDownloadProgress)
            except TypeError: #Raised when the method is not connected to the signal yet.
                pass #Don't need to disconnect.
            self._download_reply.abort()
        self._download_reply = None
        self._download_request = None
        self.setDownloadProgress(0)
        self.setIsDownloading(False)

    # Handlers for Network Events
    # --------------------------------------------------------------------------
    def _onNetworkAccessibleChanged(self, network_accessibility: QNetworkAccessManager.NetworkAccessibility) -> None:
        if network_accessibility == QNetworkAccessManager.NotAccessible:
            self.resetDownload()

    def _onRequestFinished(self, reply: QNetworkReply) -> None:
        if reply.error() == QNetworkReply.TimeoutError:
            Logger.log("w", "Got a timeout.")
            self.setViewPage("errored")
            self.resetDownload()
            return

        if reply.error() == QNetworkReply.HostNotFoundError:
            Logger.log("w", "Unable to reach server.")
            self.setViewPage("errored")
            self.resetDownload()
            return

        # HACK: These request are not handled independently at this moment, but together from the "packages" call
        do_not_handle = [
            "materials_available",
            "materials_showcase",
            "materials_generic",
            "plugins_available",
            "plugins_showcase",
        ]

        if reply.operation() == QNetworkAccessManager.GetOperation:
            for type, url in self._request_urls.items():

                # HACK: Do nothing because we'll handle these from the "packages" call
                if type in do_not_handle:
                    continue

                if reply.url() == url:
                    if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) == 200:
                        try:
                            json_data = json.loads(bytes(reply.readAll()).decode("utf-8"))

                            # Check for errors:
                            if "errors" in json_data:
                                for error in json_data["errors"]:
                                    Logger.log("e", "%s", error["title"])
                                return

                            # Create model and apply metadata:
                            if not self._models[type]:
                                Logger.log("e", "Could not find the %s model.", type)
                                break
                            
                            self._metadata[type] = json_data["data"]
                            self._models[type].setMetadata(self._metadata[type])

                            # Do some auto filtering
                            # TODO: Make multiple API calls in the future to handle this
                            if type is "packages":
                                self._models[type].setFilter({"type": "plugin"})
                                self.buildMaterialsModels()
                                self.buildPluginsModels()
                            if type is "authors":
                                self._models[type].setFilter({"package_types": "material"})
                            if type is "materials_generic":
                                self._models[type].setFilter({"tags": "generic"})

                            self.metadataChanged.emit()

                            if self.loadingComplete() is True:
                                self.setViewPage("overview")

                            return
                        except json.decoder.JSONDecodeError:
                            Logger.log("w", "Toolbox: Received invalid JSON for %s.", type)
                            break
                    else:
                        self.setViewPage("errored")
                        self.resetDownload()
                        return

        else:
            # Ignore any operation that is not a get operation
            pass

    def _onDownloadProgress(self, bytes_sent: int, bytes_total: int) -> None:
        if bytes_total > 0:
            new_progress = bytes_sent / bytes_total * 100
            self.setDownloadProgress(new_progress)
            if bytes_sent == bytes_total:
                self.setIsDownloading(False)
                cast(QNetworkReply, self._download_reply).downloadProgress.disconnect(self._onDownloadProgress)
                # Must not delete the temporary file on Windows
                self._temp_plugin_file = tempfile.NamedTemporaryFile(mode = "w+b", suffix = ".curapackage", delete = False)
                file_path = self._temp_plugin_file.name
                # Write first and close, otherwise on Windows, it cannot read the file
                self._temp_plugin_file.write(cast(QNetworkReply, self._download_reply).readAll())
                self._temp_plugin_file.close()
                self._onDownloadComplete(file_path)

    def _onDownloadComplete(self, file_path: str) -> None:
        Logger.log("i", "Toolbox: Download complete.")
        package_info = self._package_manager.getPackageInfo(file_path)
        if not package_info:
            Logger.log("w", "Toolbox: Package file [%s] was not a valid CuraPackage.", file_path)
            return

        license_content = self._package_manager.getPackageLicense(file_path)
        if license_content is not None:
            self.openLicenseDialog(package_info["package_id"], license_content, file_path)
            return

        self.install(file_path)
        return

    # Getter & Setters for Properties:
    # --------------------------------------------------------------------------
    def setDownloadProgress(self, progress: float) -> None:
        if progress != self._download_progress:
            self._download_progress = progress
            self.onDownloadProgressChanged.emit()

    @pyqtProperty(int, fset = setDownloadProgress, notify = onDownloadProgressChanged)
    def downloadProgress(self) -> float:
        return self._download_progress

    def setIsDownloading(self, is_downloading: bool) -> None:
        if self._is_downloading != is_downloading:
            self._is_downloading = is_downloading
            self.onIsDownloadingChanged.emit()

    @pyqtProperty(bool, fset = setIsDownloading, notify = onIsDownloadingChanged)
    def isDownloading(self) -> bool:
        return self._is_downloading

    def setActivePackage(self, package: Dict[str, Any]) -> None:
        self._active_package = package
        self.activePackageChanged.emit()

    @pyqtProperty(QObject, fset = setActivePackage, notify = activePackageChanged)
    def activePackage(self) -> Optional[Dict[str, Any]]:
        return self._active_package

    def setViewCategory(self, category: str = "plugin") -> None:
        self._view_category = category
        self.viewChanged.emit()

    @pyqtProperty(str, fset = setViewCategory, notify = viewChanged)
    def viewCategory(self) -> str:
        return self._view_category

    def setViewPage(self, page: str = "overview") -> None:
        self._view_page = page
        self.viewChanged.emit()

    @pyqtProperty(str, fset = setViewPage, notify = viewChanged)
    def viewPage(self) -> str:
        return self._view_page

    # Exposed Models:
    # --------------------------------------------------------------------------
    @pyqtProperty(QObject, notify = metadataChanged)
    def authorsModel(self) -> AuthorsModel:
        return cast(AuthorsModel, self._models["authors"])

    @pyqtProperty(QObject, notify = metadataChanged)
    def packagesModel(self) -> PackagesModel:
        return cast(PackagesModel, self._models["packages"])

    @pyqtProperty(QObject, notify = metadataChanged)
    def pluginsShowcaseModel(self) -> PackagesModel:
        return cast(PackagesModel, self._models["plugins_showcase"])

    @pyqtProperty(QObject, notify = metadataChanged)
    def pluginsAvailableModel(self) -> PackagesModel:
        return cast(PackagesModel, self._models["plugins_available"])

    @pyqtProperty(QObject, notify = metadataChanged)
    def pluginsInstalledModel(self) -> PackagesModel:
        return cast(PackagesModel, self._models["plugins_installed"])

    @pyqtProperty(QObject, notify = metadataChanged)
    def materialsShowcaseModel(self) -> AuthorsModel:
        return cast(AuthorsModel, self._models["materials_showcase"])

    @pyqtProperty(QObject, notify = metadataChanged)
    def materialsAvailableModel(self) -> AuthorsModel:
        return cast(AuthorsModel, self._models["materials_available"])

    @pyqtProperty(QObject, notify = metadataChanged)
    def materialsInstalledModel(self) -> PackagesModel:
        return cast(PackagesModel, self._models["materials_installed"])

    @pyqtProperty(QObject, notify=metadataChanged)
    def materialsGenericModel(self) -> PackagesModel:
        return cast(PackagesModel, self._models["materials_generic"])

    # Filter Models:
    # --------------------------------------------------------------------------
    @pyqtSlot(str, str, str)
    def filterModelByProp(self, model_type: str, filter_type: str, parameter: str) -> None:
        if not self._models[model_type]:
            Logger.log("w", "Toolbox: Couldn't filter %s model because it doesn't exist.", model_type)
            return
        self._models[model_type].setFilter({filter_type: parameter})
        self.filterChanged.emit()

    @pyqtSlot(str, "QVariantMap")
    def setFilters(self, model_type: str, filter_dict: dict) -> None:
        if not self._models[model_type]:
            Logger.log("w", "Toolbox: Couldn't filter %s model because it doesn't exist.", model_type)
            return
        self._models[model_type].setFilter(filter_dict)
        self.filterChanged.emit()

    @pyqtSlot(str)
    def removeFilters(self, model_type: str) -> None:
        if not self._models[model_type]:
            Logger.log("w", "Toolbox: Couldn't remove filters on %s model because it doesn't exist.", model_type)
            return
        self._models[model_type].setFilter({})
        self.filterChanged.emit()

    # HACK(S):
    # --------------------------------------------------------------------------
    def buildMaterialsModels(self) -> None:
        self._metadata["materials_showcase"] = []
        self._metadata["materials_available"] = []

        processed_authors = [] # type: List[str]

        for item in self._metadata["packages"]:
            if item["package_type"] == "material":

                author = item["author"]
                if author["author_id"] in processed_authors:
                    continue

                # Generic materials to be in the same section
                if "generic" in item["tags"]:
                    self._metadata["materials_generic"].append(item)
                else:
                    if "showcase" in item["tags"]:
                        self._metadata["materials_showcase"].append(author)
                    else:
                        self._metadata["materials_available"].append(author)

                    processed_authors.append(author["author_id"])

        self._models["materials_showcase"].setMetadata(self._metadata["materials_showcase"])
        self._models["materials_available"].setMetadata(self._metadata["materials_available"])
        self._models["materials_generic"].setMetadata(self._metadata["materials_generic"])

    def buildPluginsModels(self) -> None:
        self._metadata["plugins_showcase"] = []
        self._metadata["plugins_available"] = []

        for item in self._metadata["packages"]:
            if item["package_type"] == "plugin":

                if "showcase" in item["tags"]:
                    self._metadata["plugins_showcase"].append(item)
                else:
                    self._metadata["plugins_available"].append(item)

        self._models["plugins_showcase"].setMetadata(self._metadata["plugins_showcase"])
        self._models["plugins_available"].setMetadata(self._metadata["plugins_available"])
