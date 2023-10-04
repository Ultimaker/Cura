# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import copy
from typing import List

from UM.Application import Application
from UM.Job import Job
from UM.Math.Vector import Vector
from UM.Message import Message
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.TranslateOperation import TranslateOperation
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.i18n import i18nCatalog
from cura.Arranging.GridArrange import GridArrange
from cura.Arranging.Nest2DArrange import Nest2DArrange

i18n_catalog = i18nCatalog("cura")


class MultiplyObjectsJob(Job):
    def __init__(self, objects, count: int, min_offset: int = 8 ,* , grid_arrange: bool = False):
        super().__init__()
        self._objects = objects
        self._count: int = count
        self._min_offset: int = min_offset
        self._grid_arrange: bool = grid_arrange

    def run(self) -> None:
        status_message = Message(i18n_catalog.i18nc("@info:status", "Multiplying and placing objects"), lifetime = 0,
                                 dismissable = False, progress = 0,
                                 title = i18n_catalog.i18nc("@info:title", "Placing Objects"))
        status_message.show()
        scene = Application.getInstance().getController().getScene()

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack is None:
            return  # We can't do anything in this case.

        root = scene.getRoot()

        processed_nodes: List[SceneNode] = []
        nodes = []

        fixed_nodes = []
        for node_ in DepthFirstIterator(root):
            # Only count sliceable objects
            if node_.callDecoration("isSliceable"):
                fixed_nodes.append(node_)
        nodes_to_add_without_arrange = []
        for node in self._objects:
            # If object is part of a group, multiply group
            current_node = node
            while current_node.getParent() and current_node.getParent().callDecoration("isGroup"):
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
                if not current_node.getParent().callDecoration("isSliceable"):
                    nodes.append(new_node)
                else:
                    # The node we're trying to place has another node that is sliceable as a parent.
                    # As such, we shouldn't arrange it (but it should be added to the scene!)
                    nodes_to_add_without_arrange.append(new_node)
                    new_node.setParent(current_node.getParent())

        found_solution_for_all = True
        group_operation = GroupedOperation()
        if nodes:
            if self._grid_arrange:
                arranger = GridArrange(nodes, Application.getInstance().getBuildVolume(), fixed_nodes)
            else:
                arranger = Nest2DArrange(nodes, Application.getInstance().getBuildVolume(), fixed_nodes, factor=1000)

            group_operation, not_fit_count = arranger.createGroupOperationForArrange(add_new_nodes_in_scene=True)

        if nodes_to_add_without_arrange:
            for nested_node in nodes_to_add_without_arrange:
                group_operation.addOperation(AddSceneNodeOperation(nested_node, nested_node.getParent()))
                # Move the node a tiny bit so it doesn't overlap with the existing one.
                # This doesn't fix it if someone creates more than one duplicate, but it at least shows that something
                # happened (and after moving it, it's clear that there are more underneath)
                group_operation.addOperation(TranslateOperation(nested_node, Vector(2.5, 2.5, 2.5)))

        group_operation.push()
        status_message.hide()

        if not found_solution_for_all:
            no_full_solution_message = Message(
                i18n_catalog.i18nc("@info:status", "Unable to find a location within the build volume for all objects"),
                title = i18n_catalog.i18nc("@info:title", "Placing Object"),
                message_type = Message.MessageType.WARNING)
            no_full_solution_message.show()
