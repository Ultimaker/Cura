# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional
from PyQt5.QtCore.QObject import QObject
from UM.Qt.ListModel import ListModel
from PyQt5.QtCore import Qt


class IntentModel(ListModel):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self._update()

    def _update(self) -> None:
        pass