from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal


# Model for the ToolboxLicenseDialog
class LicenseModel(QObject):
    titleChanged = pyqtSignal()
    licenseTextChanged = pyqtSignal()

    def __init__(self, title: str = "", license_text: str = ""):
        super().__init__()
        self._title = title
        self._license_text = license_text

    @pyqtProperty(str, notify=titleChanged)
    def title(self) -> str:
        return self._title

    def setTitle(self, title: str) -> None:
        if self._title != title:
            self._title = title
            self.titleChanged.emit()

    @pyqtProperty(str, notify=licenseTextChanged)
    def licenseText(self) -> str:
        return self._license_text

    def setLicenseText(self, license_text: str) -> None:
        if self._license_text != license_text:
            self._license_text = license_text
            self.licenseTextChanged.emit()
