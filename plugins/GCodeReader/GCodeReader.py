# Copyright (c) 2016 Aleph Objects, Inc.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshReader import MeshReader
import os
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Math.Vector import Vector
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Application import Application
from UM.Message import Message
from UM.Logger import Logger
from UM.Backend.Backend import BackendState

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


from cura import LayerDataBuilder
from cura import LayerDataDecorator
from cura.LayerPolygon import LayerPolygon
from UM.Scene.SliceableObjectDecorator import SliceableObjectDecorator

import numpy
import math
import re


# Class for loading and parsing G-code files
class GCodeReader(MeshReader):
    def __init__(self):
        super(GCodeReader, self).__init__()
        self._supported_extensions = [".gcode", ".g"]
        Application.getInstance().hideMessageSignal.connect(self._onHideMessage)
        self._cancelled = False
        self._message = None

    @staticmethod
    def _getValue(line, code):
        n = line.find(code) + len(code)
        if n < 1:
            return None
        pattern = re.compile("[;\s]")
        match = pattern.search(line, n)
        m = match.start() if math is not None else -1
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

    @staticmethod
    def _createPolygon(layer_data, path, layer_id, extruder, thickness):
        countvalid = 0
        for point in path:
            if point[3] > 0:
                countvalid += 1
        if countvalid < 2:
            return False
        try:
            layer_data.addLayer(layer_id)
            layer_data.setLayerHeight(layer_id, path[0][1])
            layer_data.setLayerThickness(layer_id, thickness)
            this_layer = layer_data.getLayer(layer_id)
        except ValueError:
            return False
        count = len(path)
        line_types = numpy.empty((count - 1, 1), numpy.int32)
        line_widths = numpy.empty((count - 1, 1), numpy.float32)
        # TODO: need to calculate actual line width based on E values
        line_widths[:, 0] = 0.5
        points = numpy.empty((count, 3), numpy.float32)
        i = 0
        for point in path:
            points[i, 0] = point[0]
            points[i, 1] = point[2]
            points[i, 2] = -point[1]
            if i > 0:
                line_types[i - 1] = point[3]
            i += 1

        this_poly = LayerPolygon(layer_data, extruder, line_types, points, line_widths)
        this_poly.buildCache()

        this_layer.polygons.append(this_poly)
        return True

    def read(self, file_name):
        Logger.log("d", "Preparing to load %s" % file_name)
        self._cancelled = False

        scene_node = SceneNode()
        scene_node.getBoundingBox = self._getNullBoundingBox  # Manually set bounding box, because mesh doesn't have mesh data

        glist = []
        Application.getInstance().getController().getScene().gcode_list = glist

        Logger.log("d", "Opening file %s" % file_name)

        layer_data_builder = LayerDataBuilder.LayerDataBuilder()

        with open(file_name, "r") as file:
            file_lines = 0
            current_line = 0
            for line in file:
                file_lines += 1
            file.seek(0)

            file_step = max(math.floor(file_lines / 100), 1)

            current_extruder = 0
            current_path = []
            current_x = 0
            current_y = 0
            current_z = 0
            current_e = 0
            current_block = LayerPolygon.Inset0Type
            current_layer = 0
            prev_z = 0
            center_is_zero = False

            self._message = Message(catalog.i18nc("@info:status", "Parsing GCODE"), lifetime=0)
            self._message.setProgress(0)
            self._message.show()

            Logger.log("d", "Parsing %s" % file_name)

            for line in file:
                if self._cancelled:
                    Logger.log("w", "Parsing %s cancelled" % file_name)
                    return None
                current_line += 1
                if current_line % file_step == 0:
                    self._message.setProgress(math.floor(current_line / file_lines * 100))
                if len(line) == 0:
                    continue
                if line.find(";TYPE:") == 0:
                    type = line[6:].strip()
                    if type == "WALL-INNER":
                        current_block = LayerPolygon.InsetXType
                    elif type == "WALL-OUTER":
                        current_block = LayerPolygon.Inset0Type
                    elif type == "SKIN":
                        current_block = LayerPolygon.SkinType
                    elif type == "SKIRT":
                        current_block = LayerPolygon.SkirtType
                    elif type == "SUPPORT":
                        current_block = LayerPolygon.SupportType
                    elif type == "FILL":
                        current_block = LayerPolygon.InfillType
                if line[0] == ";":
                    continue
                G = self._getInt(line, "G")
                x = self._getFloat(line, "X")
                y = self._getFloat(line, "Y")
                z = self._getFloat(line, "Z")
                if x is not None and x < 0:
                    center_is_zero = True
                if y is not None and y < 0:
                    center_is_zero = True
                if G is not None:
                    if G == 0 or G == 1:
                        e = self._getFloat(line, "E")
                        z_changed = False
                        if x is not None:
                            current_x = x
                        if y is not None:
                            current_y = y
                        if z is not None:
                            if not current_z == z:
                                z_changed = True
                                prev_z = current_z
                            current_z = z
                        if e is not None:
                            if e > current_e:
                                current_path.append([current_x, current_y, current_z, current_block])  # extrusion
                            else:
                                current_path.append([current_x, current_y, current_z, LayerPolygon.MoveRetractionType])  # retraction
                            current_e = e
                        else:
                            current_path.append([current_x, current_y, current_z, LayerPolygon.MoveCombingType])
                        if z_changed:
                            if len(current_path) > 1 and current_z > 0:
                                if self._createPolygon(layer_data_builder, current_path, current_layer, current_extruder, math.fabs(current_z - prev_z)):
                                    current_layer += 1
                                current_path.clear()
                            else:
                                current_path.clear()

                    elif G == 28:
                        if x is not None:
                            current_x = x
                        if y is not None:
                            current_y = y
                        current_z = 0
                    elif G == 92:
                        e = self._getFloat(line, "E")
                        if x is not None:
                            current_x = x
                        if y is not None:
                            current_y = y
                        if z is not None:
                            current_z = z
                        if e is not None:
                            current_e = e

                T = self._getInt(line, "T")
                if T is not None:
                    current_extruder = T
                    if len(current_path) > 1 and current_z > 0:
                        if self._createPolygon(layer_data_builder, current_path, current_layer, current_extruder, math.fabs(current_z - prev_z)):
                            current_layer += 1
                        current_path.clear()
                    else:
                        current_path.clear()

            if len(current_path) > 1 and current_z > 0:
                if self._createPolygon(layer_data_builder, current_path, current_layer, current_extruder, math.fabs(current_z - prev_z)):
                    current_layer += 1
                current_path.clear()

        layer_mesh = layer_data_builder.build()
        decorator = LayerDataDecorator.LayerDataDecorator()
        decorator.setLayerData(layer_mesh)
        scene_node.addDecorator(decorator)

        sliceable_decorator = SliceableObjectDecorator()
        sliceable_decorator.setBlockSlicing(True)
        sliceable_decorator.setSliceable(False)
        scene_node.addDecorator(sliceable_decorator)

        Logger.log("d", "Finished parsing %s" % file_name)
        self._message.hide()

        if current_layer == 0:
            Logger.log("w", "File %s doesn't contain any valid layers" % file_name)

        settings = Application.getInstance().getGlobalContainerStack()
        machine_width = settings.getProperty("machine_width", "value")
        machine_depth = settings.getProperty("machine_depth", "value")

        if not center_is_zero:
            scene_node.setPosition(Vector(-machine_width / 2, 0, machine_depth / 2))

        Logger.log("d", "Loaded %s" % file_name)

        return scene_node
