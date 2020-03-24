import os
from collections import OrderedDict
from typing import Dict, Optional, List, Any

from PyQt5.QtCore import QObject, pyqtSlot

from UM.Logger import Logger
from UM.PackageManager import PackageManager
from UM.Signal import Signal
from cura.CuraApplication import CuraApplication
from UM.i18n import i18nCatalog

from .LicenseModel import LicenseModel


class LicensePresenter(QObject):
    """Presents licenses for a set of packages for the user to accept or reject.

    Call present() exactly once to show a licenseDialog for a set of packages
    Before presenting another set of licenses, create a new instance using resetCopy().

    licenseAnswers emits a list of Dicts containing answers when the user has made a choice for all provided packages.
    """

    def __init__(self, app: CuraApplication) -> None:
        super().__init__()
        self._presented = False
        """Whether present() has been called and state is expected to be initialized"""
        self._catalog = i18nCatalog("cura")
        self._dialog = None  # type: Optional[QObject]
        self._package_manager = app.getPackageManager()  # type: PackageManager
        # Emits List[Dict[str, [Any]] containing for example
        # [{ "package_id": "BarbarianPlugin", "package_path" : "/tmp/dg345as", "accepted" : True }]
        self.licenseAnswers = Signal()

        self._current_package_idx = 0
        self._package_models = []  # type: List[Dict]
        decline_button_text = self._catalog.i18nc("@button", "Decline and remove from account")
        self._license_model = LicenseModel(decline_button_text=decline_button_text)  # type: LicenseModel
        self._page_count = 0

        self._app = app

        self._compatibility_dialog_path = "resources/qml/dialogs/ToolboxLicenseDialog.qml"

    ## Show a license dialog for multiple packages where users can read a license and accept or decline them
    # \param plugin_path: Root directory of the Toolbox plugin
    # \param packages: Dict[package id, file path]
    def present(self, plugin_path: str, packages: Dict[str, Dict[str, str]]) -> None:
        if self._presented:
            Logger.error("{clazz} is single-use. Create a new {clazz} instead", clazz=self.__class__.__name__)
            return

        path = os.path.join(plugin_path, self._compatibility_dialog_path)

        self._initState(packages)

        if self._page_count == 0:
            self.licenseAnswers.emit(self._package_models)
            return

        if self._dialog is None:

            context_properties = {
                "catalog": self._catalog,
                "licenseModel": self._license_model,
                "handler": self
            }
            self._dialog = self._app.createQmlComponent(path, context_properties)
        self._presentCurrentPackage()
        self._presented = True

    def resetCopy(self) -> "LicensePresenter":
        """Clean up and return a new copy with the same settings such as app"""
        if self._dialog:
            self._dialog.close()
        self.licenseAnswers.disconnectAll()
        return LicensePresenter(self._app)

    @pyqtSlot()
    def onLicenseAccepted(self) -> None:
        self._package_models[self._current_package_idx]["accepted"] = True
        self._checkNextPage()

    @pyqtSlot()
    def onLicenseDeclined(self) -> None:
        self._package_models[self._current_package_idx]["accepted"] = False
        self._checkNextPage()

    def _initState(self, packages: Dict[str, Dict[str, Any]]) -> None:

        implicitly_accepted_count = 0

        for package_id, item in packages.items():
            item["package_id"] = package_id
            item["licence_content"] = self._package_manager.getPackageLicense(item["package_path"])
            if item["licence_content"] is None:
                # Implicitly accept when there is no license
                item["accepted"] = True
                implicitly_accepted_count = implicitly_accepted_count + 1
                self._package_models.append(item)
            else:
                item["accepted"] = None  #: None: no answer yet
                # When presenting the packages, we want to show packages which have a license first.
                # In fact, we don't want to show the others at all because they are implicitly accepted
                self._package_models.insert(0, item)
            CuraApplication.getInstance().processEvents()
        self._page_count = len(self._package_models) - implicitly_accepted_count
        self._license_model.setPageCount(self._page_count)


    def _presentCurrentPackage(self) -> None:
        package_model = self._package_models[self._current_package_idx]
        package_info = self._package_manager.getPackageInfo(package_model["package_path"])

        self._license_model.setCurrentPageIdx(self._current_package_idx)
        self._license_model.setPackageName(package_info["display_name"])
        self._license_model.setIconUrl(package_model["icon_url"])
        self._license_model.setLicenseText(package_model["licence_content"])
        if self._dialog:
            self._dialog.open()  # Does nothing if already open

    def _checkNextPage(self) -> None:
        if self._current_package_idx + 1 < self._page_count:
            self._current_package_idx += 1
            self._presentCurrentPackage()
        else:
            if self._dialog:
                self._dialog.close()
            self.licenseAnswers.emit(self._package_models)



