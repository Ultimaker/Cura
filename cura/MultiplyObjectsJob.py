# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import copy
from typing import List

from PyQt5.QtCore import QCoreApplication

from UM.Job import Job
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Message import Message
from UM.Scene.SceneNode import SceneNode
from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

from cura.Arranging.Arrange import Arrange
from cura.Arranging.ShapeArray import ShapeArray

from UM.Application import Application
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation


class MultiplyObjectsJob(Job):
    def __init__(self, objects, count, min_offset = 8):
        super().__init__()
        self._objects = objects
        self._count = count
        self._min_offset = min_offset

    def run(self) -> None:
        status_message = Message(i18n_catalog.i18nc("@info:status", "Multiplying and placing objects"), lifetime=0,
                                 dismissable=False, progress=0, title = i18n_catalog.i18nc("@info:title", "Placing Objects"))
        status_message.show()
        scene = Application.getInstance().getController().getScene()

        total_progress = len(self._objects) * self._count
        current_progress = 0

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack is None:
            return  # We can't do anything in this case.
        machine_width = global_container_stack.getProperty("machine_width", "value")
        machine_depth = global_container_stack.getProperty("machine_depth", "value")

        root = scene.getRoot()
        scale = 0.5
        arranger = Arrange.create(x = machine_width, y = machine_depth, scene_root = root, scale = scale, min_offset = self._min_offset)
        processed_nodes = []  # type: List[SceneNode]
        nodes = []

        not_fit_count = 0
        found_solution_for_all = False
        for node in self._objects:
            # If object is part of a group, multiply group
            current_node = node
            while current_node.getParent() and (current_node.getParent().callDecoration("isGroup") or current_node.getParent().callDecoration("isSliceable")):
                current_node = current_node.getParent()

            if current_node in processed_nodes:
                continue
            processed_nodes.append(current_node)

            node_too_big = False
            if node.getBoundingBox().width < machine_width or node.getBoundingBox().depth < machine_depth:
                offset_shape_arr, hull_shape_arr = ShapeArray.fromNode(current_node, min_offset = self._min_offset, scale = scale)
            else:
                node_too_big = True

            found_solution_for_all = True
            arranger.resetLastPriority()
            for _ in range(self._count):
                # We do place the nodes one by one, as we want to yield in between.
                new_node = copy.deepcopy(node)
                solution_found = False
                if not node_too_big:
                    if offset_shape_arr is not None and hull_shape_arr is not None:
                        solution_found = arranger.findNodePlacement(new_node, offset_shape_arr, hull_shape_arr)
                    else:
                        # The node has no shape, so no need to arrange it. The solution is simple: Do nothing. 
                        solution_found = True

                if node_too_big or not solution_found:
                    found_solution_for_all = False
                    new_location = new_node.getPosition()
                    new_location = new_location.set(z = - not_fit_count * 20)
                    new_node.setPosition(new_location)
                    not_fit_count += 1

                # Same build plate
                build_plate_number = current_node.callDecoration("getBuildPlateNumber")
                new_node.callDecoration("setBuildPlateNumber", build_plate_number)
                for child in new_node.getChildren():
                    child.callDecoration("setBuildPlateNumber", build_plate_number)

                nodes.append(new_node)
                current_progress += 1
                status_message.setProgress((current_progress / total_progress) * 100)
                QCoreApplication.processEvents()
                Job.yieldThread()
            QCoreApplication.processEvents()
            Job.yieldThread()

        if nodes:
            operation = GroupedOperation()
            for new_node in nodes:
                operation.addOperation(AddSceneNodeOperation(new_node, current_node.getParent()))
            operation.push()
        status_message.hide()

        if not found_solution_for_all:
            no_full_solution_message = Message(i18n_catalog.i18nc("@info:status", "Unable to find a location within the build volume for all objects"), title = i18n_catalog.i18nc("@info:title", "Placing Object"))
            no_full_solution_message.show()
