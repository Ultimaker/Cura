# Copyright (c) 2016 Aleph Objects, Inc.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Application import Application
from UM.Logger import Logger
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Math.Vector import Vector
from UM.Mesh.MeshReader import MeshReader
from UM.Message import Message
from UM.Scene.SceneNode import SceneNode
from UM.i18n import i18nCatalog

catalog = i18nCatalog("cura")


from cura import LayerDataBuilder
from cura import LayerDataDecorator
from cura.LayerPolygon import LayerPolygon
from cura.GCodeListDecorator import GCodeListDecorator

import numpy
import math
import re
from collections import namedtuple


# Class for loading and parsing G-code files
class GCodeReader(MeshReader):
    def __init__(self):
        super(GCodeReader, self).__init__()
        self._supported_extensions = [".gcode", ".g"]
        Application.getInstance().hideMessageSignal.connect(self._onHideMessage)
        self._cancelled = False
        self._message = None
        self._clearValues()
        self._scene_node = None
        self._position = namedtuple('Position', ['x', 'y', 'z', 'e'])

    def _clearValues(self):
        self._extruder = 0
        self._layer_type = LayerPolygon.Inset0Type
        self._layer = 0
        self._previous_z = 0
        self._layer_data_builder = LayerDataBuilder.LayerDataBuilder()
        self._center_is_zero = False

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

    def _createPolygon(self, current_z, path):
        countvalid = 0
        for point in path:
            if point[3] > 0:
                countvalid += 1
        if countvalid < 2:
            return False
        try:
            self._layer_data_builder.addLayer(self._layer)
            self._layer_data_builder.setLayerHeight(self._layer, path[0][2])
            self._layer_data_builder.setLayerThickness(self._layer, math.fabs(current_z - self._previous_z))
            this_layer = self._layer_data_builder.getLayer(self._layer)
        except ValueError:
            return False
        count = len(path)
        line_types = numpy.empty((count - 1, 1), numpy.int32)
        line_widths = numpy.empty((count - 1, 1), numpy.float32)
        # TODO: need to calculate actual line width based on E values
        line_widths[:, 0] = 0.4
        points = numpy.empty((count, 3), numpy.float32)
        i = 0
        for point in path:
            points[i, 0] = point[0]
            points[i, 1] = point[2]
            points[i, 2] = -point[1]
            if i > 0:
                line_types[i - 1] = point[3]
                if point[3] in [LayerPolygon.MoveCombingType, LayerPolygon.MoveRetractionType]:
                    line_widths[i - 1] = 0.2
            i += 1

        this_poly = LayerPolygon(self._layer_data_builder, self._extruder, line_types, points, line_widths)
        this_poly.buildCache()

        this_layer.polygons.append(this_poly)
        return True

    def _gCode0(self, position, params, path):
        x, y, z, e = position
        x = params.x if params.x is not None else x
        y = params.y if params.y is not None else y
        z_changed = False
        if params.z is not None:
            if z != params.z:
                z_changed = True
                self._previous_z = z
            z = params.z
        if params.e is not None:
            if params.e > e[self._extruder]:
                path.append([x, y, z, self._layer_type])  # extrusion
            else:
                path.append([x, y, z, LayerPolygon.MoveRetractionType])  # retraction
            e[self._extruder] = params.e
        else:
            path.append([x, y, z, LayerPolygon.MoveCombingType])
        if z_changed:
            if not self._is_layers_in_file:
                if len(path) > 1 and z > 0:
                    if self._createPolygon(z, path):
                        self._layer += 1
                    path.clear()
                else:
                    path.clear()
        return self._position(x, y, z, e)

    def _gCode28(self, position, params, path):
        return self._position(
            params.x if params.x is not None else position.x,
            params.y if params.y is not None else position.y,
            0,
            position.e)

    def _gCode92(self, position, params, path):
        if params.e is not None:
            position.e[self._extruder] = params.e
        return self._position(
            params.x if params.x is not None else position.x,
            params.y if params.y is not None else position.y,
            params.z if params.z is not None else position.z,
            position.e)

    _gCode1 = _gCode0

    def _processGCode(self, G, line, position, path):
        func = getattr(self, "_gCode%s" % G, None)
        x = self._getFloat(line, "X")
        y = self._getFloat(line, "Y")
        z = self._getFloat(line, "Z")
        e = self._getFloat(line, "E")
        if func is not None:
            if (x is not None and x < 0) or (y is not None and y < 0):
                self._center_is_zero = True
            params = self._position(x, y, z, e)
            return func(position, params, path)
        return position

    def _processTCode(self, T, line, position, path):
        self._extruder = T
        if self._extruder + 1 > len(position.e):
            position.e.extend([0] * (self._extruder - len(position.e) + 1))
        if not self._is_layers_in_file:
            if len(path) > 1 and position[2] > 0:
                if self._createPolygon(position[2], path):
                    self._layer += 1
                path.clear()
            else:
                path.clear()
        return position

    _type_keyword = ";TYPE:"
    _layer_keyword = ";LAYER:"

    def read(self, file_name):
        Logger.log("d", "Preparing to load %s" % file_name)
        self._cancelled = False

        scene_node = SceneNode()
        scene_node.getBoundingBox = self._getNullBoundingBox  # Manually set bounding box, because mesh doesn't have mesh data

        glist = []
        self._is_layers_in_file = False


        Logger.log("d", "Opening file %s" % file_name)

        with open(file_name, "r") as file:
            file_lines = 0
            current_line = 0
            for line in file:
                file_lines += 1
                glist.append(line)
                if not self._is_layers_in_file and line[:len(self._layer_keyword)] == self._layer_keyword:
                    self._is_layers_in_file = True
            file.seek(0)

            file_step = max(math.floor(file_lines / 100), 1)

            self._clearValues()

            self._message = Message(catalog.i18nc("@info:status", "Parsing G-code"), lifetime=0)
            self._message.setProgress(0)
            self._message.show()

            Logger.log("d", "Parsing %s" % file_name)

            current_position = self._position(0, 0, 0, [0])
            current_path = []

            for line in file:
                if self._cancelled:
                    Logger.log("d", "Parsing %s cancelled" % file_name)
                    return None
                current_line += 1
                if current_line % file_step == 0:
                    self._message.setProgress(math.floor(current_line / file_lines * 100))
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
                if self._is_layers_in_file and line[:len(self._layer_keyword)] == self._layer_keyword:
                    try:
                        layer_number = int(line[len(self._layer_keyword):])
                        self._createPolygon(current_position[2], current_path)
                        current_path.clear()
                        self._layer = layer_number
                    except:
                        pass
                if line[0] == ";":
                    continue

                G = self._getInt(line, "G")
                if G is not None:
                    current_position = self._processGCode(G, line, current_position, current_path)
                T = self._getInt(line, "T")
                if T is not None:
                    current_position = self._processTCode(T, line, current_position, current_path)

            if not self._is_layers_in_file and len(current_path) > 1 and current_position[2] > 0:
                if self._createPolygon(current_position[2], current_path):
                    self._layer += 1
                current_path.clear()

        layer_mesh = self._layer_data_builder.build()
        decorator = LayerDataDecorator.LayerDataDecorator()
        decorator.setLayerData(layer_mesh)
        scene_node.addDecorator(decorator)

        gcode_list_decorator = GCodeListDecorator()
        gcode_list_decorator.setGCodeList(glist)
        scene_node.addDecorator(gcode_list_decorator)

        Logger.log("d", "Finished parsing %s" % file_name)
        self._message.hide()

        if self._layer == 0:
            Logger.log("w", "File %s doesn't contain any valid layers" % file_name)

        settings = Application.getInstance().getGlobalContainerStack()
        machine_width = settings.getProperty("machine_width", "value")
        machine_depth = settings.getProperty("machine_depth", "value")

        if not self._center_is_zero:
            scene_node.setPosition(Vector(-machine_width / 2, 0, machine_depth / 2))

        Logger.log("d", "Loaded %s" % file_name)

        return scene_node
