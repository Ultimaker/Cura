# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.View.Renderer import Renderer
from UM.Scene.SceneNode import SceneNode
from UM.Application import Application
from UM.Resources import Resources
from UM.Mesh.MeshData import MeshData
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Math.Vector import Vector
from UM.Math.Color import Color
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Math.Polygon import Polygon

import numpy

class BuildVolume(SceneNode):
    VolumeOutlineColor = Color(12, 169, 227, 255)

    def __init__(self, parent = None):
        super().__init__(parent)

        self._width = 0
        self._height = 0
        self._depth = 0

        self._material = None

        self._grid_mesh = None
        self._grid_material = None

        self._disallowed_areas = []
        self._disallowed_area_mesh = None

        self.setCalculateBoundingBox(False)

        self._active_profile = None
        self._active_instance = None
        Application.getInstance().getMachineManager().activeMachineInstanceChanged.connect(self._onActiveInstanceChanged)
        self._onActiveInstanceChanged()

        Application.getInstance().getMachineManager().activeProfileChanged.connect(self._onActiveProfileChanged)
        self._onActiveProfileChanged()

    def setWidth(self, width):
        if width: self._width = width

    def setHeight(self, height):
        if height: self._height = height

    def setDepth(self, depth):
        if depth: self._depth = depth

    def getDisallowedAreas(self):
        return self._disallowed_areas

    def setDisallowedAreas(self, areas):
        self._disallowed_areas = areas

    def render(self, renderer):
        if not self.getMeshData():
            return True

        if not self._material:
            self._material = renderer.createMaterial(
                Resources.getPath(Resources.Shaders, "basic.vert"),
                Resources.getPath(Resources.Shaders, "vertexcolor.frag")
            )
            self._grid_material = renderer.createMaterial(
                Resources.getPath(Resources.Shaders, "basic.vert"),
                Resources.getPath(Resources.Shaders, "grid.frag")
            )
            self._grid_material.setUniformValue("u_gridColor0", Color(245, 245, 245, 255))
            self._grid_material.setUniformValue("u_gridColor1", Color(205, 202, 201, 255))

        renderer.queueNode(self, material = self._material, mode = Renderer.RenderLines)
        renderer.queueNode(self, mesh = self._grid_mesh, material = self._grid_material, force_single_sided = True)
        if self._disallowed_area_mesh:
            renderer.queueNode(self, mesh = self._disallowed_area_mesh, material = self._material, transparent = True)
        return True

    def rebuild(self):
        if self._width == 0 or self._height == 0 or self._depth == 0:
            return

        minW = -self._width / 2
        maxW = self._width / 2
        minH = 0.0
        maxH = self._height
        minD = -self._depth / 2
        maxD = self._depth / 2

        mb = MeshBuilder()

        mb.addLine(Vector(minW, minH, minD), Vector(maxW, minH, minD), color = self.VolumeOutlineColor)
        mb.addLine(Vector(minW, minH, minD), Vector(minW, maxH, minD), color = self.VolumeOutlineColor)
        mb.addLine(Vector(minW, maxH, minD), Vector(maxW, maxH, minD), color = self.VolumeOutlineColor)
        mb.addLine(Vector(maxW, minH, minD), Vector(maxW, maxH, minD), color = self.VolumeOutlineColor)

        mb.addLine(Vector(minW, minH, maxD), Vector(maxW, minH, maxD), color = self.VolumeOutlineColor)
        mb.addLine(Vector(minW, minH, maxD), Vector(minW, maxH, maxD), color = self.VolumeOutlineColor)
        mb.addLine(Vector(minW, maxH, maxD), Vector(maxW, maxH, maxD), color = self.VolumeOutlineColor)
        mb.addLine(Vector(maxW, minH, maxD), Vector(maxW, maxH, maxD), color = self.VolumeOutlineColor)

        mb.addLine(Vector(minW, minH, minD), Vector(minW, minH, maxD), color = self.VolumeOutlineColor)
        mb.addLine(Vector(maxW, minH, minD), Vector(maxW, minH, maxD), color = self.VolumeOutlineColor)
        mb.addLine(Vector(minW, maxH, minD), Vector(minW, maxH, maxD), color = self.VolumeOutlineColor)
        mb.addLine(Vector(maxW, maxH, minD), Vector(maxW, maxH, maxD), color = self.VolumeOutlineColor)

        self.setMeshData(mb.getData())

        mb = MeshBuilder()
        mb.addQuad(
            Vector(minW, minH, minD),
            Vector(maxW, minH, minD),
            Vector(maxW, minH, maxD),
            Vector(minW, minH, maxD)
        )
        self._grid_mesh = mb.getData()
        for n in range(0, 6):
            v = self._grid_mesh.getVertex(n)
            self._grid_mesh.setVertexUVCoordinates(n, v[0], v[2])

        disallowed_area_height = 0.2
        disallowed_area_size = 0
        if self._disallowed_areas:
            mb = MeshBuilder()
            color = Color(0.0, 0.0, 0.0, 0.15)
            for polygon in self._disallowed_areas:
                points = polygon.getPoints()
                first = Vector(self._clamp(points[0][0], minW, maxW), disallowed_area_height, self._clamp(points[0][1], minD, maxD))
                previous_point = Vector(self._clamp(points[0][0], minW, maxW), disallowed_area_height, self._clamp(points[0][1], minD, maxD))
                for point in points:
                    new_point = Vector(self._clamp(point[0], minW, maxW), disallowed_area_height, self._clamp(point[1], minD, maxD))
                    mb.addFace(first, previous_point, new_point, color = color)
                    previous_point = new_point

                # Find the largest disallowed area to exclude it from the maximum scale bounds
                size = abs(numpy.max(points[:, 1]) - numpy.min(points[:, 1]))
                disallowed_area_size = max(size, disallowed_area_size)

            self._disallowed_area_mesh = mb.getData()
        else:
            self._disallowed_area_mesh = None

        self._aabb = AxisAlignedBox(minimum = Vector(minW, minH - 1.0, minD), maximum = Vector(maxW, maxH, maxD))

        skirt_size = 0.0

        profile = Application.getInstance().getMachineManager().getActiveProfile()
        if profile:
            skirt_size = self._getSkirtSize(profile)

        scale_to_max_bounds = AxisAlignedBox(
            minimum = Vector(minW + skirt_size, minH, minD + skirt_size + disallowed_area_size),
            maximum = Vector(maxW - skirt_size, maxH, maxD - skirt_size - disallowed_area_size)
        )

        Application.getInstance().getController().getScene()._maximum_bounds = scale_to_max_bounds

    def _onActiveInstanceChanged(self):
        self._active_instance = Application.getInstance().getMachineManager().getActiveMachineInstance()

        if self._active_instance:
            self._width = self._active_instance.getMachineSettingValue("machine_width")
            self._height = self._active_instance.getMachineSettingValue("machine_height")
            self._depth = self._active_instance.getMachineSettingValue("machine_depth")

            self._updateDisallowedAreas()

            self.rebuild()

    def _onActiveProfileChanged(self):
        if self._active_profile:
            self._active_profile.settingValueChanged.disconnect(self._onSettingValueChanged)

        self._active_profile = Application.getInstance().getMachineManager().getActiveProfile()
        if self._active_profile:
            self._active_profile.settingValueChanged.connect(self._onSettingValueChanged)
            self._updateDisallowedAreas()
            self.rebuild()

    def _onSettingValueChanged(self, setting):
        if setting in self._skirt_settings:
            self._updateDisallowedAreas()
            self.rebuild()

    def _updateDisallowedAreas(self):
        if not self._active_instance or not self._active_profile:
            return

        disallowed_areas = self._active_instance.getMachineSettingValue("machine_disallowed_areas")
        areas = []

        skirt_size = 0.0
        if self._active_profile:
            skirt_size = self._getSkirtSize(self._active_profile)

        if disallowed_areas:
            for area in disallowed_areas:
                poly = Polygon(numpy.array(area, numpy.float32))
                poly = poly.getMinkowskiHull(Polygon(numpy.array([
                    [-skirt_size, 0],
                    [-skirt_size * 0.707, skirt_size * 0.707],
                    [0, skirt_size],
                    [skirt_size * 0.707, skirt_size * 0.707],
                    [skirt_size, 0],
                    [skirt_size * 0.707, -skirt_size * 0.707],
                    [0, -skirt_size],
                    [-skirt_size * 0.707, -skirt_size * 0.707]
                ], numpy.float32)))

                areas.append(poly)

        if skirt_size > 0:
            half_machine_width = self._active_instance.getMachineSettingValue("machine_width") / 2
            half_machine_depth = self._active_instance.getMachineSettingValue("machine_depth") / 2

            areas.append(Polygon(numpy.array([
                [-half_machine_width, -half_machine_depth],
                [-half_machine_width, half_machine_depth],
                [-half_machine_width + skirt_size, half_machine_depth - skirt_size],
                [-half_machine_width + skirt_size, -half_machine_depth + skirt_size]
            ], numpy.float32)))

            areas.append(Polygon(numpy.array([
                [half_machine_width, half_machine_depth],
                [half_machine_width, -half_machine_depth],
                [half_machine_width - skirt_size, -half_machine_depth + skirt_size],
                [half_machine_width - skirt_size, half_machine_depth - skirt_size]
            ], numpy.float32)))

            areas.append(Polygon(numpy.array([
                [-half_machine_width, half_machine_depth],
                [half_machine_width, half_machine_depth],
                [half_machine_width - skirt_size, half_machine_depth - skirt_size],
                [-half_machine_width + skirt_size, half_machine_depth - skirt_size]
            ], numpy.float32)))

            areas.append(Polygon(numpy.array([
                [half_machine_width, -half_machine_depth],
                [-half_machine_width, -half_machine_depth],
                [-half_machine_width + skirt_size, -half_machine_depth + skirt_size],
                [half_machine_width - skirt_size, -half_machine_depth + skirt_size]
            ], numpy.float32)))

        self._disallowed_areas = areas

    def _getSkirtSize(self, profile):
        skirt_size = 0.0

        adhesion_type = profile.getSettingValue("adhesion_type")
        if adhesion_type == "skirt":
            skirt_distance = profile.getSettingValue("skirt_gap")
            skirt_line_count = profile.getSettingValue("skirt_line_count")
            skirt_size = skirt_distance + (skirt_line_count * profile.getSettingValue("skirt_line_width"))
        elif adhesion_type == "brim":
            brim_line_count = profile.getSettingValue("brim_line_count")
            skirt_size = brim_line_count * profile.getSettingValue("skirt_line_width")
        elif adhesion_type == "raft":
            skirt_size = profile.getSettingValue("raft_margin")

        if profile.getSettingValue("draft_shield_enabled"):
            skirt_size += profile.getSettingValue("draft_shield_dist")

        skirt_size += profile.getSettingValue("xy_offset")

        return skirt_size

    def _clamp(self, value, min_value, max_value):
        return max(min(value, max_value), min_value)

    _skirt_settings = ["adhesion_type", "skirt_gap", "skirt_line_count", "skirt_line_width", "brim_line_count", "raft_margin", "draft_shield_enabled", "draft_shield_dist", "xy_offset"]
