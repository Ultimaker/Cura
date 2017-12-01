# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Job import Job
from UM.Scene.SceneNode import SceneNode
from UM.Math.Vector import Vector
from UM.Operations.SetTransformOperation import SetTransformOperation
from UM.Operations.TranslateOperation import TranslateOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Logger import Logger
from UM.Message import Message
from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

from cura.ZOffsetDecorator import ZOffsetDecorator
from cura.Arrange import Arrange
from cura.ShapeArray import ShapeArray

from typing import List

from UM.Application import Application
from UM.Scene.Selection import Selection
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation


class MultiplyObjectsJob(Job):
    def __init__(self, objects, count, min_offset = 8):
        super().__init__()
        self._objects = objects
        self._count = count
        self._min_offset = min_offset

    def run(self):
        status_message = Message(i18n_catalog.i18nc("@info:status", "Multiplying and placing objects"), lifetime=0,
                                 dismissable=False, progress=0, title = i18n_catalog.i18nc("@info:title", "Placing Object"))
        status_message.show()
        scene = Application.getInstance().getController().getScene()

        total_progress = len(self._objects) * self._count
        current_progress = 0

        root = scene.getRoot()
        arranger = Arrange.create(scene_root=root)
        nodes = []
        for node in self._objects:
            # If object is part of a group, multiply group
            current_node = node
            while current_node.getParent() and current_node.getParent().callDecoration("isGroup"):
                current_node = current_node.getParent()

            node_too_big = False
            if node.getBoundingBox().width < 300 or node.getBoundingBox().depth < 300:
                offset_shape_arr, hull_shape_arr = ShapeArray.fromNode(current_node, min_offset=self._min_offset)
            else:
                node_too_big = True

            found_solution_for_all = True
            for i in range(self._count):
                # We do place the nodes one by one, as we want to yield in between.
                if not node_too_big:
                    node, solution_found = arranger.findNodePlacement(current_node, offset_shape_arr, hull_shape_arr)
                if node_too_big or not solution_found:
                    found_solution_for_all = False
                    new_location = node.getPosition()
                    new_location = new_location.set(z = 100 - i * 20)
                    node.setPosition(new_location)

                nodes.append(node)
                current_progress += 1
                status_message.setProgress((current_progress / total_progress) * 100)
                Job.yieldThread()

            Job.yieldThread()

        if nodes:
            op = GroupedOperation()
            for new_node in nodes:
                op.addOperation(AddSceneNodeOperation(new_node, current_node.getParent()))
            op.push()
        status_message.hide()

        if not found_solution_for_all:
            no_full_solution_message = Message(i18n_catalog.i18nc("@info:status", "Unable to find a location within the build volume for all objects"), title = i18n_catalog.i18nc("@info:title", "Placing Object"))
            no_full_solution_message.show()
