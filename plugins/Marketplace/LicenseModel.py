from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal
from UM.i18n import i18nCatalog

catalog = i18nCatalog("cura")

# Model for the LicenseDialog
class LicenseModel(QObject):

    dialogTitleChanged = pyqtSignal()
    packageNameChanged = pyqtSignal()
    licenseTextChanged = pyqtSignal()

    def __init__(self, licence_text: str, package_name: str) -> None:
        super().__init__()
        self._license_text = ""
        self._package_name = ""

    @pyqtProperty(str, notify=packageNameChanged)
    def packageName(self) -> str:
        return self._package_name

    def setPackageName(self, name: str) -> None:
        self._package_name = name
        self.packageNameChanged.emit()

    @pyqtProperty(str, notify=licenseTextChanged)
    def licenseText(self) -> str:
        return self._license_text

    def setLicenseText(self, license_text: str) -> None:
        if self._license_text != license_text:
            self._license_text = license_text
            self.licenseTextChanged.emit()
