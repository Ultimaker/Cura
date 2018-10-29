# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM.Application import Application
from cura.Stages.CuraStage import CuraStage


class PreviewStage(CuraStage):
    def __init__(self, parent = None) -> None:
        super().__init__(parent)
        Application.getInstance().engineCreatedSignal.connect(self._engineCreated)

    def _engineCreated(self):
        return