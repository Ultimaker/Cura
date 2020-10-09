# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import copy
from typing import List

from UM.Application import Application
from UM.Job import Job
from UM.Message import Message
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.i18n import i18nCatalog
from cura.Arranging.Nest2DArrange import arrange

i18n_catalog = i18nCatalog("cura")


class MultiplyObjectsJob(Job):
    def __init__(self, objects, count, min_offset = 8):
        super().__init__()
        self._objects = objects
        self._count = count
        self._min_offset = min_offset

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

        processed_nodes = []  # type: List[SceneNode]
        nodes = []

        fixed_nodes = []
        for node_ in DepthFirstIterator(root):
            # Only count sliceable objects
            if node_.callDecoration("isSliceable"):
                fixed_nodes.append(node_)

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

        found_solution_for_all = True
        if nodes:
            found_solution_for_all = arrange(nodes, Application.getInstance().getBuildVolume(), fixed_nodes,
                                             factor = 10000, add_new_nodes_in_scene = True)
        status_message.hide()

        if not found_solution_for_all:
            no_full_solution_message = Message(
                i18n_catalog.i18nc("@info:status", "Unable to find a location within the build volume for all objects"),
                title = i18n_catalog.i18nc("@info:title", "Placing Object"))
            no_full_solution_message.show()
