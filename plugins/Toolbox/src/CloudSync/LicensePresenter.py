import os
from typing import Dict, Optional

from PyQt5.QtCore import QObject, pyqtSlot

from UM.PackageManager import PackageManager
from UM.Signal import Signal
from cura.CuraApplication import CuraApplication
from UM.i18n import i18nCatalog

from plugins.Toolbox.src.CloudSync.LicenseModel import LicenseModel


## Call present() to show a licenseDialog for a set of packages
#  licenseAnswers emits a list of Dicts containing answers when the user has made a choice for all provided packages
class LicensePresenter(QObject):

    def __init__(self, app: CuraApplication):
        super().__init__()
        self._dialog = None  # type: Optional[QObject]
        self._package_manager = app.getPackageManager()  # type: PackageManager
        # Emits List[Dict[str, str]] containing for example
        # [{ "package_id": "BarbarianPlugin", "package_path" : "/tmp/dg345as", "accepted" : True }]
        self.licenseAnswers = Signal()

        self._current_package_idx = 0
        self._package_models = None  # type: Optional[Dict]
        self._license_model = LicenseModel()  # type: LicenseModel

        self._app = app

        self._compatibility_dialog_path = "resources/qml/dialogs/ToolboxLicenseDialog.qml"

    ## Show a license dialog for multiple packages where users can read a license and accept or decline them
    # \param plugin_path: Root directory of the Toolbox plugin
    # \param packages: Dict[package id, file path]
    def present(self, plugin_path: str, packages: Dict[str, str]):
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
        self._present_current_package()

    @pyqtSlot()
    def onLicenseAccepted(self):
        self._package_models[self._current_package_idx]["accepted"] = True
        self._check_next_page()

    @pyqtSlot()
    def onLicenseDeclined(self):
        self._package_models[self._current_package_idx]["accepted"] = False
        self._check_next_page()

    def _initState(self, packages: Dict[str, str]):
        self._package_models = [
                {
                    "package_id" : package_id,
                    "package_path" : package_path,
                    "accepted" : None  #: None: no answer yet
                }
                for package_id, package_path in packages.items()
        ]

    def _present_current_package(self):
        package_model = self._package_models[self._current_package_idx]
        license_content = self._package_manager.getPackageLicense(package_model["package_path"])
        if license_content is None:
            # implicitly accept when there is no license
            self.onLicenseAccepted()
            return

        self._license_model.setCurrentPageIdx(self._current_package_idx)
        self._license_model.setPackageName(package_model["package_id"])
        self._license_model.setLicenseText(license_content)

        self._dialog.open()  # does nothing if already open

    def _check_next_page(self):
        if self._current_package_idx + 1 < len(self._package_models):
            self._current_package_idx += 1
            self._present_current_package()
        else:
            self._dialog.close()
            self.licenseAnswers.emit(self._package_models)



