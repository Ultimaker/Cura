# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

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
    def __init__(self, object_id, count, min_offset = 8):
        super().__init__()
        self._object_id = object_id
        self._count = count
        self._min_offset = min_offset

    def run(self):
        status_message = Message(i18n_catalog.i18nc("@info:status", "Multiplying and placing objects"), lifetime=0,
                                 dismissable=False, progress=0)
        status_message.show()
        scene = Application.getInstance().getController().getScene()
        node = scene.findObject(self._object_id)

        if not node and self._object_id != 0:  # Workaround for tool handles overlapping the selected object
            node = Selection.getSelectedObject(0)

        # If object is part of a group, multiply group
        current_node = node
        while current_node.getParent() and current_node.getParent().callDecoration("isGroup"):
            current_node = current_node.getParent()

        root = scene.getRoot()
        arranger = Arrange.create(scene_root=root)
        offset_shape_arr, hull_shape_arr = ShapeArray.fromNode(current_node, min_offset=self._min_offset)
        nodes = []
        found_solution_for_all = True
        for i in range(self._count):
            # We do place the nodes one by one, as we want to yield in between.
            node, solution_found = arranger.findNodePlacement(current_node, offset_shape_arr, hull_shape_arr)
            if not solution_found:
                found_solution_for_all = False
                new_location = node.getPosition()
                new_location = new_location.set(z = 100 - i * 20)
                node.setPosition(new_location)

            nodes.append(node)
            Job.yieldThread()
            status_message.setProgress((i + 1) / self._count * 100)

        if nodes:
            op = GroupedOperation()
            for new_node in nodes:
                op.addOperation(AddSceneNodeOperation(new_node, current_node.getParent()))
            op.push()
        status_message.hide()

        if not found_solution_for_all:
            no_full_solution_message = Message(i18n_catalog.i18nc("@info:status", "Unable to find a location within the build volume for all objects"))
            no_full_solution_message.show()