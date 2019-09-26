# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Scene.Iterator import Iterator
from UM.Scene.SceneNode import SceneNode
from functools import cmp_to_key
from UM.Application import Application

## Iterator that returns a list of nodes in the order that they need to be printed
#  If there is no solution an empty list is returned.
#  Take note that the list of nodes can have children (that may or may not contain mesh data)
class OneAtATimeIterator(Iterator.Iterator):
    def __init__(self, scene_node):
        super().__init__(scene_node) # Call super to make multiple inheritence work.
        self._hit_map = [[]]
        self._original_node_list = []

    def _fillStack(self):
        node_list = []
        for node in self._scene_node.getChildren():
            if not issubclass(type(node), SceneNode):
                continue

            if node.callDecoration("getConvexHull"):
                node_list.append(node)


        if len(node_list) < 2:
            self._node_stack = node_list[:]
            return

        # Copy the list
        self._original_node_list = node_list[:]

        ## Initialise the hit map (pre-compute all hits between all objects)
        self._hit_map = [[self._checkHit(i,j) for i in node_list] for j in node_list]

        # Check if we have to files that block eachother. If this is the case, there is no solution!
        for a in range(0,len(node_list)):
            for b in range(0,len(node_list)):
                if a != b and self._hit_map[a][b] and self._hit_map[b][a]:
                    return

        # Sort the original list so that items that block the most other objects are at the beginning.
        # This does not decrease the worst case running time, but should improve it in most cases.
        sorted(node_list, key = cmp_to_key(self._calculateScore))

        todo_node_list = [_ObjectOrder([], node_list)]
        while len(todo_node_list) > 0:
            current = todo_node_list.pop()
            for node in current.todo:
                # Check if the object can be placed with what we have and still allows for a solution in the future
                if not self._checkHitMultiple(node, current.order) and not self._checkBlockMultiple(node, current.todo):
                    # We found a possible result. Create new todo & order list.
                    new_todo_list = current.todo[:]
                    new_todo_list.remove(node)
                    new_order = current.order[:] + [node]
                    if len(new_todo_list) == 0:
                        # We have no more nodes to check, so quit looking.
                        todo_node_list = None
                        self._node_stack = new_order

                        return
                    todo_node_list.append(_ObjectOrder(new_order, new_todo_list))
        self._node_stack = [] #No result found!


    # Check if first object can be printed before the provided list (using the hit map)
    def _checkHitMultiple(self, node, other_nodes):
        node_index = self._original_node_list.index(node)
        for other_node in other_nodes:
            other_node_index = self._original_node_list.index(other_node)
            if self._hit_map[node_index][other_node_index]:
                return True
        return False

    def _checkBlockMultiple(self, node, other_nodes):
        node_index = self._original_node_list.index(node)
        for other_node in other_nodes:
            other_node_index = self._original_node_list.index(other_node)
            if self._hit_map[other_node_index][node_index] and node_index != other_node_index:
                return True
        return False

    ##  Calculate score simply sums the number of other objects it 'blocks'
    def _calculateScore(self, a, b):
        score_a = sum(self._hit_map[self._original_node_list.index(a)])
        score_b = sum(self._hit_map[self._original_node_list.index(b)])
        return score_a - score_b

    #   Checks if A can be printed before B
    def _checkHit(self, a, b):
        if a == b:
            return False

        overlap = a.callDecoration("getConvexHullBoundary").intersectsPolygon(b.callDecoration("getConvexHullHeadFull"))
        if overlap:
            return True
        else:
            return False


## Internal object used to keep track of a possible order in which to print objects.
class _ObjectOrder():
    def __init__(self, order, todo):
        """
        :param order:   List of indexes in which to print objects, ordered by printing order.
        :param todo:    List of indexes which are not yet inserted into the order list.
        """
        self.order = order
        self.todo = todo

