import numpy
from pynest2d import *

from UM.Math.Matrix import Matrix
from UM.Math.Polygon import Polygon
from UM.Math.Quaternion import Quaternion
from UM.Math.Vector import Vector
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.RotateOperation import RotateOperation
from UM.Operations.TranslateOperation import TranslateOperation


def findNodePlacement(nodes_to_arrange, build_volume, fixed_nodes = None, factor = 10000):
    machine_width = build_volume.getWidth()
    machine_depth = build_volume.getDepth()
    build_plate_bounding_box = Box(machine_width * factor, machine_depth * factor)

    # Add all the items we want to arrange
    node_items = []
    for node in nodes_to_arrange:
        hull_polygon = node.callDecoration("getConvexHull")
        converted_points = []
        for point in hull_polygon.getPoints():
            converted_points.append(Point(point[0] * factor, point[1] * factor))
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

        for point in clipped_area.getPoints():
            converted_points.append(Point(point[0] * factor, point[1] * factor))

        disallowed_area = Item(converted_points)
        disallowed_area.markAsFixedInBin(0)
        node_items.append(disallowed_area)
        num_disallowed_areas_added += 1

    config = NfpConfig()
    config.accuracy = 1.0

    num_bins = nest(node_items, build_plate_bounding_box, 10000, config)

    # Strip the disallowed areas from the results again
    if num_disallowed_areas_added != 0:
        node_items = node_items[:-num_disallowed_areas_added]

    found_solution_for_all = num_bins == 1

    return found_solution_for_all, node_items


def arrange(nodes_to_arrange, build_volume, fixed_nodes = None, factor = 10000) -> bool:
    found_solution_for_all, node_items = findNodePlacement(nodes_to_arrange, build_volume, fixed_nodes, factor)

    not_fit_count = 0
    grouped_operation = GroupedOperation()
    for node, node_item in zip(nodes_to_arrange, node_items):
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
                TranslateOperation(node, Vector(200, 0, -not_fit_count * 20), set_position=True))
            not_fit_count += 1
    grouped_operation.push()

    return found_solution_for_all
