from UM.Extension import Extension
from UM.PluginRegistry import PluginRegistry
from cura.CuraApplication import CuraApplication
from plugins.Toolbox import CloudPackageChecker
from plugins.Toolbox.src.CloudSync.DiscrepanciesPresenter import DiscrepanciesPresenter
from plugins.Toolbox.src.CloudSync.DownloadPresenter import DownloadPresenter
from plugins.Toolbox.src.CloudSync.SubscribedPackagesModel import SubscribedPackagesModel


## Orchestrates the synchronizing of packages from the user account to the installed packages
# Example flow:
# - CloudPackageChecker compares a list of packages the user `subscribed` to in their account
#   If there are `discrepancies` between the account and locally installed packages, they are emitted
# - DiscrepanciesPresenter shows a list of packages to be added or removed to the user. It emits the `packageMutations`
#   the user selected to be performed
# - The SyncOrchestrator uses PackageManager to remove local packages the users wants to see removed
# - The DownloadPresenter shows a download progress dialog. It emits A tuple of succeeded and failed downloads
# - The LicencePresenter extracts licences from the downloaded packages and presents a licence for each package to
# - be installed. It emits the `licenceAnswers` {'packageId' : bool} for accept or declines
# - The CloudPackageManager removes the declined packages from the account
# - The SyncOrchestrator uses PackageManager to install the downloaded packages.
# - Bliss / profit / done
class SyncOrchestrator(Extension):

    def __init__(self, app: CuraApplication):
        super().__init__()

        self._checker = CloudPackageChecker(app)
        self._checker.discrepancies.connect(self._onDiscrepancies)

        self._discrepanciesPresenter = DiscrepanciesPresenter(app)
        self._discrepanciesPresenter.packageMutations.connect(self._onPackageMutations)

        self._downloadPresenter = DownloadPresenter(app)

    def _onDiscrepancies(self, model: SubscribedPackagesModel):
        plugin_path = PluginRegistry.getInstance().getPluginPath(self.getPluginId())
        self._discrepanciesPresenter.present(plugin_path, model)

    def _onPackageMutations(self, mutations: SubscribedPackagesModel):
        self._downloadPresenter.download(mutations)
