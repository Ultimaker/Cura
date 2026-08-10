#  Copyright (c) 2021 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.
import tempfile
import json
import os.path

from PyQt6.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, Qt
from typing import cast, Dict, List, Optional, Set, TYPE_CHECKING

from UM.i18n import i18nCatalog
from UM.Qt.ListModel import ListModel
from UM.TaskManagement.HttpRequestScope import JsonDecoratorScope
from UM.TaskManagement.HttpRequestManager import HttpRequestData, HttpRequestManager
from UM.Logger import Logger
from UM import PluginRegistry

from cura.CuraApplication import CuraApplication
from cura.CuraPackageManager import CuraPackageManager
from cura.UltimakerCloud.UltimakerCloudScope import UltimakerCloudScope  # To make requests to the Ultimaker API with correct authorization.

from .PackageModel import PackageModel
from .Constants import USER_PACKAGES_URL, PACKAGES_URL

if TYPE_CHECKING:
    from PyQt6.QtCore import QObject
    from PyQt6.QtNetwork import QNetworkReply

catalog = i18nCatalog("cura")


class PackageList(ListModel):
    """ A List model for Packages, this class serves as parent class for more detailed implementations.
    such as Packages obtained from Remote or Local source
    """
    PackageRole = Qt.ItemDataRole.UserRole + 1
    DISK_WRITE_BUFFER_SIZE = 256 * 1024  # 256 KB

    def __init__(self, parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)
        self._package_manager: CuraPackageManager = cast(CuraPackageManager, CuraApplication.getInstance().getPackageManager())
        self._plugin_registry: PluginRegistry = CuraApplication.getInstance().getPluginRegistry()
        self._account = CuraApplication.getInstance().getCuraAPI().account
        self._error_message = ""
        self.addRoleName(self.PackageRole, "package")
        self._is_loading = False
        self._has_more = False
        self._has_footer = True
        self._to_install: Dict[str, str] = {}

        self._ongoing_requests: Dict[str, Optional[HttpRequestData]] = {"download_package": None}
        self._scope = JsonDecoratorScope(UltimakerCloudScope(CuraApplication.getInstance()))
        self._license_dialogs: Dict[str, QObject] = {}

        self._sort_by_install_status = False

        # Queue for sequential bulk updates triggered from the tab-level "Update all" button.
        self._pending_bulk_update_ids: List[str] = []
        self._active_bulk_update_id: Optional[str] = None
        self._bulk_update_in_progress = False
        self._package_manager.packageInstalled.connect(self._onBulkUpdateFinished)
        self._package_manager.packageInstallingFailed.connect(self._onBulkUpdateFinished)
        self._package_manager.packagesWithUpdateChanged.connect(self.hasUpdatablePackagesChanged)

    def __del__(self) -> None:
        """ When this object is deleted it will loop through all registered API requests and aborts them """
        try:
            self.isLoadingChanged.disconnect()
            self.hasMoreChanged.disconnect()
        except RuntimeError:
            pass

        try:
            self._package_manager.packageInstalled.disconnect(self._onBulkUpdateFinished)
            self._package_manager.packageInstallingFailed.disconnect(self._onBulkUpdateFinished)
            self._package_manager.packagesWithUpdateChanged.disconnect(self.hasUpdatablePackagesChanged)
        except RuntimeError:
            pass

        self.cleanUpAPIRequest()

    def abortRequest(self, request_id: str) -> None:
        """Aborts a single request"""
        if request_id in self._ongoing_requests and self._ongoing_requests[request_id]:
            HttpRequestManager.getInstance().abortRequest(self._ongoing_requests[request_id])
            self._ongoing_requests[request_id] = None

    @pyqtSlot()
    def cleanUpAPIRequest(self) -> None:
        for request_id in self._ongoing_requests:
            self.abortRequest(request_id)

    @pyqtSlot()
    def updatePackages(self) -> None:
        """ A Qt slot which will update the List from a source. Actual implementation should be done in the child class"""
        pass

    def reset(self) -> None:
        """ Resets and clears the list"""
        self.clear()

    isLoadingChanged = pyqtSignal() 

    def setIsLoading(self, value: bool) -> None:
        if self._is_loading != value:
            self._is_loading = value
            self.isLoadingChanged.emit()
            if not value:
                self.hasUpdatablePackagesChanged.emit()

    @pyqtProperty(bool, fset = setIsLoading, notify = isLoadingChanged)
    def isLoading(self) -> bool:
        """ Indicating if the the packages are loading
        :return" ``True`` if the list is being obtained, otherwise ``False``
        """
        return self._is_loading

    hasMoreChanged = pyqtSignal()

    def setHasMore(self, value: bool) -> None:
        if self._has_more != value:
            self._has_more = value
            self.hasMoreChanged.emit()

    @pyqtProperty(bool, fset = setHasMore, notify = hasMoreChanged)
    def hasMore(self) -> bool:
        """ Indicating if there are more packages available to load.
        :return: ``True`` if there are more packages to load, or ``False``.
        """
        return self._has_more

    errorMessageChanged = pyqtSignal()

    def setErrorMessage(self, error_message: str) -> None:
        if self._error_message != error_message:
            self._error_message = error_message
            self.errorMessageChanged.emit()

    @pyqtProperty(str, notify = errorMessageChanged, fset = setErrorMessage)
    def errorMessage(self) -> str:
        """ If an error occurred getting the list of packages, an error message will be held here.

        If no error occurred (yet), this will be an empty string.
        :return: An error message, if any, or an empty string if everything went okay.
        """
        return self._error_message

    @pyqtProperty(bool, constant = True)
    def hasFooter(self) -> bool:
        """ Indicating if the PackageList should have a Footer visible. For paginated PackageLists
        :return: ``True`` if a Footer should be displayed in the ListView, e.q.: paginated lists, ``False`` Otherwise"""
        return self._has_footer

    def getPackageModel(self, package_id: str) -> Optional[PackageModel]:
        index = self.find("package", package_id)
        data = self.getItem(index)
        if data:
            return data.get("package")
        return None

    bulkUpdateInProgressChanged = pyqtSignal()

    def setBulkUpdateInProgress(self, value: bool) -> None:
        if self._bulk_update_in_progress != value:
            self._bulk_update_in_progress = value
            self.bulkUpdateInProgressChanged.emit()
            self.hasUpdatablePackagesChanged.emit()

    @pyqtProperty(bool, notify = bulkUpdateInProgressChanged)
    def bulkUpdateInProgress(self) -> bool:
        return self._bulk_update_in_progress

    hasUpdatablePackagesChanged = pyqtSignal()

    @pyqtProperty(bool, notify = hasUpdatablePackagesChanged)
    def hasUpdatablePackages(self) -> bool:
        """True when at least one package in this list has a pending update available."""
        return self.updatablePackagesCount >= 1

    @pyqtProperty(int, notify = hasUpdatablePackagesChanged)
    def updatablePackagesCount(self) -> int:
        """Returns the number of packages in this list that have a pending update available."""
        count = 0
        for index in range(self.rowCount()):
            data = self.getItem(index)
            package = data.get("package") if data else None
            if package and package.canUpdate and not package.isMissingPackageInformation:
                count += 1
        return count

    sortByInstallStatusChanged = pyqtSignal()

    def setSortByInstallStatus(self, value: bool) -> None:
        if self._sort_by_install_status != value:
            self._sort_by_install_status = value
            self.sortByInstallStatusChanged.emit()
            if value:
                self._applyInstallStatusSort()
            else:
                self._restoreOrder()

    @pyqtProperty(bool, fset = setSortByInstallStatus, notify = sortByInstallStatusChanged)
    def sortByInstallStatus(self) -> bool:
        """When True the list is sorted so packages with updates bubble to the top, followed by
        installed packages without updates, then the rest ordered by their original release date."""
        return self._sort_by_install_status

    def _applyInstallStatusSort(self) -> None:
        """Re-sort the current items using install/update-status as the primary key.

        Priority order (lower number = closer to top):
          0 – installed and has an update available (Update button)
          1 – installed, no update pending (Uninstall button)
          2 – not installed; preserves original relative order (release date from API)
        Within each priority group the existing relative order is preserved (stable sort).
        """
        def _priority(model) -> int:
            if model.canUpdate:
                return 0
            if model.isInstalled or model.isToBeInstalled:
                return 1
            return 2
        self.sort(_priority, key = "package")

    def _restoreOrder(self) -> None:
        """Re-sort items back into their original API/insertion order."""
        self.sort(lambda model: model._insertion_index, key = "package")

    @pyqtSlot()
    def updateAllPackages(self) -> None:
        """Queue updates for all currently listed packages that can be updated.

        This acts only on the package models present in this specific list instance, which keeps
        the action scoped to the currently visible tab.
        """
        if self._bulk_update_in_progress:
            return

        self._pending_bulk_update_ids = []
        for index in range(self.rowCount()):
            data = self.getItem(index)
            package = data.get("package") if data else None
            if not package or not package.canUpdate or package.isMissingPackageInformation:
                continue
            self._pending_bulk_update_ids.append(package.packageId)

        self.setBulkUpdateInProgress(len(self._pending_bulk_update_ids) > 0)

        self._startNextBulkUpdate()

    def _startNextBulkUpdate(self) -> None:
        while self._pending_bulk_update_ids:
            package_id = self._pending_bulk_update_ids.pop(0)
            package = self.getPackageModel(package_id)
            if not package or not package.canUpdate or package.isMissingPackageInformation or package.busy:
                continue

            self._active_bulk_update_id = package_id
            package.update()
            return

        self._active_bulk_update_id = None
        self.setBulkUpdateInProgress(False)

    @pyqtSlot(str)
    def _onBulkUpdateFinished(self, package_id: str) -> None:
        if package_id != self._active_bulk_update_id:
            return
        self._active_bulk_update_id = None
        self._startNextBulkUpdate()

    def _openLicenseDialog(self, package_id: str, license_content: str) -> None:
        plugin_path = self._plugin_registry.getPluginPath("Marketplace")
        if plugin_path is None:
            plugin_path = os.path.dirname(__file__)

        # create a QML component for the license dialog
        license_dialog_component_path = os.path.join(plugin_path, "resources", "qml", "LicenseDialog.qml")
        dialog = CuraApplication.getInstance().createQmlComponent(license_dialog_component_path, {
            "licenseContent": license_content,
            "packageId": package_id,
            "handler": self
        })
        dialog.show()
        # place dialog in class such that it does not get remove by garbage collector
        self._license_dialogs[package_id] = dialog

    @pyqtSlot(str)
    def onLicenseAccepted(self, package_id: str) -> None:
        # close dialog
        dialog = self._license_dialogs.pop(package_id)
        if dialog is not None:
            dialog.deleteLater()
        # install relevant package
        self._install(package_id)

    @pyqtSlot(str)
    def onLicenseDeclined(self, package_id: str) -> None:
        # close dialog
        dialog = self._license_dialogs.pop(package_id)
        if dialog is not None:
            dialog.deleteLater()
        # reset package card
        self._package_manager.packageInstallingFailed.emit(package_id)

    def _requestInstall(self, package_id: str, update: bool = False) -> None:
        package_path = self._to_install[package_id]
        license_content = self._package_manager.getPackageLicense(package_path)

        if not update and license_content is not None and license_content != "":
            # If installation is not and update, and the packages contains a license then
            # open dialog, prompting the using to accept the plugin license
            self._openLicenseDialog(package_id, license_content)
        else:
            # Otherwise continue the installation
            self._install(package_id, update)

    def _install(self, package_id: str, update: bool = False) -> None:
        package_path = self._to_install.pop(package_id)
        to_be_installed = self._package_manager.installPackage(package_path) is not None
        if not to_be_installed:
            Logger.warning(f"Could not install {package_id}")
            return
        package = self.getPackageModel(package_id)
        if package:
            self.subscribeUserToPackage(package_id, str(package.sdk_version))
        else:
            Logger.log("w", f"Unable to get data on package {package_id}")

    def download(self, package_id: str, url: str, update: bool = False) -> None:
        """Initiate the download request

        :param package_id: the package identification string
        :param url: the URL from which the package needs to be obtained
        :param update: A flag if this is download request is an update process
        """

        if url == "":
            url = f"{PACKAGES_URL}/{package_id}/download"

        def downloadFinished(reply: "QNetworkReply") -> None:
            self._downloadFinished(package_id, reply, update)

        def downloadError(reply: "QNetworkReply", error: "QNetworkReply.NetworkError") -> None:
            self._downloadError(package_id, update, reply, error)

        self._ongoing_requests["download_package"] = HttpRequestManager.getInstance().get(
            url,
            scope = self._scope,
            callback = downloadFinished,
            error_callback = downloadError
        )

    def _downloadFinished(self, package_id: str, reply: "QNetworkReply", update: bool = False) -> None:
        with tempfile.NamedTemporaryFile(mode = "wb+", suffix = ".curapackage", delete = False) as temp_file:
            try:
                bytes_read = reply.read(self.DISK_WRITE_BUFFER_SIZE)
                while bytes_read:
                    temp_file.write(bytes_read)
                    bytes_read = reply.read(self.DISK_WRITE_BUFFER_SIZE)
            except IOError as e:
                Logger.error(f"Failed to write downloaded package to temp file {e}")
                temp_file.close()
                self._downloadError(package_id, update)
            except RuntimeError:
                # Setting the ownership of this object to not qml can still result in a RuntimeError. Which can occur when quickly toggling
                # between de-/constructing Remote or Local PackageLists. This try-except is here to prevent a hard crash when the wrapped C++ object
                # was deleted when it was still parsing the response
                temp_file.close()
                return
        temp_file.close()
        self._to_install[package_id] = temp_file.name
        self._ongoing_requests["download_package"] = None
        self._requestInstall(package_id, update)

    def _downloadError(self, package_id: str, update: bool = False, reply: Optional["QNetworkReply"] = None, error: Optional["QNetworkReply.NetworkError"] = None) -> None:
        if reply:
            try:
                reply_string = bytes(reply.readAll()).decode()
            except UnicodeDecodeError:
                reply_string = "<error message is corrupt too>"
            Logger.error(f"Failed to download package: {package_id} due to {reply_string}")
        self._package_manager.packageInstallingFailed.emit(package_id)

    def subscribeUserToPackage(self, package_id: str, sdk_version: str) -> None:
        """Subscribe the user (if logged in) to the package for a given SDK

         :param package_id: the package identification string
         :param sdk_version: the SDK version
         """
        if self._account.isLoggedIn:
            HttpRequestManager.getInstance().put(
                url = USER_PACKAGES_URL,
                data = json.dumps({"data": {"package_id": package_id, "sdk_version": sdk_version}}).encode(),
                scope = self._scope
            )

    def unsunscribeUserFromPackage(self, package_id: str) -> None:
        """Unsubscribe the user (if logged in) from the package

         :param package_id: the package identification string
         """
        if self._account.isLoggedIn:
            HttpRequestManager.getInstance().delete(url = f"{USER_PACKAGES_URL}/{package_id}", scope = self._scope)

    # --- Handle the manage package buttons ---

    def _connectManageButtonSignals(self, package: PackageModel) -> None:
        package.installPackageTriggered.connect(self.installPackage)
        package.uninstallPackageTriggered.connect(self.uninstallPackage)
        package.updatePackageTriggered.connect(self.updatePackage)

    def installPackage(self, package_id: str, url: str) -> None:
        """Install a package from the Marketplace

        :param package_id: the package identification string
        """
        if not self._package_manager.reinstallPackage(package_id):
            self.download(package_id, url, False)
        else:
            package = self.getPackageModel(package_id)
            if package:
                self.subscribeUserToPackage(package_id, str(package.sdk_version))

    def uninstallPackage(self, package_id: str) -> None:
        """Uninstall a package from the Marketplace

        :param package_id: the package identification string
        """
        self._package_manager.removePackage(package_id)
        self.unsunscribeUserFromPackage(package_id)

    def updatePackage(self, package_id: str, url: str) -> None:
        """Update a package from the Marketplace

        :param package_id: the package identification string
        """
        self._package_manager.removePackage(package_id, force_add = not self._package_manager.isBundledPackage(package_id))
        self.download(package_id, url, True)
