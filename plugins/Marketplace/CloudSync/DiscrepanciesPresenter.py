# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
from typing import Optional

from PyQt6.QtCore import QObject

from UM.Qt.QtApplication import QtApplication
from UM.Signal import Signal
from .SubscribedPackagesModel import SubscribedPackagesModel


class DiscrepanciesPresenter(QObject):
    """Shows a list of packages to be added or removed. The user can select which packages to (un)install. The user's

    choices are emitted on the `packageMutations` Signal.
    """

    def __init__(self, app: QtApplication) -> None:
        super().__init__()

        self.packageMutations = Signal()  # Emits SubscribedPackagesModel

        self._app = app
        self._package_manager = app.getPackageManager()
        self._dialog: Optional[QObject] = None
        self._compatibility_dialog_path = "resources/qml/CompatibilityDialog.qml"

    def present(self, plugin_path: str, model: SubscribedPackagesModel) -> None:
        path = os.path.join(plugin_path, self._compatibility_dialog_path)
        self._dialog = self._app.createQmlComponent(path, {"subscribedPackagesModel": model, "handler": self})
        assert self._dialog
        self._dialog.accepted.connect(lambda: self._onConfirmClicked(model))

    def _onConfirmClicked(self, model: SubscribedPackagesModel) -> None:
        # If there are incompatible packages - automatically dismiss them
        if model.getIncompatiblePackages():
            self._package_manager.dismissAllIncompatiblePackages(model.getIncompatiblePackages())
        # For now, all compatible packages presented to the user should be installed.
        # Later, we might remove items for which the user unselected the package
        if model.getCompatiblePackages():
            model.setItems(model.getCompatiblePackages())
            self.packageMutations.emit(model)
