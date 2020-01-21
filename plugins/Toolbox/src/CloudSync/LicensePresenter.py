import os
from typing import Dict, Optional, List

from PyQt5.QtCore import QObject, pyqtSlot

from UM.PackageManager import PackageManager
from UM.Signal import Signal
from cura.CuraApplication import CuraApplication
from UM.i18n import i18nCatalog

from .LicenseModel import LicenseModel


## Call present() to show a licenseDialog for a set of packages
#  licenseAnswers emits a list of Dicts containing answers when the user has made a choice for all provided packages
class LicensePresenter(QObject):

    def __init__(self, app: CuraApplication) -> None:
        super().__init__()
        self._dialog = None  # type: Optional[QObject]
        self._package_manager = app.getPackageManager()  # type: PackageManager
        # Emits List[Dict[str, [Any]] containing for example
        # [{ "package_id": "BarbarianPlugin", "package_path" : "/tmp/dg345as", "accepted" : True }]
        self.licenseAnswers = Signal()

        self._current_package_idx = 0
        self._package_models = []  # type: List[Dict]
        self._license_model = LicenseModel()  # type: LicenseModel

        self._app = app

        self._compatibility_dialog_path = "resources/qml/dialogs/ToolboxLicenseDialog.qml"

    ## Show a license dialog for multiple packages where users can read a license and accept or decline them
    # \param plugin_path: Root directory of the Toolbox plugin
    # \param packages: Dict[package id, file path]
    def present(self, plugin_path: str, packages: Dict[str, Dict[str, str]]) -> None:
        path = os.path.join(plugin_path, self._compatibility_dialog_path)

        self._initState(packages)

        if self._dialog is None:

            context_properties = {
                "catalog": i18nCatalog("cura"),
                "licenseModel": self._license_model,
                "handler": self
            }
            self._dialog = self._app.createQmlComponent(path, context_properties)
        self._license_model.setPageCount(len(self._package_models))
        self._presentCurrentPackage()

    @pyqtSlot()
    def onLicenseAccepted(self) -> None:
        self._package_models[self._current_package_idx]["accepted"] = True
        self._checkNextPage()

    @pyqtSlot()
    def onLicenseDeclined(self) -> None:
        self._package_models[self._current_package_idx]["accepted"] = False
        self._checkNextPage()

    def _initState(self, packages: Dict[str, Dict[str, str]]) -> None:
        self._package_models = [
                {
                    "package_id" : package_id,
                    "package_path" : item["package_path"],
                    "icon_url" : item["icon_url"],
                    "accepted" : None  #: None: no answer yet
                }
                for package_id, item in packages.items()
        ]

    def _presentCurrentPackage(self) -> None:
        package_model = self._package_models[self._current_package_idx]
        license_content = self._package_manager.getPackageLicense(package_model["package_path"])
        if license_content is None:
            # Implicitly accept when there is no license
            self.onLicenseAccepted()
            return

        self._license_model.setCurrentPageIdx(self._current_package_idx)
        self._license_model.setPackageName(package_model["package_id"])
        self._license_model.setIconUrl(package_model["icon_url"])
        self._license_model.setLicenseText(license_content)
        if self._dialog:
            self._dialog.open()  # Does nothing if already open

    def _checkNextPage(self) -> None:
        if self._current_package_idx + 1 < len(self._package_models):
            self._current_package_idx += 1
            self._presentCurrentPackage()
        else:
            if self._dialog:
                self._dialog.close()
            self.licenseAnswers.emit(self._package_models)



