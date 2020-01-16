from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal
from UM.i18n import i18nCatalog

catalog = i18nCatalog("cura")


# Model for the ToolboxLicenseDialog
class LicenseModel(QObject):
    dialogTitleChanged = pyqtSignal()
    headerChanged = pyqtSignal()
    licenseTextChanged = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        self._current_page_idx = 0
        self._page_count = 1
        self._dialogTitle = ""
        self._header_text = ""
        self._license_text = ""
        self._package_name = ""

    @pyqtProperty(str, notify=dialogTitleChanged)
    def dialogTitle(self) -> str:
        return self._dialogTitle

    @pyqtProperty(str, notify=headerChanged)
    def headerText(self) -> str:
        return self._header_text

    def setPackageName(self, name: str) -> None:
        self._header_text = name + ": " + catalog.i18nc("@label", "This plugin contains a license.\nYou need to accept this license to install this plugin.\nDo you agree with the terms below?")
        self.headerChanged.emit()

    @pyqtProperty(str, notify=licenseTextChanged)
    def licenseText(self) -> str:
        return self._license_text

    def setLicenseText(self, license_text: str) -> None:
        if self._license_text != license_text:
            self._license_text = license_text
            self.licenseTextChanged.emit()

    def setCurrentPageIdx(self, idx: int) -> None:
        self._current_page_idx = idx
        self._updateDialogTitle()

    def setPageCount(self, count: int) -> None:
        self._page_count = count
        self._updateDialogTitle()

    def _updateDialogTitle(self):
        self._dialogTitle = catalog.i18nc("@title:window", "Plugin License Agreement ({}/{})"
                                          .format(self._current_page_idx + 1, self._page_count))
        self.dialogTitleChanged.emit()
