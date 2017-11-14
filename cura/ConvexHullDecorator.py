# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Application import Application
from UM.Math.Polygon import Polygon
from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from UM.Settings.ContainerRegistry import ContainerRegistry

from cura.Settings.ExtruderManager import ExtruderManager
from . import ConvexHullNode

import numpy

##  The convex hull decorator is a scene node decorator that adds the convex hull functionality to a scene node.
#   If a scene node has a convex hull decorator, it will have a shadow in which other objects can not be printed.
class ConvexHullDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()

        self._convex_hull_node = None
        self._init2DConvexHullCache()

        self._global_stack = None

        self._raft_thickness = 0.0
        # For raft thickness, DRY
        self._build_volume = Application.getInstance().getBuildVolume()
        self._build_volume.raftThicknessChanged.connect(self._onChanged)

        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalStackChanged)
        Application.getInstance().getController().toolOperationStarted.connect(self._onChanged)
        Application.getInstance().getController().toolOperationStopped.connect(self._onChanged)

        self._onGlobalStackChanged()

    def setNode(self, node):
        previous_node = self._node
        # Disconnect from previous node signals
        if previous_node is not None and node is not previous_node:
            previous_node.transformationChanged.disconnect(self._onChanged)
            previous_node.parentChanged.disconnect(self._onChanged)

        super().setNode(node)

        self._node.transformationChanged.connect(self._onChanged)
        self._node.parentChanged.connect(self._onChanged)

        self._onChanged()

    ## Force that a new (empty) object is created upon copy.
    def __deepcopy__(self, memo):
        return ConvexHullDecorator()

    ##  Get the unmodified 2D projected convex hull of the node
    def getConvexHull(self):
        if self._node is None:
            return None

        hull = self._compute2DConvexHull()

        if self._global_stack and self._node:
            # Parent can be None if node is just loaded.
            if self._global_stack.getProperty("print_sequence", "value") == "one_at_a_time" and (self._node.getParent() is None or not self._node.getParent().callDecoration("isGroup")):
                hull = hull.getMinkowskiHull(Polygon(numpy.array(self._global_stack.getProperty("machine_head_polygon", "value"), numpy.float32)))
                hull = self._add2DAdhesionMargin(hull)
        return hull

    ##  Get the convex hull of the node with the full head size
    def getConvexHullHeadFull(self):
        if self._node is None:
            return None

        return self._compute2DConvexHeadFull()

    ##  Get convex hull of the object + head size
    #   In case of printing all at once this is the same as the convex hull.
    #   For one at the time this is area with intersection of mirrored head
    def getConvexHullHead(self):
        if self._node is None:
            return None

        if self._global_stack:
            if self._global_stack.getProperty("print_sequence", "value") == "one_at_a_time" and (self._node.getParent() is None or not self._node.getParent().callDecoration("isGroup")):
                head_with_fans = self._compute2DConvexHeadMin()
                head_with_fans_with_adhesion_margin = self._add2DAdhesionMargin(head_with_fans)
                return head_with_fans_with_adhesion_margin
        return None

    ##  Get convex hull of the node
    #   In case of printing all at once this is the same as the convex hull.
    #   For one at the time this is the area without the head.
    def getConvexHullBoundary(self):
        if self._node is None:
            return None

        if self._global_stack:
            if self._global_stack.getProperty("print_sequence", "value") == "one_at_a_time" and (self._node.getParent() is None or not self._node.getParent().callDecoration("isGroup")):
                # Printing one at a time and it's not an object in a group
                return self._compute2DConvexHull()
        return None

    def recomputeConvexHull(self):
        controller = Application.getInstance().getController()
        root = controller.getScene().getRoot()
        if self._node is None or controller.isToolOperationActive() or not self.__isDescendant(root, self._node):
            if self._convex_hull_node:
                self._convex_hull_node.setParent(None)
                self._convex_hull_node = None
            return

        convex_hull = self.getConvexHull()
        if self._convex_hull_node:
            self._convex_hull_node.setParent(None)
        hull_node = ConvexHullNode.ConvexHullNode(self._node, convex_hull, self._raft_thickness, root)
        self._convex_hull_node = hull_node

    def _onSettingValueChanged(self, key, property_name):
        if property_name != "value": #Not the value that was changed.
            return

        if key in self._affected_settings:
            self._onChanged()
        if key in self._influencing_settings:
            self._init2DConvexHullCache() #Invalidate the cache.
            self._onChanged()

    def _init2DConvexHullCache(self):
        # Cache for the group code path in _compute2DConvexHull()
        self._2d_convex_hull_group_child_polygon = None
        self._2d_convex_hull_group_result = None

        # Cache for the mesh code path in _compute2DConvexHull()
        self._2d_convex_hull_mesh = None
        self._2d_convex_hull_mesh_world_transform = None
        self._2d_convex_hull_mesh_result = None

    def _compute2DConvexHull(self):
        if self._node.callDecoration("isGroup"):
            points = numpy.zeros((0, 2), dtype=numpy.int32)
            for child in self._node.getChildren():
                child_hull = child.callDecoration("_compute2DConvexHull")
                if child_hull:
                    points = numpy.append(points, child_hull.getPoints(), axis = 0)

                if points.size < 3:
                    return None
            child_polygon = Polygon(points)

            # Check the cache
            if child_polygon == self._2d_convex_hull_group_child_polygon:
                return self._2d_convex_hull_group_result

            convex_hull = child_polygon.getConvexHull() #First calculate the normal convex hull around the points.
            offset_hull = self._offsetHull(convex_hull) #Then apply the offset from the settings.

            # Store the result in the cache
            self._2d_convex_hull_group_child_polygon = child_polygon
            self._2d_convex_hull_group_result = offset_hull

            return offset_hull

        else:
            offset_hull = None
            mesh = None
            world_transform = None
            if self._node.getMeshData():
                mesh = self._node.getMeshData()
                world_transform = self._node.getWorldTransformation()

                # Check the cache
                if mesh is self._2d_convex_hull_mesh and world_transform == self._2d_convex_hull_mesh_world_transform:
                    return self._2d_convex_hull_mesh_result

                vertex_data = mesh.getConvexHullTransformedVertices(world_transform)
                # Don't use data below 0.
                # TODO; We need a better check for this as this gives poor results for meshes with long edges.
                # Do not throw away vertices: the convex hull may be too small and objects can collide.
                # vertex_data = vertex_data[vertex_data[:,1] >= -0.01]

                if len(vertex_data) >= 4:
                    # Round the vertex data to 1/10th of a mm, then remove all duplicate vertices
                    # This is done to greatly speed up further convex hull calculations as the convex hull
                    # becomes much less complex when dealing with highly detailed models.
                    vertex_data = numpy.round(vertex_data, 1)

                    vertex_data = vertex_data[:, [0, 2]]  # Drop the Y components to project to 2D.

                    # Grab the set of unique points.
                    #
                    # This basically finds the unique rows in the array by treating them as opaque groups of bytes
                    # which are as long as the 2 float64s in each row, and giving this view to numpy.unique() to munch.
                    # See http://stackoverflow.com/questions/16970982/find-unique-rows-in-numpy-array
                    vertex_byte_view = numpy.ascontiguousarray(vertex_data).view(
                        numpy.dtype((numpy.void, vertex_data.dtype.itemsize * vertex_data.shape[1])))
                    _, idx = numpy.unique(vertex_byte_view, return_index=True)
                    vertex_data = vertex_data[idx]  # Select the unique rows by index.

                    hull = Polygon(vertex_data)

                    if len(vertex_data) >= 3:
                        convex_hull = hull.getConvexHull()
                        offset_hull = self._offsetHull(convex_hull)
            else:
                return Polygon([])  # Node has no mesh data, so just return an empty Polygon.

            # Store the result in the cache
            self._2d_convex_hull_mesh = mesh
            self._2d_convex_hull_mesh_world_transform = world_transform
            self._2d_convex_hull_mesh_result = offset_hull

            return offset_hull

    def _getHeadAndFans(self):
        return Polygon(numpy.array(self._global_stack.getProperty("machine_head_with_fans_polygon", "value"), numpy.float32))

    def _compute2DConvexHeadFull(self):
        return self._compute2DConvexHull().getMinkowskiHull(self._getHeadAndFans())

    def _compute2DConvexHeadMin(self):
        headAndFans = self._getHeadAndFans()
        mirrored = headAndFans.mirror([0, 0], [0, 1]).mirror([0, 0], [1, 0])  # Mirror horizontally & vertically.
        head_and_fans = self._getHeadAndFans().intersectionConvexHulls(mirrored)

        # Min head hull is used for the push free
        min_head_hull = self._compute2DConvexHull().getMinkowskiHull(head_and_fans)
        return min_head_hull

    ##  Compensate given 2D polygon with adhesion margin
    #   \return 2D polygon with added margin
    def _add2DAdhesionMargin(self, poly):
        # Compensate for raft/skirt/brim
        # Add extra margin depending on adhesion type
        adhesion_type = self._global_stack.getProperty("adhesion_type", "value")

        if adhesion_type == "raft":
            extra_margin = max(0, self._getSettingProperty("raft_margin", "value"))
        elif adhesion_type == "brim":
            extra_margin = max(0, self._getSettingProperty("brim_line_count", "value") * self._getSettingProperty("skirt_brim_line_width", "value"))
        elif adhesion_type == "none":
            extra_margin = 0
        elif adhesion_type == "skirt":
            extra_margin = max(
                0, self._getSettingProperty("skirt_gap", "value") +
                   self._getSettingProperty("skirt_line_count", "value") * self._getSettingProperty("skirt_brim_line_width", "value"))
        else:
            raise Exception("Unknown bed adhesion type. Did you forget to update the convex hull calculations for your new bed adhesion type?")

        # adjust head_and_fans with extra margin
        if extra_margin > 0:
            extra_margin_polygon = Polygon.approximatedCircle(extra_margin)
            poly = poly.getMinkowskiHull(extra_margin_polygon)
        return poly

    ##  Offset the convex hull with settings that influence the collision area.
    #
    #   \param convex_hull Polygon of the original convex hull.
    #   \return New Polygon instance that is offset with everything that
    #   influences the collision area.
    def _offsetHull(self, convex_hull):
        horizontal_expansion = max(
            self._getSettingProperty("xy_offset", "value"),
            self._getSettingProperty("xy_offset_layer_0", "value")
        )

        mold_width = 0
        if self._getSettingProperty("mold_enabled", "value"):
            mold_width = self._getSettingProperty("mold_width", "value")
        hull_offset = horizontal_expansion + mold_width
        if hull_offset > 0: #TODO: Implement Minkowski subtraction for if the offset < 0.
            expansion_polygon = Polygon(numpy.array([
                [-hull_offset, -hull_offset],
                [-hull_offset, hull_offset],
                [hull_offset, hull_offset],
                [hull_offset, -hull_offset]
            ], numpy.float32))
            return convex_hull.getMinkowskiHull(expansion_polygon)
        else:
            return convex_hull

    def _onChanged(self, *args):
        self._raft_thickness = self._build_volume.getRaftThickness()
        self.recomputeConvexHull()

    def _onGlobalStackChanged(self):
        if self._global_stack:
            self._global_stack.propertyChanged.disconnect(self._onSettingValueChanged)
            self._global_stack.containersChanged.disconnect(self._onChanged)
            extruders = ExtruderManager.getInstance().getMachineExtruders(self._global_stack.getId())
            for extruder in extruders:
                extruder.propertyChanged.disconnect(self._onSettingValueChanged)

        self._global_stack = Application.getInstance().getGlobalContainerStack()

        if self._global_stack:
            self._global_stack.propertyChanged.connect(self._onSettingValueChanged)
            self._global_stack.containersChanged.connect(self._onChanged)

            extruders = ExtruderManager.getInstance().getMachineExtruders(self._global_stack.getId())
            for extruder in extruders:
                extruder.propertyChanged.connect(self._onSettingValueChanged)

            self._onChanged()

    ##   Private convenience function to get a setting from the correct extruder (as defined by limit_to_extruder property).
    def _getSettingProperty(self, setting_key, property = "value"):
        per_mesh_stack = self._node.callDecoration("getStack")
        if per_mesh_stack:
            return per_mesh_stack.getProperty(setting_key, property)

        multi_extrusion = self._global_stack.getProperty("machine_extruder_count", "value") > 1
        if not multi_extrusion:
            return self._global_stack.getProperty(setting_key, property)

        extruder_index = self._global_stack.getProperty(setting_key, "limit_to_extruder")
        if extruder_index == "-1": #No limit_to_extruder.
            extruder_stack_id = self._node.callDecoration("getActiveExtruder")
            if not extruder_stack_id: #Decoration doesn't exist.
                extruder_stack_id = ExtruderManager.getInstance().extruderIds["0"]
            extruder_stack = ContainerRegistry.getInstance().findContainerStacks(id = extruder_stack_id)[0]
            return extruder_stack.getProperty(setting_key, property)
        else: #Limit_to_extruder is set. The global stack handles this then.
            return self._global_stack.getProperty(setting_key, property)

    ## Returns true if node is a descendant or the same as the root node.
    def __isDescendant(self, root, node):
        if node is None:
            return False
        if root is node:
            return True
        return self.__isDescendant(root, node.getParent())

    _affected_settings = [
        "adhesion_type", "raft_margin", "print_sequence",
        "skirt_gap", "skirt_line_count", "skirt_brim_line_width", "skirt_distance", "brim_line_count"]

    ##  Settings that change the convex hull.
    #
    #   If these settings change, the convex hull should be recalculated.
    _influencing_settings = {"xy_offset", "xy_offset_layer_0", "mold_enabled", "mold_width"}
