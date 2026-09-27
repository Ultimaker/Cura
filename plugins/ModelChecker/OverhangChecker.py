# Copyright (c) 2026 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import math

import numpy
import pyUvula as uvula

from UM.Application import Application
from UM.Scene.SceneNode import SceneNode
from cura.Settings.GlobalStack import GlobalStack

def getSupportAngle() -> float:
    """Retrieves the minimum angle needed in order for support to be generated in radians."""
    global_container_stack: GlobalStack = Application.getInstance().getGlobalContainerStack()
    if not global_container_stack:
        return math.tau / 4.0
    extruder_nr = int(global_container_stack.getExtruderPositionValueWithDefault("support_extruder_nr"))
    if extruder_nr < 0 or extruder_nr >= len(global_container_stack.extruderList):
        return math.tau / 4.0
    return (global_container_stack.extruderList[extruder_nr].getValue("support_angle") or 90.0) * math.tau / 360.0


def getCloseToBuildplateDistance() -> float:
    """Retrieves the distance that is close enough to the build-plate that no support needs to be generated."""
    global_container_stack: GlobalStack = Application.getInstance().getGlobalContainerStack()
    return 0.5 * global_container_stack.getValue("layer_height") if global_container_stack else 0.05


def getMinSupportArea() -> float:
    """Retrieves the magnitude of an area, below which support isn't generated."""
    global_container_stack: GlobalStack = Application.getInstance().getGlobalContainerStack()
    return global_container_stack.getValue("minimum_support_area") if global_container_stack else 4.0


def checkDownwardsFeatures(node: SceneNode) -> bool:
    support_angle = getSupportAngle()
    close_to_buildplate = getCloseToBuildplateDistance()
    min_support_area = getMinSupportArea()
    meshdata = node.getMeshDataTransformed()
    mesh_vertices = meshdata.getVertices()
    mesh_indices = meshdata.getIndices()
    if mesh_indices is None:
        mesh_indices = numpy.array([], dtype=numpy.int32)
    mesh_connects = meshdata.getFacesConnections()
    return uvula.checkDownwardsFeatures(
        support_angle,
        close_to_buildplate,
        min_support_area,
        mesh_vertices,
        mesh_indices,
        mesh_connects
    )
