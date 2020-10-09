# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import copy
from typing import List

from UM.Job import Job
from UM.Math.Matrix import Matrix
from UM.Math.Quaternion import Quaternion
from UM.Math.Vector import Vector
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Message import Message
from UM.Operations.RotateOperation import RotateOperation
from UM.Operations.TranslateOperation import TranslateOperation
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.i18n import i18nCatalog
from cura.Arranging.Nest2DArrange import findNodePlacement

i18n_catalog = i18nCatalog("cura")

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

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack is None:
            return  # We can't do anything in this case.

        root = scene.getRoot()

        processed_nodes = []  # type: List[SceneNode]
        nodes = []

        fixed_nodes = []
        for node_ in DepthFirstIterator(root):
            # Only count sliceable objects
            if node_.callDecoration("isSliceable"):
                fixed_nodes.append(node_)

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

            for _ in range(self._count):
                new_node = copy.deepcopy(node)

                # Same build plate
                build_plate_number = current_node.callDecoration("getBuildPlateNumber")
                new_node.callDecoration("setBuildPlateNumber", build_plate_number)
                for child in new_node.getChildren():
                    child.callDecoration("setBuildPlateNumber", build_plate_number)

                nodes.append(new_node)
        factor = 10000
        found_solution_for_all, node_items = findNodePlacement(nodes, Application.getInstance().getBuildVolume(), fixed_nodes, factor = factor)
        not_fit_count = 0
        if nodes:
            operation = GroupedOperation()
            for new_node, node_item in zip(nodes, node_items):
                operation.addOperation(AddSceneNodeOperation(new_node, root))

                if node_item.binId() == 0:
                    # We found a spot for it
                    rotation_matrix = Matrix()
                    rotation_matrix.setByRotationAxis(node_item.rotation(), Vector(0, -1, 0))
                    operation.addOperation(RotateOperation(new_node, Quaternion.fromMatrix(rotation_matrix)))
                    operation.addOperation(
                        TranslateOperation(new_node, Vector(node_item.translation().x() / factor, 0,
                                                            node_item.translation().y() / factor)))
                else:
                    # We didn't find a spot
                    operation.addOperation(TranslateOperation(new_node, Vector(200, new_node.getWorldPosition().y, -not_fit_count * 20), set_position = True))
                    not_fit_count += 1

            operation.push()
        status_message.hide()

        if not found_solution_for_all:
            no_full_solution_message = Message(i18n_catalog.i18nc("@info:status", "Unable to find a location within the build volume for all objects"), title = i18n_catalog.i18nc("@info:title", "Placing Object"))
            no_full_solution_message.show()
