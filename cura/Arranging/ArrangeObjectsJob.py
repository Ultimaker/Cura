# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from PyQt5.QtCore import QCoreApplication

from UM.Application import Application
from UM.Job import Job
from UM.Math.Matrix import Matrix
from UM.Math.Quaternion import Quaternion
from UM.Operations.RotateOperation import RotateOperation
from UM.Scene.SceneNode import SceneNode
from UM.Math.Vector import Vector
from UM.Operations.TranslateOperation import TranslateOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Logger import Logger
from UM.Message import Message
from UM.i18n import i18nCatalog
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
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        machine_width = global_container_stack.getProperty("machine_width", "value")
        machine_depth = global_container_stack.getProperty("machine_depth", "value")

        factor = 10000

        build_plate_bounding_box = Box(machine_width * factor, machine_depth  * factor )

        node_items = []
        for node in self._nodes:
            hull_polygon = node.callDecoration("getConvexHull")
            converted_points = []
            for point in hull_polygon.getPoints():
                converted_points.append(Point(point[0] * factor, point[1] * factor))
            item = Item(converted_points)
            node_items.append(item)

        config = NfpConfig()
        config.accuracy = 1.0
        num_bins = nest(node_items, build_plate_bounding_box, 1, config)
        found_solution_for_all = num_bins == 1
        not_fit_count = 0
        grouped_operation = GroupedOperation()
        for node, node_item in zip(self._nodes, node_items):
            if node_item.binId() == 0:
                # We found a spot for it
                rotation_matrix = Matrix()
                rotation_matrix.setByRotationAxis(node_item.rotation(),Vector(0, -1, 0))

                grouped_operation.addOperation(RotateOperation(node, Quaternion.fromMatrix(rotation_matrix)))
                grouped_operation.addOperation(TranslateOperation(node, Vector(node_item.translation().x() / factor, 0, node_item.translation().y() / factor)))
            else:
                # We didn't find a spot
                grouped_operation.addOperation(TranslateOperation(node, Vector(200, 0, -not_fit_count * 20), set_position=True))
                not_fit_count += 1
        grouped_operation.push()

        status_message.hide()

        if not found_solution_for_all:
            no_full_solution_message = Message(i18n_catalog.i18nc("@info:status", "Unable to find a location within the build volume for all objects"),
                                               title = i18n_catalog.i18nc("@info:title", "Can't Find Location"))
            no_full_solution_message.show()

        self.finished.emit(self)
