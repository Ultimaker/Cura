# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import re  # For escaping characters in the settings.
import time
import struct
import math
import numpy
from collections import namedtuple
from typing import Dict, List, NamedTuple, Optional, Union

from cura import LayerDataBuilder
from cura.LayerPolygon import LayerPolygon
from cura.Settings.ExtruderManager import ExtruderManager

from UM.Backend import Backend
from UM.Job import Job
from UM.Math.Vector import Vector
from UM.Mesh.MeshData import MeshData
from UM.Mesh.MeshWriter import MeshWriter
from UM.Message import Message
from UM.Logger import Logger
from UM.Application import Application
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.i18n import i18nCatalog


catalog = i18nCatalog("cura")

Position = NamedTuple("Position", [("x", float), ("y", float), ("z", float), ("f", float), ("e", float)])



def is_pos_eq(pos_a, pos_b):
    return numpy.isclose(pos_a.x, pos_b.x) and numpy.isclose(pos_a.y, pos_b.y)

##  Writes g-code to a file.
#
#   While this poses as a mesh writer, what this really does is take the g-code
#   in the entire scene and write it to an output device. Since the g-code of a
#   single mesh isn't separable from the rest what with rafts and travel moves
#   and all, it doesn't make sense to write just a single mesh.
#
#   So this plug-in takes the g-code that is stored in the root of the scene
#   node tree, adds a bit of extra information about the profiles and writes
#   that to the output device.
class GCodeModelWriter(MeshWriter):
    ##  The file format version of the serialised g-code.
    #
    #   It can only read settings with the same version as the version it was
    #   written with. If the file format is changed in a way that breaks reverse
    #   compatibility, increment this version number!
    version = 3

    ##  Dictionary that defines how characters are escaped when embedded in
    #   g-code.
    #
    #   Note that the keys of this dictionary are regex strings. The values are
    #   not.
    escape_characters = {
        re.escape("\\"): "\\\\",  # The escape character.
        re.escape("\n"): "\\n",   # Newlines. They break off the comment.
        re.escape("\r"): "\\r"    # Carriage return. Windows users may need this for visualisation in their editors.
    }

    _setting_keyword = ";SETTING_"
    _type_keyword = ";TYPE:"
    _layer_keyword = ";LAYER:"

    def __init__(self):
        super().__init__()

        self._application = Application.getInstance()

    ##  Writes the g-code for the entire scene to a stream.
    #
    #   Note that even though the function accepts a collection of nodes, the
    #   entire scene is always written to the file since it is not possible to
    #   separate the g-code for just specific nodes.
    #
    #   \param stream The stream to write the g-code to.
    #   \param nodes This is ignored.
    #   \param mode Additional information on how to format the g-code in the
    #   file. This must always be text mode.
    def write(self, stream, nodes, mode = MeshWriter.OutputMode.TextMode):
        if mode != MeshWriter.OutputMode.BinaryMode:
            Logger.log("e", "GCodeWriter does not support text mode.")
            return False
        #self.write_stl(stream)
        #self.write_scad(stream, shape = "cube")  # shape is cube or cylinder
        #self.write_f360(stream)
        self.write_csv(stream)
        return True

    def write_stl(self, stream):
        tube_type = "rectangular"
        #tube_type = "diamond"

        num_vertices = {
            "diamond": 16,
            "rectangular": 12}
        tube_function = {
            "diamond": self._generateTubeVerticesDiamond,
            "rectangular": self._generateTubeVerticesRectangular,
        }

        active_build_plate = Application.getInstance().getMultiBuildPlateModel().activeBuildPlate
        scene = Application.getInstance().getController().getScene()
        if not hasattr(scene, "gcode_dict"):
            return False
        gcode_dict = getattr(scene, "gcode_dict")
        gcode_list = gcode_dict.get(active_build_plate, None)
        if gcode_list is not None:
            paths = self.convertGCode(gcode_list)
            # every path becomes 12 or 16 faces, each consisting of 3 coordinates and every coordinate has x, y, z
            paths_vertices = numpy.zeros([3 * num_vertices[tube_type] * len(paths), 3])
            current_base_index = 0
            len_paths = len(paths)
            print("len(paths): " + str(len_paths))
            count = 0
            for position_from, position_to, layer_thickness in paths:
                line_width = self._calculateLineWidth(position_to, position_from, layer_thickness)
                vertices = tube_function[tube_type](position_from, position_to, line_width + 0.02, layer_thickness + 0.02, offset = 0.02)
                #vertices = tube_function[tube_type](position_from, position_to, line_width, layer_thickness)
                paths_vertices[current_base_index:current_base_index + 3 * num_vertices[tube_type], :] = vertices[:, :]
                current_base_index += 3 * num_vertices[tube_type]
                print("processing" + str(count) + " / " + str(len_paths) + "...")
                count += 1
            mesh_data = MeshData(vertices = paths_vertices)
            print("Saving...")
            self._writeBinary(stream, mesh_data)

    def _writeBinary(self, stream, mesh_data: MeshData):
        Logger.log("d", "Writing stl...")
        stream.write("Uranium STLWriter {0}".format(time.strftime("%a %d %b %Y %H:%M:%S")).encode().ljust(80, b"\000"))

        face_count = 0
        if mesh_data.hasIndices():
            face_count += mesh_data.getFaceCount()
        else:
            face_count += mesh_data.getVertexCount() / 3

        stream.write(struct.pack("<I", int(face_count))) #Write number of faces to STL

        if mesh_data.hasIndices():
            verts = mesh_data.getVertices()
            for face in mesh_data.getIndices():
                v1 = verts[face[0]]
                v2 = verts[face[1]]
                v3 = verts[face[2]]
                stream.write(struct.pack("<fff", 0.0, 0.0, 0.0))
                stream.write(struct.pack("<fff", v1[0], -v1[2], v1[1]))
                stream.write(struct.pack("<fff", v2[0], -v2[2], v2[1]))
                stream.write(struct.pack("<fff", v3[0], -v3[2], v3[1]))
                stream.write(struct.pack("<H", 0))
        else:
            num_verts = mesh_data.getVertexCount()
            verts = mesh_data.getVertices()
            for index in range(0, num_verts - 1, 3):
                v1 = verts[index]
                v2 = verts[index + 1]
                v3 = verts[index + 2]
                stream.write(struct.pack("<fff", 0.0, 0.0, 0.0))
                stream.write(struct.pack("<fff", v1[0], -v1[2], v1[1]))
                stream.write(struct.pack("<fff", v2[0], -v2[2], v2[1]))
                stream.write(struct.pack("<fff", v3[0], -v3[2], v3[1]))
                stream.write(struct.pack("<H", 0))

    def write_scad(self, stream, shape = "cube"):
        active_build_plate = Application.getInstance().getMultiBuildPlateModel().activeBuildPlate
        scene = Application.getInstance().getController().getScene()
        if not hasattr(scene, "gcode_dict"):
            return False
        gcode_dict = getattr(scene, "gcode_dict")
        gcode_list = gcode_dict.get(active_build_plate, None)
        if shape == "cylinder":
            stream.write("$fn = 24;\n".encode())
        if gcode_list is not None:
            paths = self.convertGCode(gcode_list)
            for position_from, position_to, layer_thickness in paths:
                line_width = self._calculateLineWidth(position_to, position_from, layer_thickness)
                stream.write(self._generateScad(position_from, position_to, line_width + 0.02, layer_thickness + 0.02, offset = 0.02, shape=shape).encode())

    def _generateScad(self, position_from, position_to, width, thickness, offset = 0, shape = "cube"):
        path_from_zero = Vector(position_to.x - position_from.x, position_to.y - position_from.y, position_to.z - position_from.z)
        length = path_from_zero.length()
        angle_radians = math.atan2(path_from_zero.x, path_from_zero.y)
        angle_degrees = math.degrees(angle_radians)
        print("length: " + str(length) + "  angle: " + str(angle_degrees))
        if shape == "cube":
            return self._generateScadCube(position_from, length, width, thickness, angle_degrees, offset)
        elif shape == "cylinder":
            return self._generateScadCylinder(position_from, length, width, thickness, angle_degrees, offset)

    def _generateScadCube(self, position_from, length, width, thickness, angle, offset = 0):
        return "translate([{x}, {y}, {z}]) rotate([0, 0, {angle}]) translate([-{half_line_width}, -{half_line_width}, 0]) cube([{line_width}, {length}, {layer_thickness}]);\n".format(
            length = length + width - offset, line_width = width, layer_thickness = thickness,
            half_line_width = 0.5 * width, angle = -angle,
            x = position_from.x + offset, y = position_from.y, z = position_from.z)

    def _generateScadCylinder(self, position_from, length, width, thickness, angle, offset = 0):
        return """
        translate([{x}, {y}, {z}]) rotate([0, 0, {angle}]) rotate([-90, 0, 0]) union() {{
            cylinder(r = {half_line_width}, h = {length});
            sphere(r = {half_line_width});
            translate([0, 0, {length}])
            sphere(r = {half_line_width});
        }}
        """.format(
            length = length - offset, line_width = width, layer_thickness = thickness,
            half_line_width = 0.5 * width, angle = -angle,
            x = position_from.x + offset, y = position_from.y, z = position_from.z)
        # return """
        # translate([{x}, {y}, {z}])
        # rotate([0, 0, {angle}])
        # translate([0, -{half_line_width}, 0])
        # rotate([-90, 0, 0])
        # cylinder(r = {half_line_width}, h = {length});
        # """.format(
        #     length = length + width - offset, line_width = width, layer_thickness = thickness,
        #     half_line_width = 0.5 * width, angle = -angle,
        #     x = position_from.x + offset, y = position_from.y, z = position_from.z)

    def write_f360(self, stream):
        script_template_before = """
import adsk.core, adsk.fusion, traceback

def run(context):
    ui = None
    try: 
        app = adsk.core.Application.get()
        ui = app.userInterface

        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = app.activeProduct

        # Get the root component of the active design.
        rootComp = design.rootComponent

        # Create a new sketch on the xy plane.
        sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
"""
        script_template_after = """        
    except:
        if ui:
            ui.messageBox('Failed:\\n{}'.format(traceback.format_exc()))"""

        active_build_plate = Application.getInstance().getMultiBuildPlateModel().activeBuildPlate
        scene = Application.getInstance().getController().getScene()
        if not hasattr(scene, "gcode_dict"):
            return False
        gcode_dict = getattr(scene, "gcode_dict")
        gcode_list = gcode_dict.get(active_build_plate, None)
        if gcode_list is not None:
            paths = self.convertGCode(gcode_list)
            stream.write(script_template_before.encode())
            for position_from, position_to, layer_thickness in paths:
                stream.write(self._generateF360Line(position_from, position_to).encode())
            stream.write(script_template_after.encode())

    def _generateF360Line(self, position_from, position_to):
        add_line_template = """
        pt1 = adsk.core.Point3D.create({x0}, {y0}, {z0})
        pt2 = adsk.core.Point3D.create({x1}, {y1}, {z1})
        sketch.sketchCurves.sketchLines.addByTwoPoints(pt1, pt2)
        """
        return add_line_template.format(
            x0 = position_from.x, y0 = position_from.y, z0 = position_from.z,
            x1 = position_to.x, y1 = position_to.y, z1 = position_to.z)

    def write_csv(self, stream):
        active_build_plate = Application.getInstance().getMultiBuildPlateModel().activeBuildPlate
        scene = Application.getInstance().getController().getScene()
        if not hasattr(scene, "gcode_dict"):
            return False
        gcode_dict = getattr(scene, "gcode_dict")
        gcode_list = gcode_dict.get(active_build_plate, None)
        if gcode_list is not None:
            paths = self.convertGCode(gcode_list)
            for position_from, position_to, layer_thickness in paths:
                line_width = self._calculateLineWidth(position_to, position_from, layer_thickness)
                stream.write(self._generate_csv_line(position_from, position_to, width = line_width, height = layer_thickness).encode())

    def _generate_csv_line(self, position_from, position_to, width, height):
        return "{x0}, {y0}, {z0}, {x1}, {y1}, {z1}\n".format(
            x0 = position_from.x, y0 = position_from.y, z0 = position_from.z,
            x1 = position_to.x, y1 = position_to.y, z1 = position_to.z, width = width, height = height)

    ##  Return vertices corresponding to a tube-like shape that goes from 'from' to 'to'
    #   This version has rectangular cross sections
    def _generateTubeVerticesRectangular(self, point_from, point_to, line_width, line_height, offset = 0):
        result = numpy.zeros([3 * 12, 3])
        real_result = numpy.zeros([3 * 12, 3])  # y and z are swapped
        half_width = 0.5 * line_width
        half_height = 0.5 * line_height
        v_from = Vector(point_from.x, point_from.y, point_from.z)
        v_to = Vector(point_to.x, point_to.y, point_to.z)
        direction = (v_to - v_from).normalized()
        v_from -= Vector(half_width * direction.x, half_width * direction.y, 0)
        v_to += Vector(half_width * direction.x, half_width * direction.y, 0)
        if offset != 0:
            v_from = v_from + Vector(offset * direction.x, offset * direction.y, 0)

        # the "long" part, or "sides"
        idx = 0
        result[idx + 0, :] = [v_to.x + half_width * direction.y, v_to.y - half_width * direction.x, v_to.z + half_height]
        result[idx + 1, :] = [v_from.x + half_width * direction.y, v_from.y - half_width * direction.x, v_from.z + half_height]
        result[idx + 2, :] = [v_from.x + half_width * direction.y, v_from.y - half_width * direction.x, v_from.z - half_height]
        idx += 3
        result[idx + 0, :] = [v_to.x + half_width * direction.y, v_to.y - half_width * direction.x, v_to.z + half_height]
        result[idx + 1, :] = [v_from.x + half_width * direction.y, v_from.y - half_width * direction.x, v_from.z - half_height]
        result[idx + 2, :] = [v_to.x + half_width * direction.y, v_to.y - half_width * direction.x, v_to.z - half_height]

        idx += 3
        result[idx + 0, :] = [v_to.x + half_width * direction.y, v_to.y - half_width * direction.x, v_to.z - half_height]
        result[idx + 1, :] = [v_from.x + half_width * direction.y, v_from.y - half_width * direction.x, v_from.z - half_height]
        result[idx + 2, :] = [v_from.x - half_width * direction.y, v_from.y + half_width * direction.x, v_from.z - half_height]
        idx += 3
        result[idx + 0, :] = [v_to.x + half_width * direction.y, v_to.y - half_width * direction.x, v_to.z - half_height]
        result[idx + 1, :] = [v_from.x - half_width * direction.y, v_from.y + half_width * direction.x, v_from.z - half_height]
        result[idx + 2, :] = [v_to.x - half_width * direction.y, v_to.y + half_width * direction.x, v_to.z - half_height]

        idx += 3
        result[idx + 0, :] = [v_to.x - half_width * direction.y, v_to.y + half_width * direction.x, v_to.z - half_height]
        result[idx + 1, :] = [v_from.x - half_width * direction.y, v_from.y + half_width * direction.x, v_from.z - half_height]
        result[idx + 2, :] = [v_from.x - half_width * direction.y, v_from.y + half_width * direction.x, v_from.z + half_height]
        idx += 3
        result[idx + 0, :] = [v_to.x - half_width * direction.y, v_to.y + half_width * direction.x, v_to.z - half_height]
        result[idx + 1, :] = [v_from.x - half_width * direction.y, v_from.y + half_width * direction.x, v_from.z + half_height]
        result[idx + 2, :] = [v_to.x - half_width * direction.y, v_to.y + half_width * direction.x, v_to.z + half_height]

        idx += 3
        result[idx + 0, :] = [v_to.x - half_width * direction.y, v_to.y + half_width * direction.x, v_to.z + half_height]
        result[idx + 1, :] = [v_from.x - half_width * direction.y, v_from.y + half_width * direction.x, v_from.z + half_height]
        result[idx + 2, :] = [v_from.x + half_width * direction.y, v_from.y - half_width * direction.x, v_from.z + half_height]
        idx += 3
        result[idx + 0, :] = [v_to.x - half_width * direction.y, v_to.y + half_width * direction.x, v_to.z + half_height]
        result[idx + 1, :] = [v_from.x + half_width * direction.y, v_from.y - half_width * direction.x, v_from.z + half_height]
        result[idx + 2, :] = [v_to.x + half_width * direction.y, v_to.y - half_width * direction.x, v_to.z + half_height]

        # "to"
        idx += 3
        result[idx + 0, :] = [v_to.x + half_width * direction.y, v_to.y - half_width * direction.x, v_to.z + half_height]
        result[idx + 1, :] = [v_to.x + half_width * direction.y, v_to.y - half_width * direction.x, v_to.z - half_height]
        result[idx + 2, :] = [v_to.x - half_width * direction.y, v_to.y + half_width * direction.x, v_to.z - half_height]

        idx += 3
        result[idx + 0, :] = [v_to.x - half_width * direction.y, v_to.y + half_width * direction.x, v_to.z - half_height]
        result[idx + 1, :] = [v_to.x - half_width * direction.y, v_to.y + half_width * direction.x, v_to.z + half_height]
        result[idx + 2, :] = [v_to.x + half_width * direction.y, v_to.y - half_width * direction.x, v_to.z + half_height]

        # "from"
        idx += 3
        result[idx + 0, :] = [v_from.x - half_width * direction.y, v_from.y + half_width * direction.x, v_from.z - half_height]
        result[idx + 1, :] = [v_from.x + half_width * direction.y, v_from.y - half_width * direction.x, v_from.z - half_height]
        result[idx + 2, :] = [v_from.x + half_width * direction.y, v_from.y - half_width * direction.x, v_from.z + half_height]

        idx += 3
        result[idx + 0, :] = [v_from.x + half_width * direction.y, v_from.y - half_width * direction.x, v_from.z + half_height]
        result[idx + 1, :] = [v_from.x - half_width * direction.y, v_from.y + half_width * direction.x, v_from.z + half_height]
        result[idx + 2, :] = [v_from.x - half_width * direction.y, v_from.y + half_width * direction.x, v_from.z - half_height]

        # x, z, y in printing coordinates, so swapping + 1 and + 2
        real_result[:, 0] = result[:, 0]
        real_result[:, 1] = result[:, 2]
        real_result[:, 2] = -result[:, 1]

        return real_result

    ##  Return vertices corresponding to a tube-like shape that goes from 'from' to 'to'
    #   This version does it in the same way as the layer view does: the cross section is diamond shaped
    #   Assumes that z in from and to are the same
    #   offset is also used to move some points around so the chance that they collide is smaller (i.e. in a square box)
    def _generateTubeVerticesDiamond(self, point_from, point_to, line_width, line_height, offset = 0):
        result = numpy.zeros([3 * 16, 3])
        real_result = numpy.zeros([3 * 16, 3])  # y and z are swapped
        half_width = 0.5 * line_width
        half_height = 0.5 * line_height
        v_from = Vector(point_from.x, point_from.y, point_from.z)
        v_to = Vector(point_to.x, point_to.y, point_to.z)
        direction = (v_to - v_from).normalized()
        if offset != 0:
            v_from = v_from + Vector(offset * direction.x, offset * direction.y, 0)

        # the "long" part, or "sides"
        idx = 0
        result[idx + 0, :] = [v_to.x, v_to.y, v_to.z + half_height]
        result[idx + 1, :] = [v_from.x, v_from.y, v_from.z + half_height]
        result[idx + 2, :] = [v_from.x + half_width * direction.y, v_from.y - half_width * direction.x, v_from.z]
        idx += 3
        result[idx + 0, :] = [v_to.x, v_to.y, v_to.z + half_height]
        result[idx + 1, :] = [v_from.x + half_width * direction.y, v_from.y - half_width * direction.x, v_from.z]
        result[idx + 2, :] = [v_to.x + half_width * direction.y, v_to.y - half_width * direction.x, v_to.z]

        idx += 3
        result[idx + 0, :] = [v_to.x + half_width * direction.y, v_to.y - half_width * direction.x, v_to.z]
        result[idx + 1, :] = [v_from.x + half_width * direction.y, v_from.y - half_width * direction.x, v_from.z]
        result[idx + 2, :] = [v_from.x, v_from.y, v_from.z - half_height]
        idx += 3
        result[idx + 0, :] = [v_to.x + half_width * direction.y, v_to.y - half_width * direction.x, v_to.z]
        result[idx + 1, :] = [v_from.x, v_from.y, v_from.z - half_height]
        result[idx + 2, :] = [v_to.x, v_to.y, v_to.z - half_height]

        idx += 3
        result[idx + 0, :] = [v_to.x, v_to.y, v_to.z - half_height]
        result[idx + 1, :] = [v_from.x, v_from.y, v_from.z - half_height]
        result[idx + 2, :] = [v_from.x - half_width * direction.y, v_from.y + half_width * direction.x, v_from.z]
        idx += 3
        result[idx + 0, :] = [v_to.x, v_to.y, v_to.z - half_height]
        result[idx + 1, :] = [v_from.x - half_width * direction.y, v_from.y + half_width * direction.x, v_from.z]
        result[idx + 2, :] = [v_to.x - half_width * direction.y, v_to.y + half_width * direction.x, v_to.z]

        idx += 3
        result[idx + 0, :] = [v_to.x - half_width * direction.y, v_to.y + half_width * direction.x, v_to.z]
        result[idx + 1, :] = [v_from.x - half_width * direction.y, v_from.y + half_width * direction.x, v_from.z]
        result[idx + 2, :] = [v_from.x, v_from.y, v_from.z + half_height]
        idx += 3
        result[idx + 0, :] = [v_to.x - half_width * direction.y, v_to.y + half_width * direction.x, v_to.z]
        result[idx + 1, :] = [v_from.x, v_from.y, v_from.z + half_height]
        result[idx + 2, :] = [v_to.x, v_to.y, v_to.z + half_height]

        # "from" end
        idx += 3
        result[idx + 0, :] = [v_from.x - half_width * direction.x, v_from.y - half_width * direction.y, v_from.z]
        result[idx + 1, :] = [v_from.x + half_width * direction.y, v_from.y - half_width * direction.x, v_from.z]
        result[idx + 2, :] = [v_from.x, v_from.y, v_from.z + half_height]

        idx += 3
        result[idx + 0, :] = [v_from.x - half_width * direction.x, v_from.y - half_width * direction.y, v_from.z]
        result[idx + 1, :] = [v_from.x, v_from.y, v_from.z - half_height]
        result[idx + 2, :] = [v_from.x + half_width * direction.y, v_from.y - half_width * direction.x, v_from.z]

        idx += 3
        result[idx + 0, :] = [v_from.x - half_width * direction.x, v_from.y - half_width * direction.y, v_from.z]
        result[idx + 1, :] = [v_from.x - half_width * direction.y, v_from.y + half_width * direction.x, v_from.z]
        result[idx + 2, :] = [v_from.x, v_from.y, v_from.z - half_height]

        idx += 3
        result[idx + 0, :] = [v_from.x - half_width * direction.x, v_from.y - half_width * direction.y, v_from.z]
        result[idx + 1, :] = [v_from.x, v_from.y, v_from.z + half_height]
        result[idx + 2, :] = [v_from.x - half_width * direction.y, v_from.y + half_width * direction.x, v_from.z]

        # "to" end
        idx += 3
        result[idx + 0, :] = [v_to.x + half_width * direction.x, v_to.y + half_width * direction.y, v_to.z]
        result[idx + 1, :] = [v_to.x, v_to.y, v_to.z + half_height]
        result[idx + 2, :] = [v_to.x + half_width * direction.y, v_to.y - half_width * direction.x, v_to.z]

        idx += 3
        result[idx + 0, :] = [v_to.x + half_width * direction.x, v_to.y + half_width * direction.y, v_to.z]
        result[idx + 1, :] = [v_to.x + half_width * direction.y, v_to.y - half_width * direction.x, v_to.z]
        result[idx + 2, :] = [v_to.x, v_to.y, v_to.z - half_height]

        idx += 3
        result[idx + 0, :] = [v_to.x + half_width * direction.x, v_to.y + half_width * direction.y, v_to.z]
        result[idx + 1, :] = [v_to.x, v_to.y, v_to.z - half_height]
        result[idx + 2, :] = [v_to.x - half_width * direction.y, v_to.y + half_width * direction.x, v_to.z]

        idx += 3
        result[idx + 0, :] = [v_to.x + half_width * direction.x, v_to.y + half_width * direction.y, v_to.z]
        result[idx + 1, :] = [v_to.x - half_width * direction.y, v_to.y + half_width * direction.x, v_to.z]
        result[idx + 2, :] = [v_to.x, v_to.y, v_to.z + half_height]

        # x, z, y in printing coordinates, so swapping + 1 and + 2
        real_result[:, 0] = result[:, 0]
        real_result[:, 1] = result[:, 2]
        real_result[:, 2] = -result[:, 1]

        return real_result

    def convertGCode(self, gcode_layers):
        self._clearValues()
        current_path = []
        current_position = self._position(0, 0, 0, 0, [0])
        for gcode_layer in gcode_layers:
            for line in gcode_layer.split("\n"):
                G = self._getInt(line, "G")
                if G is not None:
                    current_position = self.processGCode(G, line, current_position, current_path)
        return current_path

    def _calculateLineWidth(self, current_point: Position, previous_point: Position, layer_thickness: float) -> float:
        # Area of the filament
        Af = (self._filament_diameter / 2) ** 2 * numpy.pi
        # Length of the extruded filament
        de = current_point.e - previous_point.e
        # Volumne of the extruded filament
        dVe = de * Af
        # Length of the printed line
        dX = numpy.sqrt((current_point.x - previous_point.x)**2 + (current_point.y - previous_point.y)**2)
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

    def _clearValues(self) -> None:
        self._extruder_number = 0
        self._extrusion_length_offset = [0]
        self._layer_type = LayerPolygon.Inset0Type
        self._layer_number = 0
        self._previous_z = 0
        self._layer_data_builder = LayerDataBuilder.LayerDataBuilder()
        self._is_absolute_positioning = True    # It can be absolute (G90) or relative (G91)
        self._is_absolute_extrusion = True  # It can become absolute (M82, default) or relative (M83)

        self._current_layer_thickness = 0.2  # default
        self._position = namedtuple('Position', ['x', 'y', 'z', 'f', 'e'])
        self._filament_diameter = 2.85       # default

    @staticmethod
    def _getValue(line: str, code: str) -> Optional[Union[str, int, float]]:
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

    def _getInt(self, line: str, code: str) -> Optional[int]:
        value = self._getValue(line, code)
        try:
            return int(value)
        except:
            return None

    ##  For showing correct x, y offsets for each extruder
    def _extruderOffsets(self) -> Dict[int, List[float]]:
        result = {}
        for extruder in ExtruderManager.getInstance().getExtruderStacks():
            result[int(extruder.getMetaData().get("position", "0"))] = [
                extruder.getProperty("machine_nozzle_offset_x", "value"),
                extruder.getProperty("machine_nozzle_offset_y", "value")]
        return result


    def _gCode0(self, position: Position, params: Position, path: List[List[Union[float, int]]]) -> Position:
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
            position_from = self._position(x = position.x, y = position.y, z = position.z, f = position.f, e = position.e[self._extruder_number])
            position_to = self._position(x = x, y = y, z = z, f = f, e = new_extrusion_value + self._extrusion_length_offset[self._extruder_number])
            if new_extrusion_value > e[self._extruder_number] + 0.001 and not is_pos_eq(position_from, position_to):
                path.append((position_from, position_to, self._current_layer_thickness))
            # else:
            #     path.append([x, y, z, f, new_extrusion_value + self._extrusion_length_offset[self._extruder_number], LayerPolygon.MoveRetractionType])  # retraction
            e[self._extruder_number] = new_extrusion_value

            # Only when extruding we can determine the latest known "layer height" which is the difference in height between extrusions
            # Also, 1.5 is a heuristic for any priming or whatsoever, we skip those.
            if z > self._previous_z and (z - self._previous_z < 1.5):
                self._current_layer_thickness = z - self._previous_z # allow a tiny overlap
                self._previous_z = z
        # else:
        #     path.append([x, y, z, f, e[self._extruder_number] + self._extrusion_length_offset[self._extruder_number], LayerPolygon.MoveCombingType])
        return self._position(x, y, z, f, e)


    # G0 and G1 should be handled exactly the same.
    _gCode1 = _gCode0

    ##  Reset the current position to the values specified.
    #   For example: G92 X10 will set the X to 10 without any physical motion.
    def _gCode92(self, position: Position, params: Position, path: List[List[Union[float, int]]]) -> Position:
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

    def processGCode(self, G: int, line: str, position: Position, path: List[List[Union[float, int]]]) -> Position:
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
            params = self._position(x, y, z, f, e)
            return func(position, params, path)
        return position

    def processTCode(self, T: int, line: str, position: Position, path: List[List[Union[float, int]]]) -> Position:
        self._extruder_number = T
        if self._extruder_number + 1 > len(position.e):
            self._extrusion_length_offset.extend([0] * (self._extruder_number - len(position.e) + 1))
            position.e.extend([0] * (self._extruder_number - len(position.e) + 1))
        return position

    def processMCode(self, M: int, line: str, position: Position, path: List[List[Union[float, int]]]) -> Position:
        pass

    def convertGCodeOld(self, gcode_list):
        result = MeshData()
        Logger.log("d", "Converting g-code to meshes...")
        self._clearValues()

        self._cancelled = False

        # We obtain the filament diameter from the selected extruder to calculate line widths
        global_stack = Application.getInstance().getGlobalContainerStack()
        self._filament_diameter = global_stack.extruders[str(self._extruder_number)].getProperty("material_diameter", "value")

        #scene_node = CuraSceneNode()
        # Override getBoundingBox function of the sceneNode, as this node should return a bounding box, but there is no
        # real data to calculate it from.
        #scene_node.getBoundingBox = self._getNullBoundingBox

        gcode_list = []
        self._is_layers_in_file = False

        self._extruder_offsets = self._extruderOffsets()  # dict with index the extruder number. can be empty

        ##############################################################################################
        ##  This part is where the action starts
        ##############################################################################################
        file_lines = 0
        current_line = 0
        for line in gcode_list:
            file_lines += 1
            gcode_list.append(line + "\n")
            if not self._is_layers_in_file and line[:len(self._layer_keyword)] == self._layer_keyword:
                self._is_layers_in_file = True

        file_step = max(math.floor(file_lines / 100), 1)

        self._message = Message(catalog.i18nc("@info:status", "Parsing G-code"),
                                lifetime=0,
                                title = catalog.i18nc("@info:title", "G-code Details"))

        self._message.setProgress(0)
        self._message.show()

        Logger.log("d", "Parsing Gcode...")

        current_position = self._position(0, 0, 0, 0, [0], self._current_layer_thickness)
        current_path = []
        min_layer_number = 0
        negative_layers = 0
        previous_layer = 0

        for line in gcode_list:
            if self._cancelled:
                Logger.log("d", "Parsing Gcode file cancelled")
                return None
            current_line += 1

            if current_line % file_step == 0:
                self._message.setProgress(math.floor(current_line / file_lines * 100))
                Job.yieldThread()
            if len(line) == 0:
                continue

            if line.find(self._type_keyword) == 0:
                _type = line[len(self._type_keyword):].strip()
                if _type == "WALL-INNER":
                    self._layer_type = LayerPolygon.InsetXType
                elif _type == "WALL-OUTER":
                    self._layer_type = LayerPolygon.Inset0Type
                elif _type == "SKIN":
                    self._layer_type = LayerPolygon.SkinType
                elif _type == "SKIRT":
                    self._layer_type = LayerPolygon.SkirtType
                elif _type == "SUPPORT":
                    self._layer_type = LayerPolygon.SupportType
                elif _type == "FILL":
                    self._layer_type = LayerPolygon.InfillType
                else:
                    Logger.log("w", "Encountered a unknown type (%s) while parsing g-code.", _type)

            # When the layer change is reached, the polygon is computed so we have just one layer per extruder
            if self._is_layers_in_file and line[:len(self._layer_keyword)] == self._layer_keyword:
                try:
                    layer_number = int(line[len(self._layer_keyword):])
                    #self._createPolygon(self._current_layer_thickness, current_path, self._extruder_offsets.get(self._extruder_number, [0, 0]))
                    current_path.clear()
                    # Start the new layer at the end position of the last layer
                    current_path.append([current_position.x, current_position.y, current_position.z, current_position.f, current_position.e[self._extruder_number], LayerPolygon.MoveCombingType])

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
                    # for empty_layer in range(previous_layer + 1, layer_number):
                    #     self._createEmptyLayer(empty_layer)

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
                    # self._createPolygon(self._current_layer_thickness, current_path, self._extruder_offsets.get(self._extruder_number, [0, 0]))
                    current_path.clear()

                    # When changing tool, store the end point of the previous path, then process the code and finally
                    # add another point with the new position of the head.
                    current_path.append([current_position.x, current_position.y, current_position.z, current_position.f, current_position.e[self._extruder_number], LayerPolygon.MoveCombingType])
                    current_position = self.processTCode(T, line, current_position, current_path)
                    current_path.append([current_position.x, current_position.y, current_position.z, current_position.f, current_position.e[self._extruder_number], LayerPolygon.MoveCombingType])

            if line.startswith("M"):
                M = self._getInt(line, "M")
                self.processMCode(M, line, current_position, current_path)

        # "Flush" leftovers. Last layer paths are still stored
        # if len(current_path) > 1:
        #     if self._createPolygon(self._current_layer_thickness, current_path, self._extruder_offsets.get(self._extruder_number, [0, 0])):
        #         self._layer_number += 1
        #         current_path.clear()

        material_color_map = numpy.zeros((8, 4), dtype = numpy.float32)
        material_color_map[0, :] = [0.0, 0.7, 0.9, 1.0]
        material_color_map[1, :] = [0.7, 0.9, 0.0, 1.0]
        material_color_map[2, :] = [0.9, 0.0, 0.7, 1.0]
        material_color_map[3, :] = [0.7, 0.0, 0.0, 1.0]
        material_color_map[4, :] = [0.0, 0.7, 0.0, 1.0]
        material_color_map[5, :] = [0.0, 0.0, 0.7, 1.0]
        material_color_map[6, :] = [0.3, 0.3, 0.3, 1.0]
        material_color_map[7, :] = [0.7, 0.7, 0.7, 1.0]
        layer_mesh = self._layer_data_builder.build(material_color_map)
        # decorator = LayerDataDecorator()
        # decorator.setLayerData(layer_mesh)
        # scene_node.addDecorator(decorator)

        # gcode_list_decorator = GCodeListDecorator()
        # gcode_list_decorator.setGCodeList(gcode_list)
        # scene_node.addDecorator(gcode_list_decorator)

        # gcode_dict stores gcode_lists for a number of build plates.
        active_build_plate_id = Application.getInstance().getMultiBuildPlateModel().activeBuildPlate
        gcode_dict = {active_build_plate_id: gcode_list}
        Application.getInstance().getController().getScene().gcode_dict = gcode_dict

        Logger.log("d", "Finished parsing Gcode")
        self._message.hide()

        if self._layer_number == 0:
            Logger.log("w", "File doesn't contain any valid layers")

        settings = Application.getInstance().getGlobalContainerStack()
        if not settings.getProperty("machine_center_is_zero", "value"):
            machine_width = settings.getProperty("machine_width", "value")
            machine_depth = settings.getProperty("machine_depth", "value")
            # scene_node.setPosition(Vector(-machine_width / 2, 0, machine_depth / 2))

        Logger.log("d", "Saving GCode")

        if Application.getInstance().getPreferences().getValue("gcodereader/show_caution"):
            caution_message = Message(catalog.i18nc(
                "@info:generic",
                "Make sure the g-code is suitable for your printer and printer configuration before sending the file to it. The g-code representation may not be accurate."),
                lifetime=0,
                title = catalog.i18nc("@info:title", "G-code Details"))
            caution_message.show()

        # The "save/print" button's state is bound to the backend state.
        backend = Application.getInstance().getBackend()
        backend.backendStateChange.emit(Backend.BackendState.Disabled)

        return result
