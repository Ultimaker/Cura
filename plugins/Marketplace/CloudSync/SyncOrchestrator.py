# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
from typing import List, Dict, Any, cast

from UM import i18n_catalog
from UM.Extension import Extension
from UM.Logger import Logger
from UM.Message import Message
from UM.PluginRegistry import PluginRegistry
from cura.CuraApplication import CuraApplication
from .CloudPackageChecker import CloudPackageChecker
from .CloudApiClient import CloudApiClient
from .DiscrepanciesPresenter import DiscrepanciesPresenter
from .DownloadPresenter import DownloadPresenter
from .LicensePresenter import LicensePresenter
from .RestartApplicationPresenter import RestartApplicationPresenter
from .SubscribedPackagesModel import SubscribedPackagesModel


class SyncOrchestrator(Extension):
    """Orchestrates the synchronizing of packages from the user account to the installed packages

    Example flow:

    - CloudPackageChecker compares a list of packages the user `subscribed` to in their account
      If there are `discrepancies` between the account and locally installed packages, they are emitted
    - DiscrepanciesPresenter shows a list of packages to be added or removed to the user. It emits the `packageMutations`
      the user selected to be performed
    - The SyncOrchestrator uses PackageManager to remove local packages the users wants to see removed
    - The DownloadPresenter shows a download progress dialog. It emits A tuple of succeeded and failed downloads
    - The LicensePresenter extracts licenses from the downloaded packages and presents a license for each package to
      be installed. It emits the `licenseAnswers` signal for accept or declines
    - The CloudApiClient removes the declined packages from the account
    - The SyncOrchestrator uses PackageManager to install the downloaded packages and delete temp files.
    - The RestartApplicationPresenter notifies the user that a restart is required for changes to take effect
    """

    def __init__(self, app: CuraApplication) -> None:
        super().__init__()
        # Differentiate This PluginObject from the Marketplace. self.getId() includes _name.
        # getPluginId() will return the same value for The Marketplace extension and this one
        self._name = "SyncOrchestrator"

        self._package_manager = app.getPackageManager()
        # Keep a reference to the CloudApiClient. it watches for installed packages and subscribes to them
        self._cloud_api: CloudApiClient = CloudApiClient.getInstance(app)

        self._checker: CloudPackageChecker = CloudPackageChecker(app)
        self._checker.discrepancies.connect(self._onDiscrepancies)

        self._discrepancies_presenter: DiscrepanciesPresenter = DiscrepanciesPresenter(app)
        self._discrepancies_presenter.packageMutations.connect(self._onPackageMutations)

        self._download_presenter: DownloadPresenter = DownloadPresenter(app)

        self._license_presenter: LicensePresenter = LicensePresenter(app)
        self._license_presenter.licenseAnswers.connect(self._onLicenseAnswers)

        self._restart_presenter = RestartApplicationPresenter(app)

    def _onDiscrepancies(self, model: SubscribedPackagesModel) -> None:
        plugin_path = cast(str, PluginRegistry.getInstance().getPluginPath(self.getPluginId()))
        self._discrepancies_presenter.present(plugin_path, model)

    def _onPackageMutations(self, mutations: SubscribedPackagesModel) -> None:
        self._download_presenter = self._download_presenter.resetCopy()
        self._download_presenter.done.connect(self._onDownloadFinished)
        self._download_presenter.download(mutations)

    def _onDownloadFinished(self, success_items: Dict[str, Dict[str, str]], error_items: List[str]) -> None:
        """Called when a set of packages have finished downloading

        :param success_items:: Dict[package_id, Dict[str, str]]
        :param error_items:: List[package_id]
        """
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
                self._cloud_api.unsubscribe(item["package_id"])
            # delete temp file
            try:
                os.remove(item["package_path"])
            except EnvironmentError as e:  # File was already removed, no access rights, etc.
                Logger.error("Can't delete temporary package file: {err}".format(err=str(e)))

        if has_changes:
            self._restart_presenter.present()

    def _showErrorMessage(self, text: str):
        """Logs an error and shows it to the user"""

        Logger.error(text)
        Message(text, lifetime=0, message_type=Message.MessageType.ERROR).show()
