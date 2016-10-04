# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from cura.Settings.ExtruderManager import ExtruderManager
from UM.i18n import i18nCatalog
from UM.Scene.Platform import Platform
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Application import Application
from UM.Resources import Resources
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Math.Vector import Vector
from UM.Math.Color import Color
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Math.Polygon import Polygon
from UM.Message import Message
from UM.Signal import Signal
from PyQt5.QtCore import QTimer
from UM.View.RenderBatch import RenderBatch
from UM.View.GL.OpenGL import OpenGL
catalog = i18nCatalog("cura")

import numpy
import copy

import UM.Settings.ContainerRegistry


# Setting for clearance around the prime
PRIME_CLEARANCE = 1.5


##  Build volume is a special kind of node that is responsible for rendering the printable area & disallowed areas.
class BuildVolume(SceneNode):
    VolumeOutlineColor = Color(12, 169, 227, 255)

    raftThicknessChanged = Signal()

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

        self._error_areas = []
        self._error_mesh = None

        self.setCalculateBoundingBox(False)
        self._volume_aabb = None

        self._raft_thickness = 0.0
        self._adhesion_type = None
        self._platform = Platform(self)

        self._global_container_stack = None
        Application.getInstance().globalContainerStackChanged.connect(self._onStackChanged)
        self._onStackChanged()

        self._has_errors = False
        Application.getInstance().getController().getScene().sceneChanged.connect(self._onSceneChanged)

        # Number of objects loaded at the moment.
        self._number_of_objects = 0

        self._change_timer = QTimer()
        self._change_timer.setInterval(100)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self._onChangeTimerFinished)

        self._build_volume_message = Message(catalog.i18nc("@info:status",
            "The build volume height has been reduced due to the value of the"
            " \"Print Sequence\" setting to prevent the gantry from colliding"
            " with printed models."))

        # Must be after setting _build_volume_message, apparently that is used in getMachineManager.
        # activeQualityChanged is always emitted after setActiveVariant, setActiveMaterial and setActiveQuality.
        # Therefore this works.
        Application.getInstance().getMachineManager().activeQualityChanged.connect(self._onStackChanged)
        # This should also ways work, and it is semantically more correct,
        # but it does not update the disallowed areas after material change
        Application.getInstance().getMachineManager().activeStackChanged.connect(self._onStackChanged)

    def _onSceneChanged(self, source):
        if self._global_container_stack:
            self._change_timer.start()

    def _onChangeTimerFinished(self):
        root = Application.getInstance().getController().getScene().getRoot()
        new_number_of_objects = len([node for node in BreadthFirstIterator(root) if node.getMeshData() and type(node) is SceneNode])
        if new_number_of_objects != self._number_of_objects:
            recalculate = False
            if self._global_container_stack.getProperty("print_sequence", "value") == "one_at_a_time":
                recalculate = (new_number_of_objects < 2 and self._number_of_objects > 1) or (new_number_of_objects > 1 and self._number_of_objects < 2)
            self._number_of_objects = new_number_of_objects
            if recalculate:
                self._onSettingPropertyChanged("print_sequence", "value")  # Create fake event, so right settings are triggered.

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

        if self._error_mesh:
            renderer.queueNode(self, mesh=self._error_mesh, shader=self._shader, transparent=True,
                               backface_cull=True, sort=-8)

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

        # Outline 'cube' of the build volume
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

        self.setMeshData(mb.build())

        mb = MeshBuilder()
        mb.addQuad(
            Vector(min_w, min_h - 0.2, min_d),
            Vector(max_w, min_h - 0.2, min_d),
            Vector(max_w, min_h - 0.2, max_d),
            Vector(min_w, min_h - 0.2, max_d)
        )

        for n in range(0, 6):
            v = mb.getVertex(n)
            mb.setVertexUVCoordinates(n, v[0], v[2])
        self._grid_mesh = mb.build()

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

            self._disallowed_area_mesh = mb.build()
        else:
            self._disallowed_area_mesh = None

        if self._error_areas:
            mb = MeshBuilder()
            for error_area in self._error_areas:
                color = Color(1.0, 0.0, 0.0, 0.5)
                points = error_area.getPoints()
                first = Vector(self._clamp(points[0][0], min_w, max_w), disallowed_area_height,
                               self._clamp(points[0][1], min_d, max_d))
                previous_point = Vector(self._clamp(points[0][0], min_w, max_w), disallowed_area_height,
                                        self._clamp(points[0][1], min_d, max_d))
                for point in points:
                    new_point = Vector(self._clamp(point[0], min_w, max_w), disallowed_area_height,
                                       self._clamp(point[1], min_d, max_d))
                    mb.addFace(first, previous_point, new_point, color=color)
                    previous_point = new_point
            self._error_mesh = mb.build()
        else:
            self._error_mesh = None

        self._volume_aabb = AxisAlignedBox(
            minimum = Vector(min_w, min_h - 1.0, min_d),
            maximum = Vector(max_w, max_h - self._raft_thickness, max_d))

        bed_adhesion_size = self._getEdgeDisallowedSize()

        # As this works better for UM machines, we only add the disallowed_area_size for the z direction.
        # This is probably wrong in all other cases. TODO!
        # The +1 and -1 is added as there is always a bit of extra room required to work properly.
        scale_to_max_bounds = AxisAlignedBox(
            minimum = Vector(min_w + bed_adhesion_size + 1, min_h, min_d + disallowed_area_size - bed_adhesion_size + 1),
            maximum = Vector(max_w - bed_adhesion_size - 1, max_h - self._raft_thickness, max_d - disallowed_area_size + bed_adhesion_size - 1)
        )

        Application.getInstance().getController().getScene()._maximum_bounds = scale_to_max_bounds

    def getBoundingBox(self):
        return self._volume_aabb

    def getRaftThickness(self):
        return self._raft_thickness

    def _updateRaftThickness(self):
        old_raft_thickness = self._raft_thickness
        self._adhesion_type = self._global_container_stack.getProperty("adhesion_type", "value")
        self._raft_thickness = 0.0
        if self._adhesion_type == "raft":
            self._raft_thickness = (
                self._global_container_stack.getProperty("raft_base_thickness", "value") +
                self._global_container_stack.getProperty("raft_interface_thickness", "value") +
                self._global_container_stack.getProperty("raft_surface_layers", "value") *
                    self._global_container_stack.getProperty("raft_surface_thickness", "value") +
                self._global_container_stack.getProperty("raft_airgap", "value"))

        # Rounding errors do not matter, we check if raft_thickness has changed at all
        if old_raft_thickness != self._raft_thickness:
            self.setPosition(Vector(0, -self._raft_thickness, 0), SceneNode.TransformSpace.World)
            self.raftThicknessChanged.emit()

    ##  Update the build volume visualization
    def _onStackChanged(self):
        if self._global_container_stack:
            self._global_container_stack.propertyChanged.disconnect(self._onSettingPropertyChanged)
            extruders = ExtruderManager.getInstance().getMachineExtruders(self._global_container_stack.getId())
            for extruder in extruders:
                extruder.propertyChanged.disconnect(self._onSettingPropertyChanged)

        self._global_container_stack = Application.getInstance().getGlobalContainerStack()

        if self._global_container_stack:
            self._global_container_stack.propertyChanged.connect(self._onSettingPropertyChanged)
            extruders = ExtruderManager.getInstance().getMachineExtruders(self._global_container_stack.getId())
            for extruder in extruders:
                extruder.propertyChanged.connect(self._onSettingPropertyChanged)

            self._width = self._global_container_stack.getProperty("machine_width", "value")
            machine_height = self._global_container_stack.getProperty("machine_height", "value")
            if self._global_container_stack.getProperty("print_sequence", "value") == "one_at_a_time" and self._number_of_objects > 1:
                self._height = min(self._global_container_stack.getProperty("gantry_height", "value"), machine_height)
                if self._height < machine_height:
                    self._build_volume_message.show()
                else:
                    self._build_volume_message.hide()
            else:
                self._height = self._global_container_stack.getProperty("machine_height", "value")
                self._build_volume_message.hide()
            self._depth = self._global_container_stack.getProperty("machine_depth", "value")

            self._updateDisallowedAreas()
            self._updateRaftThickness()

            self.rebuild()

    def _onSettingPropertyChanged(self, setting_key, property_name):
        if property_name != "value":
            return

        rebuild_me = False
        if setting_key == "print_sequence":
            machine_height = self._global_container_stack.getProperty("machine_height", "value")
            if Application.getInstance().getGlobalContainerStack().getProperty("print_sequence", "value") == "one_at_a_time" and self._number_of_objects > 1:
                self._height = min(self._global_container_stack.getProperty("gantry_height", "value"), machine_height)
                if self._height < machine_height:
                    self._build_volume_message.show()
                else:
                    self._build_volume_message.hide()
            else:
                self._height = self._global_container_stack.getProperty("machine_height", "value")
                self._build_volume_message.hide()
            rebuild_me = True

        if setting_key in self._skirt_settings or setting_key in self._prime_settings or setting_key in self._tower_settings or setting_key == "print_sequence" or setting_key in self._ooze_shield_settings or setting_key in self._distance_settings:
            self._updateDisallowedAreas()
            rebuild_me = True

        if setting_key in self._raft_settings:
            self._updateRaftThickness()
            rebuild_me = True

        if rebuild_me:
            self.rebuild()

    def hasErrors(self):
        return self._has_errors

    def _updateDisallowedAreas(self):
        if not self._global_container_stack:
            return

        self._has_errors = False  # Reset.
        self._error_areas = []
        disallowed_areas = copy.deepcopy(
            self._global_container_stack.getProperty("machine_disallowed_areas", "value"))
        areas = []

        machine_width = self._global_container_stack.getProperty("machine_width", "value")
        machine_depth = self._global_container_stack.getProperty("machine_depth", "value")
        prime_tower_area = None

        # Add prime tower location as disallowed area.
        if ExtruderManager.getInstance().getResolveOrValue("prime_tower_enable") == True:
            prime_tower_size = self._global_container_stack.getProperty("prime_tower_size", "value")
            prime_tower_x = self._global_container_stack.getProperty("prime_tower_position_x", "value") - machine_width / 2
            prime_tower_y = - self._global_container_stack.getProperty("prime_tower_position_y", "value") + machine_depth / 2

            prime_tower_area = Polygon([
                [prime_tower_x - prime_tower_size, prime_tower_y - prime_tower_size],
                [prime_tower_x, prime_tower_y - prime_tower_size],
                [prime_tower_x, prime_tower_y],
                [prime_tower_x - prime_tower_size, prime_tower_y],
            ])
        disallowed_polygons = []

        # Check if prime positions intersect with disallowed areas
        prime_collision = False
        if disallowed_areas:
            for area in disallowed_areas:
                poly = Polygon(numpy.array(area, numpy.float32))

                # Minkowski with zero, to ensure that the polygon is correct & watertight.
                poly = poly.getMinkowskiHull(Polygon.approximatedCircle(0))
                disallowed_polygons.append(poly)

            extruder_manager = ExtruderManager.getInstance()
            extruders = extruder_manager.getMachineExtruders(self._global_container_stack.getId())
            prime_polygons = []
            # Each extruder has it's own prime location
            for extruder in extruders:
                prime_x = extruder.getProperty("extruder_prime_pos_x", "value") - machine_width / 2
                prime_y = machine_depth / 2 - extruder.getProperty("extruder_prime_pos_y", "value")

                prime_polygon = Polygon([
                    [prime_x - PRIME_CLEARANCE, prime_y - PRIME_CLEARANCE],
                    [prime_x + PRIME_CLEARANCE, prime_y - PRIME_CLEARANCE],
                    [prime_x + PRIME_CLEARANCE, prime_y + PRIME_CLEARANCE],
                    [prime_x - PRIME_CLEARANCE, prime_y + PRIME_CLEARANCE],
                ])
                prime_polygon = prime_polygon.getMinkowskiHull(Polygon.approximatedCircle(0))
                collision = False

                # Check if prime polygon is intersecting with any of the other disallowed areas.
                # Note that we check the prime area without bed adhesion.
                for poly in disallowed_polygons:
                    if prime_polygon.intersectsPolygon(poly) is not None:
                        collision = True
                        break

                # Also collide with other prime positions
                for poly in prime_polygons:
                    if prime_polygon.intersectsPolygon(poly) is not None:
                        collision = True
                        break

                if not collision:
                    # Prime area is valid. Add as normal.
                    # Once it's added like this, it will recieve a bed adhesion offset, just like the others.
                    prime_polygons.append(prime_polygon)
                else:
                    self._error_areas.append(prime_polygon)
                    prime_collision = collision or prime_collision

            disallowed_polygons.extend(prime_polygons)

        disallowed_border_size = self._getEdgeDisallowedSize()

        # Extend every area already in the disallowed_areas with the skirt size.
        if disallowed_areas:
            for poly in disallowed_polygons:
                poly = poly.getMinkowskiHull(Polygon.approximatedCircle(disallowed_border_size))
                areas.append(poly)

        # Add the skirt areas around the borders of the build plate.
        if disallowed_border_size > 0:
            half_machine_width = self._global_container_stack.getProperty("machine_width", "value") / 2
            half_machine_depth = self._global_container_stack.getProperty("machine_depth", "value") / 2

            areas.append(Polygon(numpy.array([
                [-half_machine_width, -half_machine_depth],
                [-half_machine_width, half_machine_depth],
                [-half_machine_width + disallowed_border_size, half_machine_depth - disallowed_border_size],
                [-half_machine_width + disallowed_border_size, -half_machine_depth + disallowed_border_size]
            ], numpy.float32)))

            areas.append(Polygon(numpy.array([
                [half_machine_width, half_machine_depth],
                [half_machine_width, -half_machine_depth],
                [half_machine_width - disallowed_border_size, -half_machine_depth + disallowed_border_size],
                [half_machine_width - disallowed_border_size, half_machine_depth - disallowed_border_size]
            ], numpy.float32)))

            areas.append(Polygon(numpy.array([
                [-half_machine_width, half_machine_depth],
                [half_machine_width, half_machine_depth],
                [half_machine_width - disallowed_border_size, half_machine_depth - disallowed_border_size],
                [-half_machine_width + disallowed_border_size, half_machine_depth - disallowed_border_size]
            ], numpy.float32)))

            areas.append(Polygon(numpy.array([
                [half_machine_width, -half_machine_depth],
                [-half_machine_width, -half_machine_depth],
                [-half_machine_width + disallowed_border_size, -half_machine_depth + disallowed_border_size],
                [half_machine_width - disallowed_border_size, -half_machine_depth + disallowed_border_size]
            ], numpy.float32)))

        # Check if the prime tower area intersects with any of the other areas.
        # If this is the case, add it to the error area's so it can be drawn in red.
        # If not, add it back to disallowed area's, so it's rendered as normal.
        prime_tower_collision = False
        if prime_tower_area:
            # Using Minkowski of 0 fixes the prime tower area so it's rendered correctly
            prime_tower_area = prime_tower_area.getMinkowskiHull(Polygon.approximatedCircle(0))
            for area in areas:
                if prime_tower_area.intersectsPolygon(area) is not None:
                    prime_tower_collision = True
                    break

            if not prime_tower_collision:
                areas.append(prime_tower_area)
            else:
                self._error_areas.append(prime_tower_area)
        # The buildplate has errors if either prime tower or prime has a colission.
        self._has_errors = prime_tower_collision or prime_collision
        self._disallowed_areas = areas

    ##  Private convenience function to get a setting from the adhesion
    #   extruder.
    #
    #   \param setting_key The key of the setting to get.
    #   \param property The property to get from the setting.
    #   \return The property of the specified setting in the adhesion extruder.
    def _getSettingFromAdhesionExtruder(self, setting_key, property = "value"):
        return self._getSettingFromExtruder(setting_key, "adhesion_extruder_nr", property)

    ##  Private convenience function to get a setting from the support infill
    #   extruder.
    #
    #   \param setting_key The key of the setting to get.
    #   \param property The property to get from the setting.
    #   \return The property of the specified setting in the support infill
    #   extruder.
    def _getSettingFromSupportInfillExtruder(self, setting_key, property = "value"):
        return self._getSettingFromExtruder(setting_key, "support_infill_extruder_nr", property)

    ##  Helper function to get a setting from an extruder specified in another
    #   setting.
    #
    #   \param setting_key The key of the setting to get.
    #   \param extruder_setting_key The key of the setting that specifies from
    #   which extruder to get the setting, if there are multiple extruders.
    #   \param property The property to get from the setting.
    #   \return The property of the specified setting in the specified extruder.
    def _getSettingFromExtruder(self, setting_key, extruder_setting_key, property = "value"):
        multi_extrusion = self._global_container_stack.getProperty("machine_extruder_count", "value") > 1

        if not multi_extrusion:
            return self._global_container_stack.getProperty(setting_key, property)

        extruder_index = self._global_container_stack.getProperty(extruder_setting_key, "value")

        if extruder_index == "-1":  # If extruder index is -1 use global instead
            return self._global_container_stack.getProperty(setting_key, property)

        extruder_stack_id = ExtruderManager.getInstance().extruderIds[str(extruder_index)]
        stack = UM.Settings.ContainerRegistry.getInstance().findContainerStacks(id = extruder_stack_id)[0]
        return stack.getProperty(setting_key, property)

    ##  Convenience function to calculate the disallowed radius around the edge.
    #
    #   This disallowed radius is to allow for space around the models that is
    #   not part of the collision radius, such as bed adhesion (skirt/brim/raft)
    #   and travel avoid distance.
    def _getEdgeDisallowedSize(self):
        if not self._global_container_stack:
            return 0
        container_stack = self._global_container_stack

        # If we are printing one at a time, we need to add the bed adhesion size to the disallowed areas of the objects
        if container_stack.getProperty("print_sequence", "value") == "one_at_a_time":
            return 0.1  # Return a very small value, so we do draw disallowed area's near the edges.

        adhesion_type = container_stack.getProperty("adhesion_type", "value")
        if adhesion_type == "skirt":
            skirt_distance = self._getSettingFromAdhesionExtruder("skirt_gap")
            skirt_line_count = self._getSettingFromAdhesionExtruder("skirt_line_count")
            bed_adhesion_size = skirt_distance + (skirt_line_count * self._getSettingFromAdhesionExtruder("skirt_brim_line_width"))
            if self._global_container_stack.getProperty("machine_extruder_count", "value") > 1:
                adhesion_extruder_nr = int(self._global_container_stack.getProperty("adhesion_extruder_nr", "value"))
                extruder_values = ExtruderManager.getInstance().getAllExtruderValues("skirt_brim_line_width")
                del extruder_values[adhesion_extruder_nr]  # Remove the value of the adhesion extruder nr.
                for value in extruder_values:
                    bed_adhesion_size += value
        elif adhesion_type == "brim":
            bed_adhesion_size = self._getSettingFromAdhesionExtruder("brim_line_count") * self._getSettingFromAdhesionExtruder("skirt_brim_line_width")
            if self._global_container_stack.getProperty("machine_extruder_count", "value") > 1:
                adhesion_extruder_nr = int(self._global_container_stack.getProperty("adhesion_extruder_nr", "value"))
                extruder_values = ExtruderManager.getInstance().getAllExtruderValues("skirt_brim_line_width")
                del extruder_values[adhesion_extruder_nr]  # Remove the value of the adhesion extruder nr.
                for value in extruder_values:
                    bed_adhesion_size += value
        elif adhesion_type == "raft":
            bed_adhesion_size = self._getSettingFromAdhesionExtruder("raft_margin")
        else:
            raise Exception("Unknown bed adhesion type. Did you forget to update the build volume calculations for your new bed adhesion type?")

        support_expansion = 0
        if self._getSettingFromSupportInfillExtruder("support_offset"):
            support_expansion += self._getSettingFromSupportInfillExtruder("support_offset")

        farthest_shield_distance = 0
        if container_stack.getProperty("draft_shield_enabled", "value"):
            farthest_shield_distance = max(farthest_shield_distance, container_stack.getProperty("draft_shield_dist", "value"))
        if container_stack.getProperty("ooze_shield_enabled", "value"):
            farthest_shield_distance = max(farthest_shield_distance, container_stack.getProperty("ooze_shield_dist", "value"))

        move_from_wall_radius = 0  # Moves that start from outer wall.
        if self._getSettingFromAdhesionExtruder("infill_wipe_dist"):
            move_from_wall_radius = max(move_from_wall_radius, self._getSettingFromAdhesionExtruder("infill_wipe_dist"))
        if self._getSettingFromAdhesionExtruder("travel_avoid_distance"):
            move_from_wall_radius = max(move_from_wall_radius, self._getSettingFromAdhesionExtruder("travel_avoid_distance"))

        #Now combine our different pieces of data to get the final border size.
        #Support expansion is added to the bed adhesion, since the bed adhesion goes around support.
        #Support expansion is added to farthest shield distance, since the shields go around support.
        border_size = max(move_from_wall_radius, support_expansion + farthest_shield_distance, support_expansion + bed_adhesion_size)
        return border_size

    def _clamp(self, value, min_value, max_value):
        return max(min(value, max_value), min_value)

    _skirt_settings = ["adhesion_type", "skirt_gap", "skirt_line_count", "skirt_brim_line_width", "brim_width", "brim_line_count", "raft_margin", "draft_shield_enabled", "draft_shield_dist"]
    _raft_settings = ["adhesion_type", "raft_base_thickness", "raft_interface_thickness", "raft_surface_layers", "raft_surface_thickness", "raft_airgap"]
    _prime_settings = ["extruder_prime_pos_x", "extruder_prime_pos_y", "extruder_prime_pos_z"]
    _tower_settings = ["prime_tower_enable", "prime_tower_size", "prime_tower_position_x", "prime_tower_position_y"]
    _ooze_shield_settings = ["ooze_shield_enabled", "ooze_shield_dist"]
    _distance_settings = ["infill_wipe_dist", "travel_avoid_distance", "support_offset"]
