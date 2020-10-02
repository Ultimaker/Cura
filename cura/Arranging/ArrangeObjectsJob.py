# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import numpy
from PyQt5.QtCore import QCoreApplication

from UM.Application import Application
from UM.Job import Job
from UM.Math.Matrix import Matrix
from UM.Math.Polygon import Polygon
from UM.Math.Quaternion import Quaternion
from UM.Operations.RotateOperation import RotateOperation
from UM.Scene.SceneNode import SceneNode
from UM.Math.Vector import Vector
from UM.Operations.TranslateOperation import TranslateOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Logger import Logger
from UM.Message import Message
from UM.i18n import i18nCatalog
from cura.Arranging.Nest2DArrange import arrange

i18n_catalog = i18nCatalog("cura")

from cura.Scene.ZOffsetDecorator import ZOffsetDecorator
from cura.Arranging.Arrange import Arrange
from cura.Arranging.ShapeArray import ShapeArray

from typing import List
from pynest2d import *


class ArrangeObjectsJob(Job):
    def __init__(self, nodes: List[SceneNode], fixed_nodes: List[SceneNode], min_offset = 8) -> None:
        super().__init__()
        self._nodes = nodes
        self._fixed_nodes = fixed_nodes
        self._min_offset = min_offset

    def run(self):
        status_message = Message(i18n_catalog.i18nc("@info:status", "Finding new location for objects"),
                                 lifetime = 0,
                                 dismissable=False,
                                 progress = 0,
                                 title = i18n_catalog.i18nc("@info:title", "Finding Location"))
        status_message.show()

        found_solution_for_all = arrange(self._nodes, Application.getInstance().getBuildVolume())

        status_message.hide()
        if not found_solution_for_all:
            no_full_solution_message = Message(i18n_catalog.i18nc("@info:status", "Unable to find a location within the build volume for all objects"),
                                               title = i18n_catalog.i18nc("@info:title", "Can't Find Location"))
            no_full_solution_message.show()
        self.finished.emit(self)