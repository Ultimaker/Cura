# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Scene.SceneNode import SceneNode
from UM.Application import Application
from UM.Resources import Resources
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Math.Vector import Vector
from UM.Math.Color import Color
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Math.Polygon import Polygon

from UM.View.RenderBatch import RenderBatch
from UM.View.GL.OpenGL import OpenGL

import numpy


##  Build volume is a special kind of node that is responsible for rendering the printable area & disallowed areas.
class BuildVolume(SceneNode):
    VolumeOutlineColor = Color(12, 169, 227, 255)

    def __init__(self, parent = None):
        super().__init__(parent)

        self._width = 0
        self._height = 0
        self._depth = 0

        self._shader = None

        self._grid_mesh = None
        self._grid_shader = None

        self._disallowed_areas = []
        self._disallowed_area_mesh = None

        self.setCalculateBoundingBox(False)

        self._active_container_stack = None
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerStackChanged)
        self._onGlobalContainerStackChanged()

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

        if not self._shader:
            self._shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "default.shader"))
            self._grid_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "grid.shader"))

        renderer.queueNode(self, mode = RenderBatch.RenderMode.Lines)
        renderer.queueNode(self, mesh = self._grid_mesh, shader = self._grid_shader, backface_cull = True)
        if self._disallowed_area_mesh:
            renderer.queueNode(self, mesh = self._disallowed_area_mesh, shader = self._shader, transparent = True, backface_cull = True, sort = -9)
        return True

    ##  Recalculates the build volume & disallowed areas.
    def rebuild(self):
        if not self._width or not self._height or not self._depth:
            return

        min_w = -self._width / 2
        max_w = self._width / 2
        min_h = 0.0
        max_h = self._height
        min_d = -self._depth / 2
        max_d = self._depth / 2

        mb = MeshBuilder()

        mb.addLine(Vector(min_w, min_h, min_d), Vector(max_w, min_h, min_d), color = self.VolumeOutlineColor)
        mb.addLine(Vector(min_w, min_h, min_d), Vector(min_w, max_h, min_d), color = self.VolumeOutlineColor)
        mb.addLine(Vector(min_w, max_h, min_d), Vector(max_w, max_h, min_d), color = self.VolumeOutlineColor)
        mb.addLine(Vector(max_w, min_h, min_d), Vector(max_w, max_h, min_d), color = self.VolumeOutlineColor)

        mb.addLine(Vector(min_w, min_h, max_d), Vector(max_w, min_h, max_d), color = self.VolumeOutlineColor)
        mb.addLine(Vector(min_w, min_h, max_d), Vector(min_w, max_h, max_d), color = self.VolumeOutlineColor)
        mb.addLine(Vector(min_w, max_h, max_d), Vector(max_w, max_h, max_d), color = self.VolumeOutlineColor)
        mb.addLine(Vector(max_w, min_h, max_d), Vector(max_w, max_h, max_d), color = self.VolumeOutlineColor)

        mb.addLine(Vector(min_w, min_h, min_d), Vector(min_w, min_h, max_d), color = self.VolumeOutlineColor)
        mb.addLine(Vector(max_w, min_h, min_d), Vector(max_w, min_h, max_d), color = self.VolumeOutlineColor)
        mb.addLine(Vector(min_w, max_h, min_d), Vector(min_w, max_h, max_d), color = self.VolumeOutlineColor)
        mb.addLine(Vector(max_w, max_h, min_d), Vector(max_w, max_h, max_d), color = self.VolumeOutlineColor)

        self.setMeshData(mb.getData())

        mb = MeshBuilder()
        mb.addQuad(
            Vector(min_w, min_h - 0.2, min_d),
            Vector(max_w, min_h - 0.2, min_d),
            Vector(max_w, min_h - 0.2, max_d),
            Vector(min_w, min_h - 0.2, max_d)
        )
        self._grid_mesh = mb.getData()
        for n in range(0, 6):
            v = self._grid_mesh.getVertex(n)
            self._grid_mesh.setVertexUVCoordinates(n, v[0], v[2])

        disallowed_area_height = 0.1
        disallowed_area_size = 0
        if self._disallowed_areas:
            mb = MeshBuilder()
            color = Color(0.0, 0.0, 0.0, 0.15)
            for polygon in self._disallowed_areas:
                points = polygon.getPoints()
                first = Vector(self._clamp(points[0][0], min_w, max_w), disallowed_area_height, self._clamp(points[0][1], min_d, max_d))
                previous_point = Vector(self._clamp(points[0][0], min_w, max_w), disallowed_area_height, self._clamp(points[0][1], min_d, max_d))
                for point in points:
                    new_point = Vector(self._clamp(point[0], min_w, max_w), disallowed_area_height, self._clamp(point[1], min_d, max_d))
                    mb.addFace(first, previous_point, new_point, color = color)
                    previous_point = new_point

                # Find the largest disallowed area to exclude it from the maximum scale bounds.
                # This is a very nasty hack. This pretty much only works for UM machines.
                # This disallowed area_size needs a -lot- of rework at some point in the future: TODO
                if numpy.min(points[:, 1]) >= 0: # This filters out all areas that have points to the left of the centre. This is done to filter the skirt area.
                    size = abs(numpy.max(points[:, 1]) - numpy.min(points[:, 1]))
                else:
                    size = 0
                disallowed_area_size = max(size, disallowed_area_size)

            self._disallowed_area_mesh = mb.getData()
        else:
            self._disallowed_area_mesh = None

        self._aabb = AxisAlignedBox(minimum = Vector(min_w, min_h - 1.0, min_d), maximum = Vector(max_w, max_h, max_d))

        skirt_size = 0.0

        container_stack = Application.getInstance().getGlobalContainerStack()
        if container_stack:
            skirt_size = self._getSkirtSize(container_stack)

        # As this works better for UM machines, we only add the disallowed_area_size for the z direction.
        # This is probably wrong in all other cases. TODO!
        # The +1 and -1 is added as there is always a bit of extra room required to work properly.
        scale_to_max_bounds = AxisAlignedBox(
            minimum = Vector(min_w + skirt_size + 1, min_h, min_d + disallowed_area_size - skirt_size + 1),
            maximum = Vector(max_w - skirt_size - 1, max_h, max_d - disallowed_area_size + skirt_size - 1)
        )

        Application.getInstance().getController().getScene()._maximum_bounds = scale_to_max_bounds

    def _onGlobalContainerStackChanged(self):
        if self._active_container_stack:
            self._active_container_stack.propertyChanged.disconnect(self._onSettingPropertyChanged)

        self._active_container_stack = Application.getInstance().getGlobalContainerStack()

        if self._active_container_stack:
            self._active_container_stack.propertyChanged.connect(self._onSettingPropertyChanged)

            self._width = self._active_container_stack.getProperty("machine_width", "value")
            if self._active_container_stack.getProperty("print_sequence", "value") == "one_at_a_time":
                self._height = self._active_container_stack.getProperty("gantry_height", "value")
            else:
                self._height = self._active_container_stack.getProperty("machine_height", "value")
            self._depth = self._active_container_stack.getProperty("machine_depth", "value")

            self._updateDisallowedAreas()

            self.rebuild()

    def _onSettingPropertyChanged(self, setting_key, property_name):
        if property_name != "value":
            return

        if setting_key == "print_sequence":
            if Application.getInstance().getGlobalContainerStack().getProperty("print_sequence", "value") == "one_at_a_time":
                self._height = self._active_container_stack.getProperty("gantry_height", "value")
            else:
                self._height = self._active_container_stack.getProperty("machine_height", "value")
            self.rebuild()
        if setting_key in self._skirt_settings:
            self._updateDisallowedAreas()
            self.rebuild()

    def _updateDisallowedAreas(self):
        if not self._active_container_stack:
            return

        disallowed_areas = self._active_container_stack.getProperty("machine_disallowed_areas", "value")
        areas = []

        skirt_size = 0.0
        skirt_size = self._getSkirtSize(self._active_container_stack)

        if disallowed_areas:
            # Extend every area already in the disallowed_areas with the skirt size.
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

        # Add the skirt areas around the borders of the build plate.
        if skirt_size > 0:
            half_machine_width = self._active_container_stack.getProperty("machine_width", "value") / 2
            half_machine_depth = self._active_container_stack.getProperty("machine_depth", "value") / 2

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

    ##  Convenience function to calculate the size of the bed adhesion.
    def _getSkirtSize(self, container_stack):
        skirt_size = 0.0

        adhesion_type = container_stack.getProperty("adhesion_type", "value")
        if adhesion_type == "skirt":
            skirt_distance = container_stack.getProperty("skirt_gap", "value")
            skirt_line_count = container_stack.getProperty("skirt_line_count", "value")
            skirt_size = skirt_distance + (skirt_line_count * container_stack.getProperty("skirt_line_width", "value"))
        elif adhesion_type == "brim":
            skirt_size = container_stack.getProperty("brim_line_count", "value") * container_stack.getProperty("skirt_line_width", "value")
        elif adhesion_type == "raft":
            skirt_size = container_stack.getProperty("raft_margin", "value")

        if container_stack.getProperty("draft_shield_enabled", "value"):
            skirt_size += container_stack.getProperty("draft_shield_dist", "value")

        if container_stack.getProperty("xy_offset", "value"):
            skirt_size += container_stack.getProperty("xy_offset", "value")

        return skirt_size

    def _clamp(self, value, min_value, max_value):
        return max(min(value, max_value), min_value)

    _skirt_settings = ["adhesion_type", "skirt_gap", "skirt_line_count", "skirt_line_width", "brim_width", "brim_line_count", "raft_margin", "draft_shield_enabled", "draft_shield_dist", "xy_offset"]
