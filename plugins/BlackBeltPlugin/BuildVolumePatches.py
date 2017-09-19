from UM.Application import Application

from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Math.Vector import Vector
from UM.Math.Matrix import Matrix
from UM.Math.Color import Color
from UM.Math.AxisAlignedBox import AxisAlignedBox

import numpy
import math

class BuildVolumePatches():
    def __init__(self, build_volume):
        self._build_volume = build_volume
        self._build_volume.rebuild = self._rebuild

    ##  Recalculates the build volume & disallowed areas.
    #   Copied verbatim from Buildvolume.rebuild, with a minor patch to limit the buildvolume asymmetrically
    def _rebuild(self):
        if not self._build_volume._width or not self._build_volume._height or not self._build_volume._depth:
            return

        if not Application.getInstance()._engine:
            return

        if not self._build_volume._volume_outline_color:
            theme = Application.getInstance().getTheme()
            self._build_volume._volume_outline_color = Color(*theme.getColor("volume_outline").getRgb())
            self._build_volume._x_axis_color = Color(*theme.getColor("x_axis").getRgb())
            self._build_volume._y_axis_color = Color(*theme.getColor("y_axis").getRgb())
            self._build_volume._z_axis_color = Color(*theme.getColor("z_axis").getRgb())
            self._build_volume._disallowed_area_color = Color(*theme.getColor("disallowed_area").getRgb())
            self._build_volume._error_area_color = Color(*theme.getColor("error_area").getRgb())

        ### START PATCH
        # Get a dict from the machine metadata optionally overriding the build volume
        # Note that CuraEngine is blissfully unaware of this; it is just what the user is shown in Cura
        limit_buildvolume = self._build_volume._global_container_stack.getMetaDataEntry("limit_buildvolume", {})
        if not isinstance(limit_buildvolume, dict):
            limit_buildvolume = {}

        min_w = limit_buildvolume.get("width", {}).get("minimum",-self._build_volume._width / 2)
        max_w = limit_buildvolume.get("width", {}).get("maximum", self._build_volume._width / 2)
        min_h = limit_buildvolume.get("height", {}).get("minimum", 0.0)
        max_h = limit_buildvolume.get("height", {}).get("maximum", self._build_volume._height)
        min_d = limit_buildvolume.get("depth", {}).get("minimum",-self._build_volume._depth / 2)
        max_d = limit_buildvolume.get("depth", {}).get("maximum", self._build_volume._depth / 2)
        ### END PATCH

        z_fight_distance = 0.2 # Distance between buildplate and disallowed area meshes to prevent z-fighting

        if self._build_volume._shape != "elliptic":
            # Outline 'cube' of the build volume
            mb = MeshBuilder()
            mb.addLine(Vector(min_w, min_h, min_d), Vector(max_w, min_h, min_d), color = self._build_volume._volume_outline_color)
            mb.addLine(Vector(min_w, min_h, min_d), Vector(min_w, max_h, min_d), color = self._build_volume._volume_outline_color)
            mb.addLine(Vector(min_w, max_h, min_d), Vector(max_w, max_h, min_d), color = self._build_volume._volume_outline_color)
            mb.addLine(Vector(max_w, min_h, min_d), Vector(max_w, max_h, min_d), color = self._build_volume._volume_outline_color)

            mb.addLine(Vector(min_w, min_h, max_d), Vector(max_w, min_h, max_d), color = self._build_volume._volume_outline_color)
            mb.addLine(Vector(min_w, min_h, max_d), Vector(min_w, max_h, max_d), color = self._build_volume._volume_outline_color)
            mb.addLine(Vector(min_w, max_h, max_d), Vector(max_w, max_h, max_d), color = self._build_volume._volume_outline_color)
            mb.addLine(Vector(max_w, min_h, max_d), Vector(max_w, max_h, max_d), color = self._build_volume._volume_outline_color)

            mb.addLine(Vector(min_w, min_h, min_d), Vector(min_w, min_h, max_d), color = self._build_volume._volume_outline_color)
            mb.addLine(Vector(max_w, min_h, min_d), Vector(max_w, min_h, max_d), color = self._build_volume._volume_outline_color)
            mb.addLine(Vector(min_w, max_h, min_d), Vector(min_w, max_h, max_d), color = self._build_volume._volume_outline_color)
            mb.addLine(Vector(max_w, max_h, min_d), Vector(max_w, max_h, max_d), color = self._build_volume._volume_outline_color)

            self._build_volume.setMeshData(mb.build())

            # Build plate grid mesh
            mb = MeshBuilder()
            mb.addQuad(
                Vector(min_w, min_h - z_fight_distance, min_d),
                Vector(max_w, min_h - z_fight_distance, min_d),
                Vector(max_w, min_h - z_fight_distance, max_d),
                Vector(min_w, min_h - z_fight_distance, max_d)
            )

            for n in range(0, 6):
                v = mb.getVertex(n)
                mb.setVertexUVCoordinates(n, v[0], v[2])
            self._build_volume._grid_mesh = mb.build()

        else:
            # Bottom and top 'ellipse' of the build volume
            aspect = 1.0
            scale_matrix = Matrix()
            if self._build_volume._width != 0:
                # Scale circular meshes by aspect ratio if width != height
                aspect = self._build_volume._depth / self._build_volume._width
                scale_matrix.compose(scale = Vector(1, 1, aspect))
            mb = MeshBuilder()
            mb.addArc(max_w, Vector.Unit_Y, center = (0, min_h - z_fight_distance, 0), color = self._build_volume._volume_outline_color)
            mb.addArc(max_w, Vector.Unit_Y, center = (0, max_h, 0),  color = self._build_volume._volume_outline_color)
            self._build_volume.setMeshData(mb.build().getTransformed(scale_matrix))

            # Build plate grid mesh
            mb = MeshBuilder()
            mb.addVertex(0, min_h - z_fight_distance, 0)
            mb.addArc(max_w, Vector.Unit_Y, center = Vector(0, min_h - z_fight_distance, 0))
            sections = mb.getVertexCount() - 1 # Center point is not an arc section
            indices = []
            for n in range(0, sections - 1):
                indices.append([0, n + 2, n + 1])
            mb.addIndices(numpy.asarray(indices, dtype = numpy.int32))
            mb.calculateNormals()

            for n in range(0, mb.getVertexCount()):
                v = mb.getVertex(n)
                mb.setVertexUVCoordinates(n, v[0], v[2] * aspect)
            self._build_volume._grid_mesh = mb.build().getTransformed(scale_matrix)

        # Indication of the machine origin
        if self._build_volume._global_container_stack.getProperty("machine_center_is_zero", "value"):
            origin = (Vector(min_w, min_h, min_d) + Vector(max_w, min_h, max_d)) / 2
        else:
            origin = Vector(min_w, min_h, max_d)

        mb = MeshBuilder()
        mb.addCube(
            width = self._build_volume._origin_line_length,
            height = self._build_volume._origin_line_width,
            depth = self._build_volume._origin_line_width,
            center = origin + Vector(self._build_volume._origin_line_length / 2, 0, 0),
            color = self._build_volume._x_axis_color
        )
        mb.addCube(
            width = self._build_volume._origin_line_width,
            height = self._build_volume._origin_line_length,
            depth = self._build_volume._origin_line_width,
            center = origin + Vector(0, self._build_volume._origin_line_length / 2, 0),
            color = self._build_volume._y_axis_color
        )
        mb.addCube(
            width = self._build_volume._origin_line_width,
            height = self._build_volume._origin_line_width,
            depth = self._build_volume._origin_line_length,
            center = origin - Vector(0, 0, self._build_volume._origin_line_length / 2),
            color = self._build_volume._z_axis_color
        )
        self._build_volume._origin_mesh = mb.build()

        disallowed_area_height = 0.1
        disallowed_area_size = 0
        if self._build_volume._disallowed_areas:
            mb = MeshBuilder()
            color = self._build_volume._disallowed_area_color
            for polygon in self._build_volume._disallowed_areas:
                points = polygon.getPoints()
                if len(points) == 0:
                    continue

                first = Vector(self._build_volume._clamp(points[0][0], min_w, max_w), disallowed_area_height, self._build_volume._clamp(points[0][1], min_d, max_d))
                previous_point = Vector(self._build_volume._clamp(points[0][0], min_w, max_w), disallowed_area_height, self._build_volume._clamp(points[0][1], min_d, max_d))
                for point in points:
                    new_point = Vector(self._build_volume._clamp(point[0], min_w, max_w), disallowed_area_height, self._build_volume._clamp(point[1], min_d, max_d))
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

            self._build_volume._disallowed_area_mesh = mb.build()
        else:
            self._build_volume._disallowed_area_mesh = None

        if self._build_volume._error_areas:
            mb = MeshBuilder()
            for error_area in self._build_volume._error_areas:
                color = self._build_volume._error_area_color
                points = error_area.getPoints()
                first = Vector(self._build_volume._clamp(points[0][0], min_w, max_w), disallowed_area_height,
                               self._build_volume._clamp(points[0][1], min_d, max_d))
                previous_point = Vector(self._build_volume._clamp(points[0][0], min_w, max_w), disallowed_area_height,
                                        self._build_volume._clamp(points[0][1], min_d, max_d))
                for point in points:
                    new_point = Vector(self._build_volume._clamp(point[0], min_w, max_w), disallowed_area_height,
                                       self._build_volume._clamp(point[1], min_d, max_d))
                    mb.addFace(first, previous_point, new_point, color=color)
                    previous_point = new_point
            self._build_volume._error_mesh = mb.build()
        else:
            self._build_volume._error_mesh = None

        self._build_volume._volume_aabb = AxisAlignedBox(
            minimum = Vector(min_w, min_h - 1.0, min_d),
            maximum = Vector(max_w, max_h - self._build_volume._raft_thickness - self._build_volume._extra_z_clearance, max_d))

        bed_adhesion_size = self._build_volume._getEdgeDisallowedSize()

        # As this works better for UM machines, we only add the disallowed_area_size for the z direction.
        # This is probably wrong in all other cases. TODO!
        # The +1 and -1 is added as there is always a bit of extra room required to work properly.
        scale_to_max_bounds = AxisAlignedBox(
            minimum = Vector(min_w + bed_adhesion_size + 1, min_h, min_d + disallowed_area_size - bed_adhesion_size + 1),
            maximum = Vector(max_w - bed_adhesion_size - 1, max_h - self._build_volume._raft_thickness - self._build_volume._extra_z_clearance, max_d - disallowed_area_size + bed_adhesion_size - 1)
        )

        Application.getInstance().getController().getScene()._maximum_bounds = scale_to_max_bounds

        self._build_volume.updateNodeBoundaryCheck()
