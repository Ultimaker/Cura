from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal
from UM.i18n import i18nCatalog

catalog = i18nCatalog("cura")

# Model for the LicenseDialog
class LicenseModel(QObject):
    packageIdChanged = pyqtSignal()
    licenseTextChanged = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._license_text = ""
        self._package_id = ""

    @pyqtProperty(str, notify=packageIdChanged)
    def packageId(self) -> str:
        return self._package_id

    def setPackageId(self, name: str) -> None:
        self._package_id = name
        self.packageIdChanged.emit()

    @pyqtProperty(str, notify=licenseTextChanged)
    def licenseText(self) -> str:
        return self._license_text

    def setLicenseText(self, license_text: str) -> None:
        if self._license_text != license_text:
            self._license_text = license_text
            self.licenseTextChanged.emit()
