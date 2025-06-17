#  Copyright (c) 2025 UltiMaker
#  Cura is released under the terms of the LGPLv3 or higher.

from typing import List

from PyQt6.QtCore import QObject, pyqtProperty

from cura import CuraVersion
from .OpenSourceDependency import OpenSourceDependency


class OpenSourceDependenciesModel(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dependencies = []

        for name, data in CuraVersion.DependenciesDescriptions.items():
            self._dependencies.append(OpenSourceDependency(name, data))

    @pyqtProperty(list, constant=True)
    def dependencies(self) -> List[OpenSourceDependency]:
        return self._dependencies