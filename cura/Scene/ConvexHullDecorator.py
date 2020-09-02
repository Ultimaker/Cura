# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QTimer

from UM.Application import Application
from UM.Math.Polygon import Polygon

from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from UM.Settings.ContainerRegistry import ContainerRegistry

from cura.Settings.ExtruderManager import ExtruderManager
from cura.Scene import ConvexHullNode

import numpy

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from UM.Scene.SceneNode import SceneNode
    from cura.Settings.GlobalStack import GlobalStack
    from UM.Mesh.MeshData import MeshData
    from UM.Math.Matrix import Matrix


class ConvexHullDecorator(SceneNodeDecorator):
    """The convex hull decorator is a scene node decorator that adds the convex hull functionality to a scene node.

    If a scene node has a convex hull decorator, it will have a shadow in which other objects can not be printed.
    """

    def __init__(self) -> None:
        super().__init__()

        self._convex_hull_node = None  # type: Optional["SceneNode"]
        self._init2DConvexHullCache()

        self._global_stack = None  # type: Optional[GlobalStack]

        # Make sure the timer is created on the main thread
        self._recompute_convex_hull_timer = None  # type: Optional[QTimer]
        self._timer_scheduled_to_be_created = False
        from cura.CuraApplication import CuraApplication
        if CuraApplication.getInstance() is not None:
            self._timer_scheduled_to_be_created = True
            CuraApplication.getInstance().callLater(self.createRecomputeConvexHullTimer)

        self._raft_thickness = 0.0
        self._build_volume = CuraApplication.getInstance().getBuildVolume()
        self._build_volume.raftThicknessChanged.connect(self._onChanged)

        CuraApplication.getInstance().globalContainerStackChanged.connect(self._onGlobalStackChanged)
        controller = CuraApplication.getInstance().getController()
        controller.toolOperationStarted.connect(self._onChanged)
        controller.toolOperationStopped.connect(self._onChanged)
        #CuraApplication.getInstance().sceneBoundingBoxChanged.connect(self._onChanged)

        self._root = Application.getInstance().getController().getScene().getRoot()

        self._onGlobalStackChanged()

    def createRecomputeConvexHullTimer(self) -> None:
        self._recompute_convex_hull_timer = QTimer()
        self._recompute_convex_hull_timer.setInterval(200)
        self._recompute_convex_hull_timer.setSingleShot(True)
        self._recompute_convex_hull_timer.timeout.connect(self.recomputeConvexHull)

    def setNode(self, node: "SceneNode") -> None:
        previous_node = self._node
        # Disconnect from previous node signals
        if previous_node is not None and node is not previous_node:
            previous_node.boundingBoxChanged.disconnect(self._onChanged)

        super().setNode(node)

        node.boundingBoxChanged.connect(self._onChanged)

        per_object_stack = node.callDecoration("getStack")
        if per_object_stack:
            per_object_stack.propertyChanged.connect(self._onSettingValueChanged)

        self._onChanged()

    def __deepcopy__(self, memo):
        """Force that a new (empty) object is created upon copy."""

        return ConvexHullDecorator()

    def getAdhesionArea(self) -> Optional[Polygon]:
        """The polygon representing the 2D adhesion area.

        If no adhesion is used, the regular convex hull is returned
        """
        if self._node is None:
            return None

        hull = self._compute2DConvexHull()
        if hull is None:
            return None

        return self._add2DAdhesionMargin(hull)

    def getConvexHull(self) -> Optional[Polygon]:
        """Get the unmodified 2D projected convex hull of the node (if any)

        In case of one-at-a-time, this includes adhesion and head+fans clearance
        """
        if self._node is None:
            return None
        if self._node.callDecoration("isNonPrintingMesh"):
            return None

        # Parent can be None if node is just loaded.
        if self._isSingularOneAtATimeNode():
            hull = self.getConvexHullHeadFull()
            if hull is None:
                return None
            hull = self._add2DAdhesionMargin(hull)
            return hull

        return self._compute2DConvexHull()

    def getConvexHullHeadFull(self) -> Optional[Polygon]:
        """For one at the time this is the convex hull of the node with the full head size

        In case of printing all at once this is None.
        """
        if self._node is None:
            return None

        if self._isSingularOneAtATimeNode():
            return self._compute2DConvexHeadFull()

        return None

    @staticmethod
    def hasGroupAsParent(node: "SceneNode") -> bool:
        parent = node.getParent()
        if parent is None:
            return False
        return bool(parent.callDecoration("isGroup"))

    def getConvexHullHead(self) -> Optional[Polygon]:
        """Get convex hull of the object + head size

        In case of printing all at once this is None.
        For one at the time this is area with intersection of mirrored head
        """
        if self._node is None:
            return None
        if self._node.callDecoration("isNonPrintingMesh"):
            return None
        if self._isSingularOneAtATimeNode():
            head_with_fans = self._compute2DConvexHeadMin()
            if head_with_fans is None:
                return None
            head_with_fans_with_adhesion_margin = self._add2DAdhesionMargin(head_with_fans)
            return head_with_fans_with_adhesion_margin
        return None

    def getConvexHullBoundary(self) -> Optional[Polygon]:
        """Get convex hull of the node

        In case of printing all at once this None??
        For one at the time this is the area without the head.
        """
        if self._node is None:
            return None

        if self._node.callDecoration("isNonPrintingMesh"):
            return None

        if self._isSingularOneAtATimeNode():
            # Printing one at a time and it's not an object in a group
            return self._compute2DConvexHull()
        return None

    def getPrintingArea(self) -> Optional[Polygon]:
        """Get the buildplate polygon where will be printed

        In case of printing all at once this is the same as convex hull (no individual adhesion)
        For one at the time this includes the adhesion area
        """
        if self._isSingularOneAtATimeNode():
            # In one-at-a-time mode, every printed object gets it's own adhesion
            printing_area = self.getAdhesionArea()
        else:
            printing_area = self.getConvexHull()
        return printing_area

    def recomputeConvexHullDelayed(self) -> None:
        """The same as recomputeConvexHull, but using a timer if it was set."""
        if self._recompute_convex_hull_timer is not None:
            self._recompute_convex_hull_timer.start()
        else:
            from cura.CuraApplication import CuraApplication
            if not self._timer_scheduled_to_be_created:
                # The timer is not created and we never scheduled it. Time to create it now!
                CuraApplication.getInstance().callLater(self.createRecomputeConvexHullTimer)
            # Now we know for sure that the timer has been scheduled for creation, so we can try this again.
            CuraApplication.getInstance().callLater(self.recomputeConvexHullDelayed)

    def recomputeConvexHull(self) -> None:
        if self._node is None or not self.__isDescendant(self._root, self._node):
            if self._convex_hull_node:
                # Convex hull node still exists, but the node is removed or no longer in the scene.
                self._convex_hull_node.setParent(None)
                self._convex_hull_node = None
            return

        if self._convex_hull_node:
            self._convex_hull_node.setParent(None)
        hull_node = ConvexHullNode.ConvexHullNode(self._node, self.getPrintingArea(), self._raft_thickness, self._root)
        self._convex_hull_node = hull_node

    def _onSettingValueChanged(self, key: str, property_name: str) -> None:
        if property_name != "value":  # Not the value that was changed.
            return

        if key in self._affected_settings:
            self._onChanged()
        if key in self._influencing_settings:
            self._init2DConvexHullCache()  # Invalidate the cache.
            self._onChanged()

    def _init2DConvexHullCache(self) -> None:
        # Cache for the group code path in _compute2DConvexHull()
        self._2d_convex_hull_group_child_polygon = None  # type: Optional[Polygon]
        self._2d_convex_hull_group_result = None  # type: Optional[Polygon]

        # Cache for the mesh code path in _compute2DConvexHull()
        self._2d_convex_hull_mesh = None  # type: Optional[MeshData]
        self._2d_convex_hull_mesh_world_transform = None  # type: Optional[Matrix]
        self._2d_convex_hull_mesh_result = None  # type: Optional[Polygon]

    def _compute2DConvexHull(self) -> Optional[Polygon]:
        if self._node is None:
            return None
        if self._node.callDecoration("isGroup"):
            points = numpy.zeros((0, 2), dtype = numpy.int32)
            for child in self._node.getChildren():
                child_hull = child.callDecoration("_compute2DConvexHull")
                if child_hull:
                    try:
                        points = numpy.append(points, child_hull.getPoints(), axis = 0)
                    except ValueError:
                        pass

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
            convex_hull = Polygon([])
            offset_hull = Polygon([])
            mesh = self._node.getMeshData()
            if mesh is None:
                return Polygon([])  # Node has no mesh data, so just return an empty Polygon.

            world_transform = self._node.getWorldTransformation(copy = False)

            # Check the cache
            if mesh is self._2d_convex_hull_mesh and world_transform == self._2d_convex_hull_mesh_world_transform:
                return self._offsetHull(self._2d_convex_hull_mesh_result)

            vertex_data = mesh.getConvexHullTransformedVertices(world_transform)
            # Don't use data below 0.
            # TODO; We need a better check for this as this gives poor results for meshes with long edges.
            # Do not throw away vertices: the convex hull may be too small and objects can collide.
            # vertex_data = vertex_data[vertex_data[:,1] >= -0.01]

            if vertex_data is not None and len(vertex_data) >= 4:  # type: ignore # mypy and numpy don't play along well just yet.
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
                _, idx = numpy.unique(vertex_byte_view, return_index = True)
                vertex_data = vertex_data[idx]  # Select the unique rows by index.

                hull = Polygon(vertex_data)

                if len(vertex_data) >= 3:
                    convex_hull = hull.getConvexHull()
                    offset_hull = self._offsetHull(convex_hull)

            # Store the result in the cache
            self._2d_convex_hull_mesh = mesh
            self._2d_convex_hull_mesh_world_transform = world_transform
            self._2d_convex_hull_mesh_result = convex_hull

            return offset_hull

    def _getHeadAndFans(self) -> Polygon:
        if not self._global_stack:
            return Polygon()

        polygon = Polygon(numpy.array(self._global_stack.getHeadAndFansCoordinates(), numpy.float32))
        offset_x = self._getSettingProperty("machine_nozzle_offset_x", "value")
        offset_y = self._getSettingProperty("machine_nozzle_offset_y", "value")
        return polygon.translate(-offset_x, -offset_y)

    def _compute2DConvexHeadFull(self) -> Optional[Polygon]:
        convex_hull = self._compute2DConvexHull()
        if convex_hull:
            return convex_hull.getMinkowskiHull(self._getHeadAndFans())
        return None

    def _compute2DConvexHeadMin(self) -> Optional[Polygon]:
        head_and_fans = self._getHeadAndFans()
        mirrored = head_and_fans.mirror([0, 0], [0, 1]).mirror([0, 0], [1, 0])  # Mirror horizontally & vertically.
        head_and_fans = self._getHeadAndFans().intersectionConvexHulls(mirrored)

        # Min head hull is used for the push free
        convex_hull = self._compute2DConvexHull()
        if convex_hull:
            return convex_hull.getMinkowskiHull(head_and_fans)
        return None

    def _add2DAdhesionMargin(self, poly: Polygon) -> Polygon:
        """Compensate given 2D polygon with adhesion margin

        :return: 2D polygon with added margin
        """
        if not self._global_stack:
            return Polygon()
        # Compensate for raft/skirt/brim
        # Add extra margin depending on adhesion type
        adhesion_type = self._global_stack.getProperty("adhesion_type", "value")

        max_length_available = 0.5 * min(
            self._getSettingProperty("machine_width", "value"),
            self._getSettingProperty("machine_depth", "value")
        )

        if adhesion_type == "raft":
            extra_margin = min(max_length_available, max(0, self._getSettingProperty("raft_margin", "value")))
        elif adhesion_type == "brim":
            extra_margin = min(max_length_available, max(0, self._getSettingProperty("brim_line_count", "value") * self._getSettingProperty("skirt_brim_line_width", "value")))
        elif adhesion_type == "none":
            extra_margin = 0
        elif adhesion_type == "skirt":
            extra_margin = min(max_length_available, max(
                0, self._getSettingProperty("skirt_gap", "value") +
                   self._getSettingProperty("skirt_line_count", "value") * self._getSettingProperty("skirt_brim_line_width", "value")))
        else:
            raise Exception("Unknown bed adhesion type. Did you forget to update the convex hull calculations for your new bed adhesion type?")

        # Adjust head_and_fans with extra margin
        if extra_margin > 0:
            extra_margin_polygon = Polygon.approximatedCircle(extra_margin)
            poly = poly.getMinkowskiHull(extra_margin_polygon)
        return poly

    def _offsetHull(self, convex_hull: Polygon) -> Polygon:
        """Offset the convex hull with settings that influence the collision area.

        :param convex_hull: Polygon of the original convex hull.
        :return: New Polygon instance that is offset with everything that
        influences the collision area.
        """

        scale_factor = self._global_stack.getProperty("material_shrinkage_percentage", "value") / 100.0
        result = convex_hull
        if scale_factor != 1.0:
            center = None
            if self._global_stack.getProperty("print_sequence", "value") == "one_at_a_time":
                # Find the root node that's placed in the scene; the root of the mesh group.
                ancestor = self.getNode()
                while ancestor.getParent() != self._root:
                    ancestor = ancestor.getParent()
                center = ancestor.getBoundingBox().center
            else:
                # Find the bounding box of the entire scene, which is all one mesh group then.
                aabb = None
                for printed_node in self._root.getChildren():
                    if not printed_node.callDecoration("isSliceable"):
                        continue  # Not a printed node.
                    if aabb is None:
                        aabb = printed_node.getBoundingBox()
                    else:
                        aabb = aabb + printed_node.getBoundingBox()
                if aabb:
                    center = aabb.center
            if center:
                result = convex_hull.scale(scale_factor, [center.x, center.z])  # Yes, use Z instead of Y. Mixed conventions there with how the OpenGL coordinates are transmitted.

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
            return result.getMinkowskiHull(expansion_polygon)
        else:
            return result

    def _onChanged(self, *args) -> None:
        self._raft_thickness = self._build_volume.getRaftThickness()
        self.recomputeConvexHullDelayed()

    def _onGlobalStackChanged(self) -> None:
        if self._global_stack:
            self._global_stack.propertyChanged.disconnect(self._onSettingValueChanged)
            self._global_stack.containersChanged.disconnect(self._onChanged)
            extruders = ExtruderManager.getInstance().getActiveExtruderStacks()
            for extruder in extruders:
                extruder.propertyChanged.disconnect(self._onSettingValueChanged)

        self._global_stack = Application.getInstance().getGlobalContainerStack()

        if self._global_stack:
            self._global_stack.propertyChanged.connect(self._onSettingValueChanged)
            self._global_stack.containersChanged.connect(self._onChanged)

            extruders = ExtruderManager.getInstance().getActiveExtruderStacks()
            for extruder in extruders:
                extruder.propertyChanged.connect(self._onSettingValueChanged)

            self._onChanged()

    def _getSettingProperty(self, setting_key: str, prop: str = "value") -> Any:
        """Private convenience function to get a setting from the correct extruder (as defined by limit_to_extruder property)."""

        if self._global_stack is None or self._node is None:
            return None
        per_mesh_stack = self._node.callDecoration("getStack")
        if per_mesh_stack:
            return per_mesh_stack.getProperty(setting_key, prop)

        extruder_index = self._global_stack.getProperty(setting_key, "limit_to_extruder")
        if extruder_index == "-1":
            # No limit_to_extruder
            extruder_stack_id = self._node.callDecoration("getActiveExtruder")
            if not extruder_stack_id:
                # Decoration doesn't exist
                extruder_stack_id = ExtruderManager.getInstance().extruderIds["0"]
            extruder_stack = ContainerRegistry.getInstance().findContainerStacks(id = extruder_stack_id)[0]
            return extruder_stack.getProperty(setting_key, prop)
        else:
            # Limit_to_extruder is set. The global stack handles this then
            return self._global_stack.getProperty(setting_key, prop)

    def __isDescendant(self, root: "SceneNode", node: Optional["SceneNode"]) -> bool:
        """Returns True if node is a descendant or the same as the root node."""

        if node is None:
            return False
        if root is node:
            return True
        return self.__isDescendant(root, node.getParent())

    def _isSingularOneAtATimeNode(self) -> bool:
        """True if print_sequence is one_at_a_time and _node is not part of a group"""

        if self._node is None:
            return False
        return self._global_stack is not None \
            and self._global_stack.getProperty("print_sequence", "value") == "one_at_a_time" \
            and not self.hasGroupAsParent(self._node)

    _affected_settings = [
        "adhesion_type", "raft_margin", "print_sequence",
        "skirt_gap", "skirt_line_count", "skirt_brim_line_width", "skirt_distance", "brim_line_count"]

    _influencing_settings = {"xy_offset", "xy_offset_layer_0", "mold_enabled", "mold_width", "anti_overhang_mesh", "infill_mesh", "cutting_mesh", "material_shrinkage_percentage"}
    """Settings that change the convex hull.

    If these settings change, the convex hull should be recalculated.
    """
