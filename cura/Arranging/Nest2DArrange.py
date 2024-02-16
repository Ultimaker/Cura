# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import numpy
from pynest2d import Point, Box, Item, NfpConfig, nest
from typing import List, TYPE_CHECKING, Optional, Tuple

from UM.Application import Application
from UM.Decorators import deprecated
from UM.Logger import Logger
from UM.Math.Matrix import Matrix
from UM.Math.Polygon import Polygon
from UM.Math.Quaternion import Quaternion
from UM.Math.Vector import Vector
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.RotateOperation import RotateOperation
from UM.Operations.TranslateOperation import TranslateOperation
from cura.Arranging.Arranger import Arranger

if TYPE_CHECKING:
    from UM.Scene.SceneNode import SceneNode
    from cura.BuildVolume import BuildVolume


class Nest2DArrange(Arranger):
    def __init__(self,
                 nodes_to_arrange: List["SceneNode"],
                 build_volume: "BuildVolume",
                 fixed_nodes: Optional[List["SceneNode"]] = None,
                 *,
                 factor: int = 10000,
                 lock_rotation: bool = False):
        """
        :param nodes_to_arrange: The list of nodes that need to be moved.
        :param build_volume: The build volume that we want to place the nodes in. It gets size & disallowed areas from this.
        :param fixed_nodes: List of nods that should not be moved, but should be used when deciding where the others nodes
                            are placed.
        :param factor: The library that we use is int based. This factor defines how accuracte we want it to be.
        :param lock_rotation: If set to true the orientation of the object will remain the same
        """
        super().__init__()
        self._nodes_to_arrange = nodes_to_arrange
        self._build_volume = build_volume
        self._fixed_nodes = fixed_nodes
        self._factor = factor
        self._lock_rotation = lock_rotation

    def findNodePlacement(self) -> Tuple[bool, List[Item]]:
        spacing = int(1.5 * self._factor)  # 1.5mm spacing.

        edge_disallowed_size = self._build_volume.getEdgeDisallowedSize()
        machine_width = self._build_volume.getWidth() - (edge_disallowed_size * 2)
        machine_depth = self._build_volume.getDepth() - (edge_disallowed_size * 2)
        build_plate_bounding_box = Box(int(machine_width * self._factor), int(machine_depth * self._factor))

        if self._fixed_nodes is None:
            self._fixed_nodes = []

        # Add all the items we want to arrange
        node_items = []
        for node in self._nodes_to_arrange:
            hull_polygon = node.callDecoration("getConvexHull")
            if not hull_polygon or hull_polygon.getPoints is None:
                Logger.log("w", "Object {} cannot be arranged because it has no convex hull.".format(node.getName()))
                continue
            converted_points = []
            for point in hull_polygon.getPoints():
                converted_points.append(Point(int(point[0] * self._factor), int(point[1] * self._factor)))
            item = Item(converted_points)
            node_items.append(item)

        # Use a tiny margin for the build_plate_polygon (the nesting doesn't like overlapping disallowed areas)
        half_machine_width = 0.5 * machine_width - 1
        half_machine_depth = 0.5 * machine_depth - 1
        build_plate_polygon = Polygon(numpy.array([
            [half_machine_width, -half_machine_depth],
            [-half_machine_width, -half_machine_depth],
            [-half_machine_width, half_machine_depth],
            [half_machine_width, half_machine_depth]
        ], numpy.float32))

        disallowed_areas = self._build_volume.getDisallowedAreas()
        for area in disallowed_areas:
            converted_points = []

            # Clip the disallowed areas so that they don't overlap the bounding box (The arranger chokes otherwise)
            clipped_area = area.intersectionConvexHulls(build_plate_polygon)

            if clipped_area.getPoints() is not None and len(
                    clipped_area.getPoints()) > 2:  # numpy array has to be explicitly checked against None
                for point in clipped_area.getPoints():
                    converted_points.append(Point(int(point[0] * self._factor), int(point[1] * self._factor)))

                disallowed_area = Item(converted_points)
                disallowed_area.markAsDisallowedAreaInBin(0)
                node_items.append(disallowed_area)

        for node in self._fixed_nodes:
            converted_points = []
            hull_polygon = node.callDecoration("getConvexHull")

            if hull_polygon is not None and hull_polygon.getPoints() is not None and len(
                    hull_polygon.getPoints()) > 2:  # numpy array has to be explicitly checked against None
                for point in hull_polygon.getPoints():
                    converted_points.append(Point(int(point[0] * self._factor), int(point[1] * self._factor)))
                item = Item(converted_points)
                item.markAsFixedInBin(0)
                node_items.append(item)

        strategies = [NfpConfig.Alignment.CENTER] * 3 + [NfpConfig.Alignment.BOTTOM_LEFT] * 3
        found_solution_for_all = False
        while not found_solution_for_all and len(strategies) > 0:
            config = NfpConfig()
            config.accuracy = 1.0
            config.alignment = NfpConfig.Alignment.CENTER
            config.starting_point = strategies[0]
            strategies = strategies[1:]

            if self._lock_rotation:
                config.rotations = [0.0]

            num_bins = nest(node_items, build_plate_bounding_box, spacing, config)

            # Strip the fixed items (previously placed) and the disallowed areas from the results again.
            node_items = list(filter(lambda item: not item.isFixed(), node_items))

            found_solution_for_all = num_bins == 1

        return found_solution_for_all, node_items

    def createGroupOperationForArrange(self, add_new_nodes_in_scene: bool = False) -> Tuple[GroupedOperation, int]:
        scene_root = Application.getInstance().getController().getScene().getRoot()
        found_solution_for_all, node_items = self.findNodePlacement()

        not_fit_count = 0
        grouped_operation = GroupedOperation()
        for node, node_item in zip(self._nodes_to_arrange, node_items):
            if add_new_nodes_in_scene:
                grouped_operation.addOperation(AddSceneNodeOperation(node, scene_root))

            if node_item.binId() == 0:
                # We found a spot for it
                rotation_matrix = Matrix()
                rotation_matrix.setByRotationAxis(node_item.rotation(), Vector(0, -1, 0))
                grouped_operation.addOperation(RotateOperation(node, Quaternion.fromMatrix(rotation_matrix)))
                grouped_operation.addOperation(
                    TranslateOperation(node, Vector(node_item.translation().x() / self._factor, 0,
                                                    node_item.translation().y() / self._factor)))
            else:
                # We didn't find a spot
                grouped_operation.addOperation(
                    TranslateOperation(node, Vector(200, node.getWorldPosition().y, -not_fit_count * 20), set_position = True))
                not_fit_count += 1

        return grouped_operation, not_fit_count


