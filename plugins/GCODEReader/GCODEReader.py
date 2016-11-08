# Copyright (c) 2015 Ultimaker B.V.
# Copyright (c) 2013 David Braam
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshReader import MeshReader
import os
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Math.Vector import Vector
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Application import Application
from UM.Message import Message
from UM.Logger import Logger

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


from cura import LayerDataBuilder
from cura import LayerDataDecorator
from cura import LayerPolygon

import numpy
import math


class GCODEReader(MeshReader):
    def __init__(self):
        super(GCODEReader, self).__init__()
        self._supported_extensions = [".gcode", ".g"]
        Application.getInstance().hideMessageSignal.connect(self.onHideMessage)
        self.cancelled = False
        self.message = None

    def getInt(self, line, code):
        n = line.find(code) + 1
        if n < 1:
            return None
        m = line.find(' ', n)
        try:
            if m < 0:
                return int(line[n:])
            return int(line[n:m])
        except:
            return None

    def getFloat(self, line, code):
        n = line.find(code) + 1
        if n < 1:
            return None
        m = line.find(' ', n)
        try:
            if m < 0:
                return float(line[n:])
            return float(line[n:m])
        except:
            return None

    def onHideMessage(self, m):
        if m == self.message:
            self.cancelled = True

    def parent_changed(self, node):
        if node.getParent() is None:
            scene = Application.getInstance().getController().getScene()

            def findAny():
                for node1 in DepthFirstIterator(scene.getRoot()):
                    if hasattr(node1, "gcode") and getattr(node1, "gcode") is True:
                        return True
                return False

            backend = Application.getInstance().getBackend()
            if not findAny():
                backend._pauseSlicing = False
                Application.getInstance().setHideSettings(False)
                Application.getInstance().getPrintInformation().setPreSliced(False)
            else:
                backend._pauseSlicing = True
                backend.backendStateChange.emit(3)
                Application.getInstance().getPrintInformation().setPreSliced(True)
                Application.getInstance().setHideSettings(True)

    def read(self, file_name):
        scene_node = None

        extension = os.path.splitext(file_name)[1]
        if extension.lower() in self._supported_extensions:
            Logger.log("d", "Preparing to load %s" % file_name)
            self.cancelled = False
            Application.getInstance().deleteAll()

            scene_node = SceneNode()

            def getBoundingBox():
                return AxisAlignedBox(minimum=Vector(0, 0, 0), maximum=Vector(10, 10, 10))

            scene_node.getBoundingBox = getBoundingBox
            scene_node.gcode = True
            backend = Application.getInstance().getBackend()
            backend._pauseSlicing = True
            backend.close()
            backend.backendStateChange.emit(1)

            glist = getattr(Application.getInstance().getController().getScene(), "gcode_list")
            glist.clear()

            Logger.log("d", "Opening file %s" % file_name)

            file = open(file_name, "r")

            file_lines = 0
            current_line = 0
            for line in file:
                file_lines += 1
            file.seek(0)

            file_step = math.floor(file_lines / 100)
            file_step = 1 if file_step < 1 else file_step

            layer_data = LayerDataBuilder.LayerDataBuilder()

            current_extruder = 1
            current_path = []
            current_x = 0
            current_y = 0
            current_z = 0
            current_e = 0
            current_layer = 0

            self.message = Message(catalog.i18nc("@info:status", "Parsing GCODE"), lifetime=0)
            self.message.setProgress(0)
            self.message.show()

            Logger.log("d", "Parsing %s" % file_name)

            def CreatePolygon():
                countvalid = False
                for point in current_path:
                    if point[3] > 0:
                        countvalid += 1
                if countvalid < 2:
                    current_path.clear()
                    return False
                try:
                    layer_data.addLayer(current_layer)
                    layer_data.setLayerHeight(current_layer, current_path[0][1])
                    layer_data.setLayerThickness(current_layer, 0.25)
                    this_layer = layer_data.getLayer(current_layer)
                except ValueError:
                    current_path.clear()
                    return False
                count = len(current_path)
                line_types = numpy.empty((count-1, 1), numpy.int32)
                line_types[:, 0] = 1
                line_widths = numpy.empty((count-1, 1), numpy.int32)
                line_widths[:, 0] = 0.5
                points = numpy.empty((count, 3), numpy.float32)
                i = 0
                for point in current_path:
                    points[i, 0] = point[0]
                    points[i, 1] = point[1]
                    points[i, 2] = point[2]
                    if i > 0:
                        line_types[i-1] = point[3]
                    i += 1

                this_poly = LayerPolygon.LayerPolygon(layer_data, current_extruder, line_types, points, line_widths)
                this_poly.buildCache()

                this_layer.polygons.append(this_poly)

                current_path.clear()
                return True

            for line in file:
                if self.cancelled:
                    Logger.log("w", "Parsing %s cancelled" % file_name)
                    return None
                current_line += 1
                if current_line % file_step == 0:
                    self.message.setProgress(math.floor(current_line/file_lines*100))
                if len(line) == 0:
                    continue
                if line[0] == ";":
                    continue
                G = self.getInt(line, "G")
                if G is not None:
                    if G == 0 or G == 1:
                        x = self.getFloat(line, "X")
                        y = self.getFloat(line, "Y")
                        z = self.getFloat(line, "Z")
                        e = self.getFloat(line, "E")
                        z_changed = False
                        if x is not None:
                            current_x = x
                        if y is not None:
                            current_y = y
                        if z is not None:
                            if not current_z == z:
                                z_changed = True
                            current_z = z
                        if e is not None:
                            if e > current_e:
                                current_path.append([current_x, current_z, -current_y, 1])  # extrusion
                            else:
                                current_path.append([current_x, current_z, -current_y, 2])  # retraction
                            current_e = e
                        else:
                            current_path.append([current_x, current_z, -current_y, 0])
                        if z_changed:
                            if len(current_path) > 1 and current_z > 0:
                                if CreatePolygon():
                                    current_layer += 1
                            else:
                                current_path.clear()

                    elif G == 28:
                        x = self.getFloat(line, "X")
                        y = self.getFloat(line, "Y")
                        if x is not None:
                            current_x = x
                        if y is not None:
                            current_y = y
                        current_z = 0
                    elif G == 92:
                        x = self.getFloat(line, "X")
                        y = self.getFloat(line, "Y")
                        z = self.getFloat(line, "Z")
                        if x is not None:
                            current_x += x
                        if y is not None:
                            current_y += y
                        if z is not None:
                            current_z += z

            if len(current_path) > 1:
                if CreatePolygon():
                    current_layer += 1

            layer_mesh = layer_data.build()
            decorator = LayerDataDecorator.LayerDataDecorator()
            decorator.setLayerData(layer_mesh)
            scene_node.addDecorator(decorator)

            Logger.log("d", "Finished parsing %s" % file_name)
            self.message.hide()

            if current_layer == 0:
                Logger.log("w", "File %s doesn't contain any valid layers" % file_name)

            Application.getInstance().getPrintInformation()._pre_sliced = True

            scene_node.parentChanged.connect(self.parent_changed)

            scene_node_parent = Application.getInstance().getBuildVolume()
            scene_node.setParent(scene_node_parent)

            settings = Application.getInstance().getGlobalContainerStack()
            machine_width = settings.getProperty("machine_width", "value")
            machine_depth = settings.getProperty("machine_depth", "value")

            scene_node.setPosition(Vector(-machine_width / 2, 0, machine_depth / 2))

            view = Application.getInstance().getController().getActiveView()
            if view.getPluginId() == "LayerView":
                view.resetLayerData()
                view.setLayer(999999)
                view.calculateMaxLayers()

            Logger.log("d", "Loaded %s" % file_name)

        return scene_node
