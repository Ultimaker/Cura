# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Application import Application
from UM.Backend import Backend
from UM.Job import Job
from UM.Logger import Logger
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Math.Vector import Vector
from UM.Message import Message
from UM.Scene.SceneNode import SceneNode
from UM.i18n import i18nCatalog
from UM.Preferences import Preferences

catalog = i18nCatalog("cura")

from cura import LayerDataBuilder
from cura import LayerDataDecorator
from cura.LayerPolygon import LayerPolygon
from cura.GCodeListDecorator import GCodeListDecorator
from cura.Settings.ExtruderManager import ExtruderManager

import numpy
import math
import re
from collections import namedtuple

# This parser is intented for interpret the common firmware codes among all the different flavors
class FlavorParser:

    def __init__(self):
        Application.getInstance().hideMessageSignal.connect(self._onHideMessage)
        self._cancelled = False
        self._message = None
        self._layer_number = 0
        self._extruder_number = 0
        self._clearValues()
        self._scene_node = None
        # X, Y, Z position, F feedrate and E extruder values are stored
        self._position = namedtuple('Position', ['x', 'y', 'z', 'f', 'e'])
        self._is_layers_in_file = False  # Does the Gcode have the layers comment?
        self._extruder_offsets = {}  # Offsets for multi extruders. key is index, value is [x-offset, y-offset]
        self._current_layer_thickness = 0.2  # default

        Preferences.getInstance().addPreference("gcodereader/show_caution", True)

    def _clearValues(self):
        self._filament_diameter = 2.85
        self._extruder_number = 0
        self._extrusion_length_offset = [0]
        self._layer_type = LayerPolygon.Inset0Type
        self._layer_number = 0
        self._previous_z = 0
        self._layer_data_builder = LayerDataBuilder.LayerDataBuilder()
        self._center_is_zero = False
        self._is_absolute_positioning = True    # It can be absolute (G90) or relative (G91)
        self._is_absolute_extrusion = True  # It can become absolute (M82, default) or relative (M83)

    @staticmethod
    def _getValue(line, code):
        n = line.find(code)
        if n < 0:
            return None
        n += len(code)
        pattern = re.compile("[;\s]")
        match = pattern.search(line, n)
        m = match.start() if match is not None else -1
        try:
            if m < 0:
                return line[n:]
            return line[n:m]
        except:
            return None

    def _getInt(self, line, code):
        value = self._getValue(line, code)
        try:
            return int(value)
        except:
            return None

    def _getFloat(self, line, code):
        value = self._getValue(line, code)
        try:
            return float(value)
        except:
            return None

    def _onHideMessage(self, message):
        if message == self._message:
            self._cancelled = True

    @staticmethod
    def _getNullBoundingBox():
        return AxisAlignedBox(minimum=Vector(0, 0, 0), maximum=Vector(10, 10, 10))

    def _createPolygon(self, layer_thickness, path, extruder_offsets):
        countvalid = 0
        for point in path:
            if point[5] > 0:
                countvalid += 1
                if countvalid >= 2:
                    # we know what to do now, no need to count further
                    continue
        if countvalid < 2:
            return False
        try:
            self._layer_data_builder.addLayer(self._layer_number)
            self._layer_data_builder.setLayerHeight(self._layer_number, path[0][2])
            self._layer_data_builder.setLayerThickness(self._layer_number, layer_thickness)
            this_layer = self._layer_data_builder.getLayer(self._layer_number)
        except ValueError:
            return False
        count = len(path)
        line_types = numpy.empty((count - 1, 1), numpy.int32)
        line_widths = numpy.empty((count - 1, 1), numpy.float32)
        line_thicknesses = numpy.empty((count - 1, 1), numpy.float32)
        line_feedrates = numpy.empty((count - 1, 1), numpy.float32)
        line_widths[:, 0] = 0.35  # Just a guess
        line_thicknesses[:, 0] = layer_thickness
        points = numpy.empty((count, 3), numpy.float32)
        extrusion_values = numpy.empty((count, 1), numpy.float32)
        i = 0
        for point in path:
            points[i, :] = [point[0] + extruder_offsets[0], point[2], -point[1] - extruder_offsets[1]]
            extrusion_values[i] = point[4]
            if i > 0:
                line_feedrates[i - 1] = point[3]
                line_types[i - 1] = point[5]
                if point[5] in [LayerPolygon.MoveCombingType, LayerPolygon.MoveRetractionType]:
                    line_widths[i - 1] = 0.1
                    line_thicknesses[i - 1] = 0.0 # Travels are set as zero thickness lines
                else:
                    line_widths[i - 1] = self._calculateLineWidth(points[i], points[i-1], extrusion_values[i], extrusion_values[i-1], layer_thickness)
            i += 1

        this_poly = LayerPolygon(self._extruder_number, line_types, points, line_widths, line_thicknesses, line_feedrates)
        this_poly.buildCache()

        this_layer.polygons.append(this_poly)
        return True

    def _createEmptyLayer(self, layer_number):
        self._layer_data_builder.addLayer(layer_number)
        self._layer_data_builder.setLayerHeight(layer_number, 0)
        self._layer_data_builder.setLayerThickness(layer_number, 0)

    def _calculateLineWidth(self, current_point, previous_point, current_extrusion, previous_extrusion, layer_thickness):
        # Area of the filament
        Af = (self._filament_diameter / 2) ** 2 * numpy.pi
        # Length of the extruded filament
        de = current_extrusion - previous_extrusion
        # Volumne of the extruded filament
        dVe = de * Af
        # Length of the printed line
        dX = numpy.sqrt((current_point[0] - previous_point[0])**2 + (current_point[2] - previous_point[2])**2)
        # When the extruder recovers from a retraction, we get zero distance
        if dX == 0:
            return 0.1
        # Area of the printed line. This area is a rectangle
        Ae = dVe / dX
        # This area is a rectangle with area equal to layer_thickness * layer_width
        line_width = Ae / layer_thickness

        # A threshold is set to avoid weird paths in the GCode
        if line_width > 1.2:
            return 0.35
        return line_width

    def _gCode0(self, position, params, path):
        x, y, z, f, e = position

        if self._is_absolute_positioning:
            x = params.x if params.x is not None else x
            y = params.y if params.y is not None else y
            z = params.z if params.z is not None else z
        else:
            x += params.x if params.x is not None else 0
            y += params.y if params.y is not None else 0
            z += params.z if params.z is not None else 0

        f = params.f if params.f is not None else f

        if params.e is not None:
            new_extrusion_value = params.e if self._is_absolute_extrusion else e[self._extruder_number] + params.e
            if new_extrusion_value > e[self._extruder_number]:
                path.append([x, y, z, f, new_extrusion_value + self._extrusion_length_offset[self._extruder_number], self._layer_type])  # extrusion
            else:
                path.append([x, y, z, f, new_extrusion_value + self._extrusion_length_offset[self._extruder_number], LayerPolygon.MoveRetractionType])  # retraction
            e[self._extruder_number] = new_extrusion_value

            # Only when extruding we can determine the latest known "layer height" which is the difference in height between extrusions
            # Also, 1.5 is a heuristic for any priming or whatsoever, we skip those.
            if z > self._previous_z and (z - self._previous_z < 1.5):
                self._current_layer_thickness = z - self._previous_z # allow a tiny overlap
                self._previous_z = z
        else:
            path.append([x, y, z, f, e[self._extruder_number] + self._extrusion_length_offset[self._extruder_number], LayerPolygon.MoveCombingType])
        return self._position(x, y, z, f, e)


    # G0 and G1 should be handled exactly the same.
    _gCode1 = _gCode0

    ##  Home the head.
    def _gCode28(self, position, params, path):
        return self._position(
            params.x if params.x is not None else position.x,
            params.y if params.y is not None else position.y,
            params.z if params.z is not None else position.z,
            position.f,
            position.e)

    ##  Set the absolute positioning
    def _gCode90(self, position, params, path):
        self._is_absolute_positioning = True
        self._is_absolute_extrusion = True
        return position

    ##  Set the relative positioning
    def _gCode91(self, position, params, path):
        self._is_absolute_positioning = False
        self._is_absolute_extrusion = False
        return position

    ##  Reset the current position to the values specified.
    #   For example: G92 X10 will set the X to 10 without any physical motion.
    def _gCode92(self, position, params, path):
        if params.e is not None:
            # Sometimes a G92 E0 is introduced in the middle of the GCode so we need to keep those offsets for calculate the line_width
            self._extrusion_length_offset[self._extruder_number] += position.e[self._extruder_number] - params.e
            position.e[self._extruder_number] = params.e
        return self._position(
            params.x if params.x is not None else position.x,
            params.y if params.y is not None else position.y,
            params.z if params.z is not None else position.z,
            params.f if params.f is not None else position.f,
            position.e)

    def processGCode(self, G, line, position, path):
        func = getattr(self, "_gCode%s" % G, None)
        line = line.split(";", 1)[0]  # Remove comments (if any)
        if func is not None:
            s = line.upper().split(" ")
            x, y, z, f, e = None, None, None, None, None
            for item in s[1:]:
                if len(item) <= 1:
                    continue
                if item.startswith(";"):
                    continue
                if item[0] == "X":
                    x = float(item[1:])
                if item[0] == "Y":
                    y = float(item[1:])
                if item[0] == "Z":
                    z = float(item[1:])
                if item[0] == "F":
                    f = float(item[1:]) / 60
                if item[0] == "E":
                    e = float(item[1:])
            if self._is_absolute_positioning and ((x is not None and x < 0) or (y is not None and y < 0)):
                self._center_is_zero = True
            params = self._position(x, y, z, f, e)
            return func(position, params, path)
        return position

    def processTCode(self, T, line, position, path):
        self._extruder_number = T
        if self._extruder_number + 1 > len(position.e):
            self._extrusion_length_offset.extend([0] * (self._extruder_number - len(position.e) + 1))
            position.e.extend([0] * (self._extruder_number - len(position.e) + 1))
        return position

    def processMCode(self, M, line, position, path):
        pass

    _type_keyword = ";TYPE:"
    _layer_keyword = ";LAYER:"

    ##  For showing correct x, y offsets for each extruder
    def _extruderOffsets(self):
        result = {}
        for extruder in ExtruderManager.getInstance().getExtruderStacks():
            result[int(extruder.getMetaData().get("position", "0"))] = [
                extruder.getProperty("machine_nozzle_offset_x", "value"),
                extruder.getProperty("machine_nozzle_offset_y", "value")]
        return result

    def processGCodeFile(self, file_name):
        Logger.log("d", "Preparing to load %s" % file_name)
        self._cancelled = False
        # We obtain the filament diameter from the selected printer to calculate line widths
        self._filament_diameter = Application.getInstance().getGlobalContainerStack().getProperty("material_diameter", "value")

        scene_node = SceneNode()
        # Override getBoundingBox function of the sceneNode, as this node should return a bounding box, but there is no
        # real data to calculate it from.
        scene_node.getBoundingBox = self._getNullBoundingBox

        gcode_list = []
        self._is_layers_in_file = False

        Logger.log("d", "Opening file %s" % file_name)

        self._extruder_offsets = self._extruderOffsets()  # dict with index the extruder number. can be empty

        with open(file_name, "r") as file:
            file_lines = 0
            current_line = 0
            for line in file:
                file_lines += 1
                gcode_list.append(line)
                if not self._is_layers_in_file and line[:len(self._layer_keyword)] == self._layer_keyword:
                    self._is_layers_in_file = True
            file.seek(0)

            file_step = max(math.floor(file_lines / 100), 1)

            self._clearValues()

            self._message = Message(catalog.i18nc("@info:status", "Parsing G-code"),
                                    lifetime=0,
                                    title = catalog.i18nc("@info:title", "G-code Details"))

            self._message.setProgress(0)
            self._message.show()

            Logger.log("d", "Parsing %s..." % file_name)

            current_position = self._position(0, 0, 0, 0, [0])
            current_path = []
            min_layer_number = 0
            negative_layers = 0
            previous_layer = 0

            for line in file:
                if self._cancelled:
                    Logger.log("d", "Parsing %s cancelled" % file_name)
                    return None
                current_line += 1

                if current_line % file_step == 0:
                    self._message.setProgress(math.floor(current_line / file_lines * 100))
                    Job.yieldThread()
                if len(line) == 0:
                    continue

                if line.find(self._type_keyword) == 0:
                    type = line[len(self._type_keyword):].strip()
                    if type == "WALL-INNER":
                        self._layer_type = LayerPolygon.InsetXType
                    elif type == "WALL-OUTER":
                        self._layer_type = LayerPolygon.Inset0Type
                    elif type == "SKIN":
                        self._layer_type = LayerPolygon.SkinType
                    elif type == "SKIRT":
                        self._layer_type = LayerPolygon.SkirtType
                    elif type == "SUPPORT":
                        self._layer_type = LayerPolygon.SupportType
                    elif type == "FILL":
                        self._layer_type = LayerPolygon.InfillType
                    else:
                        Logger.log("w", "Encountered a unknown type (%s) while parsing g-code.", type)

                # When the layer change is reached, the polygon is computed so we have just one layer per layer per extruder
                if self._is_layers_in_file and line[:len(self._layer_keyword)] == self._layer_keyword:
                    try:
                        layer_number = int(line[len(self._layer_keyword):])
                        self._createPolygon(self._current_layer_thickness, current_path, self._extruder_offsets.get(self._extruder_number, [0, 0]))
                        current_path.clear()

                        # When using a raft, the raft layers are stored as layers < 0, it mimics the same behavior
                        # as in ProcessSlicedLayersJob
                        if layer_number < min_layer_number:
                            min_layer_number = layer_number
                        if layer_number < 0:
                            layer_number += abs(min_layer_number)
                            negative_layers += 1
                        else:
                            layer_number += negative_layers

                        # In case there is a gap in the layer count, empty layers are created
                        for empty_layer in range(previous_layer + 1, layer_number):
                            self._createEmptyLayer(empty_layer)

                        self._layer_number = layer_number
                        previous_layer = layer_number
                    except:
                        pass

                # This line is a comment. Ignore it (except for the layer_keyword)
                if line.startswith(";"):
                    continue

                G = self._getInt(line, "G")
                if G is not None:
                    # When find a movement, the new posistion is calculated and added to the current_path, but
                    # don't need to create a polygon until the end of the layer
                    current_position = self.processGCode(G, line, current_position, current_path)
                    continue

                # When changing the extruder, the polygon with the stored paths is computed
                if line.startswith("T"):
                    T = self._getInt(line, "T")
                    if T is not None:
                        self._createPolygon(self._current_layer_thickness, current_path, self._extruder_offsets.get(self._extruder_number, [0, 0]))
                        current_path.clear()

                        current_position = self.processTCode(T, line, current_position, current_path)

                if line.startswith("M"):
                    M = self._getInt(line, "M")
                    self.processMCode(M, line, current_position, current_path)

            # "Flush" leftovers. Last layer paths are still stored
            if len(current_path) > 1:
                if self._createPolygon(self._current_layer_thickness, current_path, self._extruder_offsets.get(self._extruder_number, [0, 0])):
                    self._layer_number += 1
                    current_path.clear()

        material_color_map = numpy.zeros((10, 4), dtype = numpy.float32)
        material_color_map[0, :] = [0.0, 0.7, 0.9, 1.0]
        material_color_map[1, :] = [0.7, 0.9, 0.0, 1.0]
        layer_mesh = self._layer_data_builder.build(material_color_map)
        decorator = LayerDataDecorator.LayerDataDecorator()
        decorator.setLayerData(layer_mesh)
        scene_node.addDecorator(decorator)

        gcode_list_decorator = GCodeListDecorator()
        gcode_list_decorator.setGCodeList(gcode_list)
        scene_node.addDecorator(gcode_list_decorator)

        Application.getInstance().getController().getScene().gcode_list = gcode_list

        Logger.log("d", "Finished parsing %s" % file_name)
        self._message.hide()

        if self._layer_number == 0:
            Logger.log("w", "File %s doesn't contain any valid layers" % file_name)

        settings = Application.getInstance().getGlobalContainerStack()
        machine_width = settings.getProperty("machine_width", "value")
        machine_depth = settings.getProperty("machine_depth", "value")

        if not self._center_is_zero:
            scene_node.setPosition(Vector(-machine_width / 2, 0, machine_depth / 2))

        Logger.log("d", "Loaded %s" % file_name)

        if Preferences.getInstance().getValue("gcodereader/show_caution"):
            caution_message = Message(catalog.i18nc(
                "@info:generic",
                "Make sure the g-code is suitable for your printer and printer configuration before sending the file to it. The g-code representation may not be accurate."),
                lifetime=0,
                title = catalog.i18nc("@info:title", "G-code Details"))
            caution_message.show()

        # The "save/print" button's state is bound to the backend state.
        backend = Application.getInstance().getBackend()
        backend.backendStateChange.emit(Backend.BackendState.Disabled)

        return scene_node
