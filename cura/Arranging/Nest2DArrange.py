# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import numpy
from pynest2d import Point, Box, Item, NfpConfig, nest
from typing import List, TYPE_CHECKING, Optional, Tuple

from UM.Application import Application
from UM.Logger import Logger
from UM.Math.Matrix import Matrix
from UM.Math.Polygon import Polygon
from UM.Math.Quaternion import Quaternion
from UM.Math.Vector import Vector
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.RotateOperation import RotateOperation
from UM.Operations.TranslateOperation import TranslateOperation


if TYPE_CHECKING:
    from UM.Scene.SceneNode import SceneNode
    from cura.BuildVolume import BuildVolume


def findNodePlacement(nodes_to_arrange: List["SceneNode"], build_volume: "BuildVolume", fixed_nodes: Optional[List["SceneNode"]] = None, factor = 10000) -> Tuple[bool, List[Item]]:
    """
    Find placement for a set of scene nodes, but don't actually move them just yet.
    :param nodes_to_arrange: The list of nodes that need to be moved.
    :param build_volume: The build volume that we want to place the nodes in. It gets size & disallowed areas from this.
    :param fixed_nodes: List of nods that should not be moved, but should be used when deciding where the others nodes
                        are placed.
    :param factor: The library that we use is int based. This factor defines how accurate we want it to be.

    :return: tuple (found_solution_for_all, node_items)
        WHERE
        found_solution_for_all: Whether the algorithm found a place on the buildplate for all the objects
        node_items: A list of the nodes return by libnest2d, which contain the new positions on the buildplate
    """
    spacing = int(1.5 * factor)  # 1.5mm spacing.

    machine_width = build_volume.getWidth()
    machine_depth = build_volume.getDepth()
    build_plate_bounding_box = Box(machine_width * factor, machine_depth * factor)

    if fixed_nodes is None:
        fixed_nodes = []

    # Add all the items we want to arrange
    node_items = []
    for node in nodes_to_arrange:
        hull_polygon = node.callDecoration("getConvexHull")
        if not hull_polygon or hull_polygon.getPoints is None:
            Logger.log("w", "Object {} cannot be arranged because it has no convex hull.".format(node.getName()))
            continue
        converted_points = []
        for point in hull_polygon.getPoints():
            converted_points.append(Point(int(point[0] * factor), int(point[1] * factor)))
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

    disallowed_areas = build_volume.getDisallowedAreas()
    num_disallowed_areas_added = 0
    for area in disallowed_areas:
        converted_points = []

        # Clip the disallowed areas so that they don't overlap the bounding box (The arranger chokes otherwise)
        clipped_area = area.intersectionConvexHulls(build_plate_polygon)

        if clipped_area.getPoints() is not None and len(clipped_area.getPoints()) > 2:  # numpy array has to be explicitly checked against None
            for point in clipped_area.getPoints():
                converted_points.append(Point(int(point[0] * factor), int(point[1] * factor)))

            disallowed_area = Item(converted_points)
            disallowed_area.markAsDisallowedAreaInBin(0)
            node_items.append(disallowed_area)
            num_disallowed_areas_added += 1

    for node in fixed_nodes:
        converted_points = []
        hull_polygon = node.callDecoration("getConvexHull")

        if hull_polygon is not None and hull_polygon.getPoints() is not None and len(hull_polygon.getPoints()) > 2:  # numpy array has to be explicitly checked against None
            for point in hull_polygon.getPoints():
                converted_points.append(Point(int(point[0] * factor), int(point[1] * factor)))
            item = Item(converted_points)
            item.markAsFixedInBin(0)
            node_items.append(item)
            num_disallowed_areas_added += 1

    config = NfpConfig()
    config.accuracy = 1.0

    num_bins = nest(node_items, build_plate_bounding_box, spacing, config)

    # Strip the fixed items (previously placed) and the disallowed areas from the results again.
    node_items = list(filter(lambda item: not item.isFixed(), node_items))

    found_solution_for_all = num_bins == 1

    return found_solution_for_all, node_items


def createGroupOperationForArrange(nodes_to_arrange: List["SceneNode"],
                                   build_volume: "BuildVolume",
                                   fixed_nodes: Optional[List["SceneNode"]] = None,
                                   factor = 10000,
                                   add_new_nodes_in_scene: bool = False)  -> Tuple[GroupedOperation, int]:
    scene_root = Application.getInstance().getController().getScene().getRoot()
    found_solution_for_all, node_items = findNodePlacement(nodes_to_arrange, build_volume, fixed_nodes, factor)

    not_fit_count = 0
    grouped_operation = GroupedOperation()
    for node, node_item in zip(nodes_to_arrange, node_items):
        if add_new_nodes_in_scene:
            grouped_operation.addOperation(AddSceneNodeOperation(node, scene_root))

        if node_item.binId() == 0:
            # We found a spot for it
            rotation_matrix = Matrix()
            rotation_matrix.setByRotationAxis(node_item.rotation(), Vector(0, -1, 0))
            grouped_operation.addOperation(RotateOperation(node, Quaternion.fromMatrix(rotation_matrix)))
            grouped_operation.addOperation(TranslateOperation(node, Vector(node_item.translation().x() / factor, 0,
                                                                           node_item.translation().y() / factor)))
        else:
            # We didn't find a spot
            grouped_operation.addOperation(
                TranslateOperation(node, Vector(200, node.getWorldPosition().y, -not_fit_count * 20), set_position = True))
            not_fit_count += 1

    return grouped_operation, not_fit_count


def arrange(nodes_to_arrange: List["SceneNode"],
            build_volume: "BuildVolume",
            fixed_nodes: Optional[List["SceneNode"]] = None,
            factor = 10000,
            add_new_nodes_in_scene: bool = False) -> bool:
    """
    Find placement for a set of scene nodes, and move them by using a single grouped operation.
    :param nodes_to_arrange: The list of nodes that need to be moved.
    :param build_volume: The build volume that we want to place the nodes in. It gets size & disallowed areas from this.
    :param fixed_nodes: List of nods that should not be moved, but should be used when deciding where the others nodes
                        are placed.
    :param factor: The library that we use is int based. This factor defines how accuracte we want it to be.
    :param add_new_nodes_in_scene: Whether to create new scene nodes before applying the transformations and rotations

    :return: found_solution_for_all: Whether the algorithm found a place on the buildplate for all the objects
    """

    grouped_operation, not_fit_count = createGroupOperationForArrange(nodes_to_arrange, build_volume, fixed_nodes, factor, add_new_nodes_in_scene)
    grouped_operation.push()
    return not_fit_count == 0