@deprecated("Use the Nest2DArrange class instead")
def findNodePlacement(nodes_to_arrange: List["SceneNode"], build_volume: "BuildVolume",
                      fixed_nodes: Optional[List["SceneNode"]] = None, factor=10000) -> Tuple[bool, List[Item]]:
    arranger = Nest2DArrange(nodes_to_arrange, build_volume, fixed_nodes, factor=factor)
    return arranger.findNodePlacement()


@deprecated("Use the Nest2DArrange class instead")
def createGroupOperationForArrange(nodes_to_arrange: List["SceneNode"],
                                   build_volume: "BuildVolume",
                                   fixed_nodes: Optional[List["SceneNode"]] = None,
                                   factor=10000,
                                   add_new_nodes_in_scene: bool = False) -> Tuple[GroupedOperation, int]:
    arranger = Nest2DArrange(nodes_to_arrange, build_volume, fixed_nodes, factor=factor)
    return arranger.createGroupOperationForArrange(add_new_nodes_in_scene=add_new_nodes_in_scene)


@deprecated("Use the Nest2DArrange class instead")
def arrange(nodes_to_arrange: List["SceneNode"],
            build_volume: "BuildVolume",
            fixed_nodes: Optional[List["SceneNode"]] = None,
            factor=10000,
            add_new_nodes_in_scene: bool = False) -> bool:
    arranger = Nest2DArrange(nodes_to_arrange, build_volume, fixed_nodes, factor=factor)
    return arranger.arrange(add_new_nodes_in_scene=add_new_nodes_in_scene)
