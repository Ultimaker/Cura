import os
from typing import Optional

from PyQt5.QtCore import QObject

from UM.Qt.QtApplication import QtApplication
from UM.Signal import Signal
from plugins.Toolbox.src.CloudSync.SubscribedPackagesModel import SubscribedPackagesModel


## Shows a list of packages to be added or removed. The user can select which packages to (un)install. The user's
#  choices are emitted on the `packageMutations` Signal.
class DiscrepanciesPresenter(QObject):

    def __init__(self, app: QtApplication):
        super().__init__(app)

        self.packageMutations = Signal()  # {"SettingsGuide" : "install", "PrinterSettings" : "uninstall"}

        self._app = app
        self._dialog = None  # type: Optional[QObject]
        self._compatibility_dialog_path = "resources/qml/dialogs/CompatibilityDialog.qml"

    def present(self, plugin_path: str, model: SubscribedPackagesModel):
        path = os.path.join(plugin_path, self._compatibility_dialog_path)
        self._dialog = self._app.createQmlComponent(path, {"subscribedPackagesModel": model})
        self._dialog.accepted.connect(lambda: self._onConfirmClicked(model))

    def _onConfirmClicked(self, model: SubscribedPackagesModel):
        # For now, all packages presented to the user should be installed.
        # Later, we will support uninstall ?or ignoring? of a certain package
        choices = {item["package_id"]: "install" for item in model.items}
        self.packageMutations.emit(choices)
