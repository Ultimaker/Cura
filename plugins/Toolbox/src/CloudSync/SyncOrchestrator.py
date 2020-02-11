import os
from typing import List, Dict, Any, cast

from UM import i18n_catalog
from UM.Extension import Extension
from UM.Logger import Logger
from UM.Message import Message
from UM.PluginRegistry import PluginRegistry
from cura.CuraApplication import CuraApplication
from .CloudPackageChecker import CloudPackageChecker
from .CloudPackageManager import CloudPackageManager
from .DiscrepanciesPresenter import DiscrepanciesPresenter
from .DownloadPresenter import DownloadPresenter
from .LicensePresenter import LicensePresenter
from .RestartApplicationPresenter import RestartApplicationPresenter
from .SubscribedPackagesModel import SubscribedPackagesModel


## Orchestrates the synchronizing of packages from the user account to the installed packages
# Example flow:
# - CloudPackageChecker compares a list of packages the user `subscribed` to in their account
#   If there are `discrepancies` between the account and locally installed packages, they are emitted
# - DiscrepanciesPresenter shows a list of packages to be added or removed to the user. It emits the `packageMutations`
#   the user selected to be performed
# - The SyncOrchestrator uses PackageManager to remove local packages the users wants to see removed
# - The DownloadPresenter shows a download progress dialog. It emits A tuple of succeeded and failed downloads
# - The LicensePresenter extracts licenses from the downloaded packages and presents a license for each package to
#   be installed. It emits the `licenseAnswers` signal for accept or declines
# - The CloudPackageManager removes the declined packages from the account
# - The SyncOrchestrator uses PackageManager to install the downloaded packages and delete temp files.
# - The RestartApplicationPresenter notifies the user that a restart is required for changes to take effect
class SyncOrchestrator(Extension):

    def __init__(self, app: CuraApplication) -> None:
        super().__init__()
        # Differentiate This PluginObject from the Toolbox. self.getId() includes _name.
        # getPluginId() will return the same value for The toolbox extension and this one
        self._name = "SyncOrchestrator"

        self._package_manager = app.getPackageManager()
        # Keep a reference to the CloudPackageManager. it watches for installed packages and subscribes to them
        self._cloud_package_manager = CloudPackageManager.getInstance(app)  # type: CloudPackageManager

        self._checker = CloudPackageChecker(app)  # type: CloudPackageChecker
        self._checker.discrepancies.connect(self._onDiscrepancies)

        self._discrepancies_presenter = DiscrepanciesPresenter(app)  # type: DiscrepanciesPresenter
        self._discrepancies_presenter.packageMutations.connect(self._onPackageMutations)

        self._download_presenter = DownloadPresenter(app)  # type: DownloadPresenter

        self._license_presenter = LicensePresenter(app)  # type: LicensePresenter
        self._license_presenter.licenseAnswers.connect(self._onLicenseAnswers)

        self._restart_presenter = RestartApplicationPresenter(app)

    def _onDiscrepancies(self, model: SubscribedPackagesModel) -> None:
        plugin_path = cast(str, PluginRegistry.getInstance().getPluginPath(self.getPluginId()))
        self._discrepancies_presenter.present(plugin_path, model)

    def _onPackageMutations(self, mutations: SubscribedPackagesModel) -> None:
        self._download_presenter = self._download_presenter.resetCopy()
        self._download_presenter.done.connect(self._onDownloadFinished)
        self._download_presenter.download(mutations)

    ## Called when a set of packages have finished downloading
    # \param success_items: Dict[package_id, Dict[str, str]]
    # \param error_items: List[package_id]
    def _onDownloadFinished(self, success_items: Dict[str, Dict[str, str]], error_items: List[str]) -> None:
        if error_items:
            message = i18n_catalog.i18nc("@info:generic", "{} plugins failed to download".format(len(error_items)))
            self._showErrorMessage(message)

        plugin_path = cast(str, PluginRegistry.getInstance().getPluginPath(self.getPluginId()))
        self._license_presenter = self._license_presenter.resetCopy()
        self._license_presenter.licenseAnswers.connect(self._onLicenseAnswers)
        self._license_presenter.present(plugin_path, success_items)

    # Called when user has accepted / declined all licenses for the downloaded packages
    def _onLicenseAnswers(self, answers: List[Dict[str, Any]]) -> None:
        has_changes = False  # True when at least one package is installed

        for item in answers:
            if item["accepted"]:
                # install and subscribe packages
                if not self._package_manager.installPackage(item["package_path"]):
                    message = "Could not install {}".format(item["package_id"])
                    self._showErrorMessage(message)
                    continue
                has_changes = True
            else:
                self._cloud_package_manager.unsubscribe(item["package_id"])
            # delete temp file
            os.remove(item["package_path"])

        if has_changes:
            self._restart_presenter.present()

    ## Logs an error and shows it to the user
    def _showErrorMessage(self, text: str):
        Logger.error(text)
        Message(text, lifetime=0).show()
