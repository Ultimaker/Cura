from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from UM.Application import Application

from UM.Math.Polygon import Polygon
from UM.Logger import Logger
from . import ConvexHullNode

import numpy

##  The convex hull decorator is a scene node decorator that adds the convex hull functionality to a scene node.
#   If a scene node has a convex hull decorator, it will have a shadow in which other objects can not be printed.
class ConvexHullDecorator(SceneNodeDecorator):
    def __init__(self,):
        super().__init__()

        self._convex_hull_node = None
        self._init2DConvexHullCache()

        self._profile = None
        Application.getInstance().getMachineManager().activeProfileChanged.connect(self._onActiveProfileChanged)
        Application.getInstance().getMachineManager().activeMachineInstanceChanged.connect(self._onActiveMachineInstanceChanged)
        self._onActiveProfileChanged()

    ## Force that a new (empty) object is created upon copy.
    def __deepcopy__(self, memo):
        return ConvexHullDecorator()

    ##  Get the unmodified 2D projected convex hull of the node
    def getConvexHull(self):
        hull = self._compute2DConvexHull()
        profile = Application.getInstance().getMachineManager().getWorkingProfile()
        if profile:
            if profile.getSettingValue("print_sequence") == "one_at_a_time" and not self._node.getParent().callDecoration("isGroup"):
                hull = hull.getMinkowskiHull(Polygon(numpy.array(profile.getSettingValue("machine_head_polygon"), numpy.float32)))
        return hull

    ##  Get the convex hull of the node with the full head size
    def getConvexHullHeadFull(self):
        return self._compute2DConvexHeadFull()

    ##  Get convex hull of the object + head size
    #   In case of printing all at once this is the same as the convex hull.
    #   For one at the time this is area with intersection of mirrored head
    def getConvexHullHead(self):
        profile = Application.getInstance().getMachineManager().getWorkingProfile()
        if profile:
            if profile.getSettingValue("print_sequence") == "one_at_a_time" and not self._node.getParent().callDecoration(
                    "isGroup"):
                return self._compute2DConvexHeadMin()
        return None

    ##  Get convex hull of the node
    #   In case of printing all at once this is the same as the convex hull.
    #   For one at the time this is the area without the head.
    def getConvexHullBoundary(self):
        profile = Application.getInstance().getMachineManager().getWorkingProfile()
        if profile:
            if profile.getSettingValue("print_sequence") == "one_at_a_time" and not self._node.getParent().callDecoration(
                    "isGroup"):
                # Printing one at a time and it's not an object in a group
                return self._compute2DConvexHull()
        return None

    def recomputeConvexHull(self):
        convex_hull = self.getConvexHull()
        if self._convex_hull_node:
            if self._convex_hull_node.getHull() == convex_hull:
                Logger.log('d', 'ConvexHullDecorator not creating a new ConvexHullNode')
                return
            self._convex_hull_node.setParent(None)
        Logger.log('d', 'ConvexHullDecorator creating ConvexHullNode')
        hull_node = ConvexHullNode.ConvexHullNode(self._node, convex_hull,
                                                  Application.getInstance().getController().getScene().getRoot())
        self._convex_hull_node = hull_node

    def _onActiveProfileChanged(self):
        if self._profile:
            self._profile.settingValueChanged.disconnect(self._onSettingValueChanged)

        self._profile = Application.getInstance().getMachineManager().getWorkingProfile()

        if self._profile:
            self._profile.settingValueChanged.connect(self._onSettingValueChanged)

    def _onActiveMachineInstanceChanged(self):
        if self._convex_hull_node:
            self._convex_hull_node.setParent(None)
            self._convex_hull_node = None

    def _onSettingValueChanged(self, setting):
        if setting == "print_sequence":
            self.recomputeConvexHull()

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
                # Logger.log('d', 'Cache hit in _compute2DConvexHull group path')
                return self._2d_convex_hull_group_result

            # First, calculate the normal convex hull around the points
            convex_hull = child_polygon.getConvexHull()

            # Then, do a Minkowski hull with a simple 1x1 quad to outset and round the normal convex hull.
            # This is done because of rounding errors.
            rounded_hull = self._roundHull(convex_hull)

            # Store the result in the cache
            self._2d_convex_hull_group_child_polygon = child_polygon
            self._2d_convex_hull_group_result = rounded_hull

            return rounded_hull

        else:
            if not self._node.getMeshData():
                return None
            mesh = self._node.getMeshData()
            world_transform = self._node.getWorldTransformation()

            # Check the cache
            if mesh is self._2d_convex_hull_mesh and world_transform == self._2d_convex_hull_mesh_world_transform:
                # Logger.log('d', 'Cache hit in _compute2DConvexHull mesh path')
                return self._2d_convex_hull_mesh_result

            vertex_data = mesh.getConvexHullTransformedVertices(world_transform)
            # Don't use data below 0.
            # TODO; We need a better check for this as this gives poor results for meshes with long edges.
            vertex_data = vertex_data[vertex_data[:,1] >= 0]

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

            # First, calculate the normal convex hull around the points
            convex_hull = hull.getConvexHull()

            # Then, do a Minkowski hull with a simple 1x1 quad to outset and round the normal convex hull.
            # This is done because of rounding errors.
            rounded_hull = convex_hull.getMinkowskiHull(Polygon(numpy.array([[-0.5, -0.5], [-0.5, 0.5], [0.5, 0.5], [0.5, -0.5]], numpy.float32)))

            # Store the result in the cache
            self._2d_convex_hull_mesh = mesh
            self._2d_convex_hull_mesh_world_transform = world_transform
            self._2d_convex_hull_mesh_result = rounded_hull

            return rounded_hull

    def _getHeadAndFans(self):
        profile = Application.getInstance().getMachineManager().getWorkingProfile()
        return Polygon(numpy.array(profile.getSettingValue("machine_head_with_fans_polygon"), numpy.float32))

    def _compute2DConvexHeadFull(self):
        return self._compute2DConvexHull().getMinkowskiHull(self._getHeadAndFans())

    def _compute2DConvexHeadMin(self):
        headAndFans = self._getHeadAndFans()
        mirrored = headAndFans.mirror([0, 0], [0, 1]).mirror([0, 0], [1, 0])  # Mirror horizontally & vertically.
        head_and_fans = self._getHeadAndFans().intersectionConvexHulls(mirrored)

        # Min head hull is used for the push free
        min_head_hull = self._compute2DConvexHull().getMinkowskiHull(head_and_fans)
        return min_head_hull

    def _roundHull(self, convex_hull):
        return convex_hull.getMinkowskiHull(Polygon(numpy.array([[-0.5, -0.5], [-0.5, 0.5], [0.5, 0.5], [0.5, -0.5]], numpy.float32)))
