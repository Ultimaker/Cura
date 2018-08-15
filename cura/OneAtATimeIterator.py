# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import sys

from shapely import affinity
from shapely.geometry import Polygon

from UM.Scene.Iterator.Iterator import Iterator
from UM.Scene.SceneNode import SceneNode


# Iterator that determines the object print order when one-at a time mode is enabled.
#
# In one-at-a-time mode, only one extruder can be enabled to print. In order to maximize the number of objects we can
# print, we need to print from the corner that's closest to the extruder that's being used. Here is an illustration:
#
#  +--------------------------------+
#  |                                |
#  |                                |
#  |                                |          - Rectangle represents the complete print head including fans, etc.
#  |       X                X       |    y     - X's are the nozzles
#  |      (1)              (2)      |    ^
#  |                                |    |
#  +--------------------------------+    +--> x
#
# In this case, the nozzles are symmetric, nozzle (1) is closer to the bottom left corner while (2) is closer to the
# bottom right. If we use nozzle (1) to print, then we better off printing from the bottom left corner so the print
# head will not collide into an object on its top-right side, which is a very large unused area. Following the same
# logic, if we are printing with nozzle (2), then it's better to print from the bottom-right side.
#
# This iterator determines the print order following the rules above.
#
class OneAtATimeIterator(Iterator):

    def __init__(self, scene_node):
        from cura.CuraApplication import CuraApplication
        self._global_stack = CuraApplication.getInstance().getGlobalContainerStack()
        self._original_node_list = []

        super().__init__(scene_node)  # Call super to make multiple inheritance work.

    def getMachineNearestCornerToExtruder(self, global_stack):
        head_and_fans_coordinates = global_stack.getHeadAndFansCoordinates()

        used_extruder = None
        for extruder in global_stack.extruders.values():
            if extruder.isEnabled:
                used_extruder = extruder
                break

        extruder_offsets = [used_extruder.getProperty("machine_nozzle_offset_x", "value"),
                            used_extruder.getProperty("machine_nozzle_offset_y", "value")]

        # find the corner that's closest to the origin
        min_distance2 = sys.maxsize
        min_coord = None
        for coord in head_and_fans_coordinates:
            x = coord[0] - extruder_offsets[0]
            y = coord[1] - extruder_offsets[1]

            distance2 = x**2 + y**2
            if distance2 <= min_distance2:
                min_distance2 = distance2
                min_coord = coord

        return min_coord

    def _checkForCollisions(self) -> bool:
        all_nodes = []
        for node in self._scene_node.getChildren():
            if not issubclass(type(node), SceneNode):
                continue
            convex_hull = node.callDecoration("getConvexHullHead")
            if not convex_hull:
                continue

            bounding_box = node.getBoundingBox()
            if not bounding_box:
                continue
            from UM.Math.Polygon import Polygon
            bounding_box_polygon = Polygon([[bounding_box.left, bounding_box.front],
                                            [bounding_box.left, bounding_box.back],
                                            [bounding_box.right, bounding_box.back],
                                            [bounding_box.right, bounding_box.front]])

            all_nodes.append({"node": node,
                              "bounding_box": bounding_box_polygon,
                              "convex_hull": convex_hull})

        has_collisions = False
        for i, node_dict in enumerate(all_nodes):
            for j, other_node_dict in enumerate(all_nodes):
                if i == j:
                    continue
                if node_dict["bounding_box"].intersectsPolygon(other_node_dict["convex_hull"]):
                    has_collisions = True
                    break

            if has_collisions:
                break

        return has_collisions

    def _fillStack(self):
        min_coord = self.getMachineNearestCornerToExtruder(self._global_stack)
        transform_x = -int(round(min_coord[0] / abs(min_coord[0])))
        transform_y = -int(round(min_coord[1] / abs(min_coord[1])))

        machine_size = [self._global_stack.getProperty("machine_width", "value"),
                        self._global_stack.getProperty("machine_depth", "value")]

        def flip_x(polygon):
            tm2 = [-1, 0, 0, 1, 0, 0]
            return affinity.affine_transform(affinity.translate(polygon, xoff = -machine_size[0]), tm2)

        def flip_y(polygon):
            tm2 = [1, 0, 0, -1, 0, 0]
            return affinity.affine_transform(affinity.translate(polygon, yoff = -machine_size[1]), tm2)

        if self._checkForCollisions():
            self._node_stack = []
            return

        node_list = []
        for node in self._scene_node.getChildren():
            if not issubclass(type(node), SceneNode):
                continue

            convex_hull = node.callDecoration("getConvexHull")
            if convex_hull:
                xmin = min(x for x, _ in convex_hull._points)
                xmax = max(x for x, _ in convex_hull._points)
                ymin = min(y for _, y in convex_hull._points)
                ymax = max(y for _, y in convex_hull._points)

                convex_hull_polygon = Polygon.from_bounds(xmin, ymin, xmax, ymax)
                if transform_x < 0:
                    convex_hull_polygon = flip_x(convex_hull_polygon)
                if transform_y < 0:
                    convex_hull_polygon = flip_y(convex_hull_polygon)

                node_list.append({"node": node,
                                  "min_coord": [convex_hull_polygon.bounds[0], convex_hull_polygon.bounds[1]],
                                  })

        node_list = sorted(node_list, key = lambda d: d["min_coord"])

        self._node_stack = [d["node"] for d in node_list]
