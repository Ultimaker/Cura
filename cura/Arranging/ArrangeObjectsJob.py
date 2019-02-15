# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Application import Application
from UM.Job import Job
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

        arranger = Arrange.create(x = machine_width, y = machine_depth, fixed_nodes = self._fixed_nodes, min_offset = self._min_offset)

        # Build set to exclude children (those get arranged together with the parents).
        included_as_child = set()
        for node in self._nodes:
            included_as_child.update(node.getAllChildren())

        # Collect nodes to be placed
        nodes_arr = []  # fill with (size, node, offset_shape_arr, hull_shape_arr)
        for node in self._nodes:
            if node in included_as_child:
                continue
            offset_shape_arr, hull_shape_arr = ShapeArray.fromNode(node, min_offset = self._min_offset, include_children = True)
            if offset_shape_arr is None:
                Logger.log("w", "Node [%s] could not be converted to an array for arranging...", str(node))
                continue
            nodes_arr.append((offset_shape_arr.arr.shape[0] * offset_shape_arr.arr.shape[1], node, offset_shape_arr, hull_shape_arr))

        # Sort the nodes with the biggest area first.
        nodes_arr.sort(key=lambda item: item[0])
        nodes_arr.reverse()

        # Place nodes one at a time
        start_priority = 0
        last_priority = start_priority
        last_size = None
        grouped_operation = GroupedOperation()
        found_solution_for_all = True
        not_fit_count = 0
        for idx, (size, node, offset_shape_arr, hull_shape_arr) in enumerate(nodes_arr):
            # For performance reasons, we assume that when a location does not fit,
            # it will also not fit for the next object (while what can be untrue).
            if last_size == size:  # This optimization works if many of the objects have the same size
                start_priority = last_priority
            else:
                start_priority = 0
            best_spot = arranger.bestSpot(hull_shape_arr, start_prio = start_priority)
            x, y = best_spot.x, best_spot.y
            node.removeDecorator(ZOffsetDecorator)
            if node.getBoundingBox():
                center_y = node.getWorldPosition().y - node.getBoundingBox().bottom
            else:
                center_y = 0
            if x is not None:  # We could find a place
                last_size = size
                last_priority = best_spot.priority

                arranger.place(x, y, offset_shape_arr)  # take place before the next one
                grouped_operation.addOperation(TranslateOperation(node, Vector(x, center_y, y), set_position = True))
            else:
                Logger.log("d", "Arrange all: could not find spot!")
                found_solution_for_all = False
                grouped_operation.addOperation(TranslateOperation(node, Vector(200, center_y, -not_fit_count * 20), set_position = True))
                not_fit_count += 1

            status_message.setProgress((idx + 1) / len(nodes_arr) * 100)
            Job.yieldThread()

        grouped_operation.push()

        status_message.hide()

        if not found_solution_for_all:
            no_full_solution_message = Message(i18n_catalog.i18nc("@info:status", "Unable to find a location within the build volume for all objects"),
                                               title = i18n_catalog.i18nc("@info:title", "Can't Find Location"))
            no_full_solution_message.show()

        self.finished.emit(self)
