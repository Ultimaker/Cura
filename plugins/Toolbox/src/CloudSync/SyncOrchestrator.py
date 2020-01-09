from typing import List, Dict

from UM.Extension import Extension
from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry
from cura.CuraApplication import CuraApplication
from plugins.Toolbox import CloudPackageChecker
from plugins.Toolbox.src.CloudSync.DiscrepanciesPresenter import DiscrepanciesPresenter
from plugins.Toolbox.src.CloudSync.DownloadPresenter import DownloadPresenter
from plugins.Toolbox.src.CloudSync.LicensePresenter import LicensePresenter
from plugins.Toolbox.src.CloudSync.SubscribedPackagesModel import SubscribedPackagesModel


## Orchestrates the synchronizing of packages from the user account to the installed packages
# Example flow:
# - CloudPackageChecker compares a list of packages the user `subscribed` to in their account
#   If there are `discrepancies` between the account and locally installed packages, they are emitted
# - DiscrepanciesPresenter shows a list of packages to be added or removed to the user. It emits the `packageMutations`
#   the user selected to be performed
# - The SyncOrchestrator uses PackageManager to remove local packages the users wants to see removed
# - The DownloadPresenter shows a download progress dialog. It emits A tuple of succeeded and failed downloads
# - The LicensePresenter extracts licenses from the downloaded packages and presents a license for each package to
#   be installed. It emits the `licenseAnswers` {'packageId' : bool} for accept or declines
# - The CloudPackageManager removes the declined packages from the account
# - The SyncOrchestrator uses PackageManager to install the downloaded packages.
# - Bliss / profit / done
class SyncOrchestrator(Extension):

    def __init__(self, app: CuraApplication):
        super().__init__()
        # Differentiate This PluginObject from the Toolbox. self.getId() includes _name.
        # getPluginId() will return the same value for The toolbox extension and this one
        self._name = "SyncOrchestrator"

        self._checker = CloudPackageChecker(app)  # type: CloudPackageChecker
        self._checker.discrepancies.connect(self._onDiscrepancies)

        self._discrepanciesPresenter = DiscrepanciesPresenter(app)  # type: DiscrepanciesPresenter
        self._discrepanciesPresenter.packageMutations.connect(self._onPackageMutations)

        self._downloadPresenter = DownloadPresenter(app)  # type: DownloadPresenter

        self._licensePresenter = LicensePresenter(app)  # type: LicensePresenter
        self._licensePresenter.licenseAnswers.connect(self._onLicenseAnswers)

    def _onDiscrepancies(self, model: SubscribedPackagesModel):
        plugin_path = PluginRegistry.getInstance().getPluginPath(self.getPluginId())
        self._discrepanciesPresenter.present(plugin_path, model)

    def _onPackageMutations(self, mutations: SubscribedPackagesModel):
        self._downloadPresenter = self._downloadPresenter.resetCopy()
        self._downloadPresenter.done.connect(self._onDownloadFinished)
        self._downloadPresenter.download(mutations)

    ## Called when a set of packages have finished downloading
    # \param success_items: Dict[package_id, file_path]
    # \param error_items: List[package_id]
    def _onDownloadFinished(self, success_items: Dict[str, str], error_items: List[str]):
        # todo handle error items
        plugin_path = PluginRegistry.getInstance().getPluginPath(self.getPluginId())
        self._licensePresenter.present(plugin_path, success_items)

    # Called when user has accepted / declined all licenses for the downloaded packages
    def _onLicenseAnswers(self, answers: Dict[str, bool]):
        Logger.debug("Got license answers: {}", answers)


