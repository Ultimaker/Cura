# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import List

from UM.Scene.Iterator import Iterator
from UM.Scene.SceneNode import SceneNode
from functools import cmp_to_key

from cura.HitChecker import HitChecker
from cura.PrintOrderManager import PrintOrderManager
from cura.Scene.CuraSceneNode import CuraSceneNode


class OneAtATimeIterator(Iterator.Iterator):
    """Iterator that returns a list of nodes in the order that they need to be printed

    If there is no solution an empty list is returned.
    Take note that the list of nodes can have children (that may or may not contain mesh data)
    """

    def __init__(self, scene_node) -> None:
        super().__init__(scene_node) # Call super to make multiple inheritance work.

    def _fillStack(self) -> None:
        """Fills the ``_node_stack`` with a list of scene nodes that need to be printed in order. """

        node_list = []
        for node in self._scene_node.getChildren():
            if not issubclass(type(node), SceneNode):
                continue

            # Node can't be printed, so don't bother sending it.
            if getattr(node, "_outside_buildarea", False):
                continue

            if node.callDecoration("getConvexHull"):
                node_list.append(node)

        if len(node_list) < 2:
            self._node_stack = node_list[:]
            return

        hit_checker = HitChecker(node_list)

        if PrintOrderManager.isUserDefinedPrintOrderEnabled():
            self._node_stack = self._getNodesOrderedByUser(hit_checker, node_list)
        else:
            self._node_stack = self._getNodesOrderedAutomatically(hit_checker, node_list)

            # update print orders so that user can try to arrange the nodes automatically first
            # and if result is not satisfactory he/she can switch to manual mode and change it
            for index, node in enumerate(self._node_stack):
                node.printOrder = index + 1

    @staticmethod
    def _getNodesOrderedByUser(hit_checker: HitChecker, node_list: List[CuraSceneNode]) -> List[CuraSceneNode]:
        nodes_ordered_by_user = sorted(node_list, key=lambda n: n.printOrder)
        if hit_checker.canPrintNodesInProvidedOrder(nodes_ordered_by_user):
            return nodes_ordered_by_user
        return []  # No solution

    @staticmethod
    def _getNodesOrderedAutomatically(hit_checker: HitChecker, node_list: List[CuraSceneNode]) -> List[CuraSceneNode]:
        # Check if we have two files that block each other. If this is the case, there is no solution!
        if hit_checker.anyTwoNodesBlockEachOther(node_list):
            return []  # No solution

        # Sort the original list so that items that block the most other objects are at the beginning.
        # This does not decrease the worst case running time, but should improve it in most cases.
        node_list = sorted(node_list, key = cmp_to_key(hit_checker.calculateScore))

        todo_node_list = [_ObjectOrder([], node_list)]
        while len(todo_node_list) > 0:
            current = todo_node_list.pop()
            for node in current.todo:
                # Check if the object can be placed with what we have and still allows for a solution in the future
                if hit_checker.canPrintAfter(node, current.order) and hit_checker.canPrintBefore(node, current.todo):
                    # We found a possible result. Create new todo & order list.
                    new_todo_list = current.todo[:]
                    new_todo_list.remove(node)
                    new_order = current.order[:] + [node]
                    if len(new_todo_list) == 0:
                        # We have no more nodes to check, so quit looking.
                        return new_order # Solution found!
                    todo_node_list.append(_ObjectOrder(new_order, new_todo_list))
        return []  # No result found!


class _ObjectOrder:
    """Internal object used to keep track of a possible order in which to print objects."""

    def __init__(self, order: List[SceneNode], todo: List[SceneNode]) -> None:
        """Creates the _ObjectOrder instance.

        :param order: List of indices in which to print objects, ordered by printing order.
        :param todo: List of indices which are not yet inserted into the order list.
        """
        self.order = order
        self.todo = todo
