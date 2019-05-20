# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import numpy

import math

from PyQt5.QtGui import QImage, qRed, qGreen, qBlue
from PyQt5.QtCore import Qt

from UM.Mesh.MeshReader import MeshReader
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Math.Vector import Vector
from UM.Job import Job
from UM.Logger import Logger
from .ImageReaderUI import ImageReaderUI

from cura.Scene.CuraSceneNode import CuraSceneNode as SceneNode


class ImageReader(MeshReader):
    def __init__(self) -> None:
        super().__init__()
        self._supported_extensions = [".jpg", ".jpeg", ".bmp", ".gif", ".png"]
        self._ui = ImageReaderUI(self)

    def preRead(self, file_name, *args, **kwargs):
        img = QImage(file_name)

        if img.isNull():
            Logger.log("e", "Image is corrupt.")
            return MeshReader.PreReadResult.failed

        width = img.width()
        depth = img.height()

        largest = max(width, depth)
        width = width / largest * self._ui.default_width
        depth = depth / largest * self._ui.default_depth

        self._ui.setWidthAndDepth(width, depth)
        self._ui.showConfigUI()
        self._ui.waitForUIToClose()

        if self._ui.getCancelled():
            return MeshReader.PreReadResult.cancelled
        return MeshReader.PreReadResult.accepted

    def _read(self, file_name):
        size = max(self._ui.getWidth(), self._ui.getDepth())
        return self._generateSceneNode(file_name, size, self._ui.peak_height, self._ui.base_height, self._ui.smoothing, 512, self._ui.lighter_is_higher, self._ui.use_logarithmic_function)

    def _generateSceneNode(self, file_name, xz_size, peak_height, base_height, blur_iterations, max_size, lighter_is_higher, use_logarithmic_function):
        scene_node = SceneNode()

        mesh = MeshBuilder()

        img = QImage(file_name)

        if img.isNull():
            Logger.log("e", "Image is corrupt.")
            return None

        width = max(img.width(), 2)
        height = max(img.height(), 2)
        aspect = height / width

        if img.width() < 2 or img.height() < 2:
            img = img.scaled(width, height, Qt.IgnoreAspectRatio)

        base_height = max(base_height, 0)
        peak_height = max(peak_height, -base_height)

        xz_size = max(xz_size, 1)
        scale_vector = Vector(xz_size, peak_height, xz_size)

        if width > height:
            scale_vector = scale_vector.set(z=scale_vector.z * aspect)
        elif height > width:
            scale_vector = scale_vector.set(x=scale_vector.x / aspect)

        if width > max_size or height > max_size:
            scale_factor = max_size / width
            if height > width:
                scale_factor = max_size / height

            width = int(max(round(width * scale_factor), 2))
            height = int(max(round(height * scale_factor), 2))
            img = img.scaled(width, height, Qt.IgnoreAspectRatio)

        width_minus_one = width - 1
        height_minus_one = height - 1

        Job.yieldThread()

        texel_width = 1.0 / (width_minus_one) * scale_vector.x
        texel_height = 1.0 / (height_minus_one) * scale_vector.z

        height_data = numpy.zeros((height, width), dtype=numpy.float32)

        for x in range(0, width):
            for y in range(0, height):
                qrgb = img.pixel(x, y)
                luminance = (0.2126 * qRed(qrgb) + 0.7152 * qGreen(qrgb) + 0.0722 * qBlue(qrgb)) / 255 # fast computation ignoring gamma
                height_data[y, x] = luminance

        Job.yieldThread()

        if not lighter_is_higher:
            height_data = 1 - height_data

        for _ in range(0, blur_iterations):
            copy = numpy.pad(height_data, ((1, 1), (1, 1)), mode= "edge")

            height_data += copy[1:-1, 2:]
            height_data += copy[1:-1, :-2]
            height_data += copy[2:, 1:-1]
            height_data += copy[:-2, 1:-1]

            height_data += copy[2:, 2:]
            height_data += copy[:-2, 2:]
            height_data += copy[2:, :-2]
            height_data += copy[:-2, :-2]

            height_data /= 9

            Job.yieldThread()

        if use_logarithmic_function:
            min_luminance = 2.0 ** (peak_height - base_height)
            for (y, x) in numpy.ndindex(height_data.shape):
                mapped_luminance = min_luminance + (1.0 - min_luminance) * height_data[y, x]
                height_data[y, x] = peak_height - math.log(mapped_luminance, 2)
        else:
            height_data *= scale_vector.y
            height_data += base_height

        heightmap_face_count = 2 * height_minus_one * width_minus_one
        total_face_count = heightmap_face_count + (width_minus_one * 2) * (height_minus_one * 2) + 2

        mesh.reserveFaceCount(total_face_count)

        # initialize to texel space vertex offsets.
        # 6 is for 6 vertices for each texel quad.
        heightmap_vertices = numpy.zeros((width_minus_one * height_minus_one, 6, 3), dtype = numpy.float32)
        heightmap_vertices = heightmap_vertices + numpy.array([[
            [0, base_height, 0],
            [0, base_height, texel_height],
            [texel_width, base_height, texel_height],
            [texel_width, base_height, texel_height],
            [texel_width, base_height, 0],
            [0, base_height, 0]
        ]], dtype = numpy.float32)

        offsetsz, offsetsx = numpy.mgrid[0: height_minus_one, 0: width - 1]
        offsetsx = numpy.array(offsetsx, numpy.float32).reshape(-1, 1) * texel_width
        offsetsz = numpy.array(offsetsz, numpy.float32).reshape(-1, 1) * texel_height

        # offsets for each texel quad
        heightmap_vertex_offsets = numpy.concatenate([offsetsx, numpy.zeros((offsetsx.shape[0], offsetsx.shape[1]), dtype=numpy.float32), offsetsz], 1)
        heightmap_vertices += heightmap_vertex_offsets.repeat(6, 0).reshape(-1, 6, 3)

        # apply height data to y values
        heightmap_vertices[:, 0, 1] = heightmap_vertices[:, 5, 1] = height_data[:-1, :-1].reshape(-1)
        heightmap_vertices[:, 1, 1] = height_data[1:, :-1].reshape(-1)
        heightmap_vertices[:, 2, 1] = heightmap_vertices[:, 3, 1] = height_data[1:, 1:].reshape(-1)
        heightmap_vertices[:, 4, 1] = height_data[:-1, 1:].reshape(-1)

        heightmap_indices = numpy.array(numpy.mgrid[0:heightmap_face_count * 3], dtype=numpy.int32).reshape(-1, 3)

        mesh._vertices[0:(heightmap_vertices.size // 3), :] = heightmap_vertices.reshape(-1, 3)
        mesh._indices[0:(heightmap_indices.size // 3), :] = heightmap_indices

        mesh._vertex_count = heightmap_vertices.size // 3
        mesh._face_count = heightmap_indices.size // 3

        geo_width = width_minus_one * texel_width
        geo_height = height_minus_one * texel_height

        # bottom
        mesh.addFaceByPoints(0, 0, 0, 0, 0, geo_height, geo_width, 0, geo_height)
        mesh.addFaceByPoints(geo_width, 0, geo_height, geo_width, 0, 0, 0, 0, 0)

        # north and south walls
        for n in range(0, width_minus_one):
            x = n * texel_width
            nx = (n + 1) * texel_width

            hn0 = height_data[0, n]
            hn1 = height_data[0, n + 1]

            hs0 = height_data[height_minus_one, n]
            hs1 = height_data[height_minus_one, n + 1]

            mesh.addFaceByPoints(x, 0, 0, nx, 0, 0, nx, hn1, 0)
            mesh.addFaceByPoints(nx, hn1, 0, x, hn0, 0, x, 0, 0)

            mesh.addFaceByPoints(x, 0, geo_height, nx, 0, geo_height, nx, hs1, geo_height)
            mesh.addFaceByPoints(nx, hs1, geo_height, x, hs0, geo_height, x, 0, geo_height)

        # west and east walls
        for n in range(0, height_minus_one):
            y = n * texel_height
            ny = (n + 1) * texel_height

            hw0 = height_data[n, 0]
            hw1 = height_data[n + 1, 0]

            he0 = height_data[n, width_minus_one]
            he1 = height_data[n + 1, width_minus_one]

            mesh.addFaceByPoints(0, 0, y, 0, 0, ny, 0, hw1, ny)
            mesh.addFaceByPoints(0, hw1, ny, 0, hw0, y, 0, 0, y)

            mesh.addFaceByPoints(geo_width, 0, y, geo_width, 0, ny, geo_width, he1, ny)
            mesh.addFaceByPoints(geo_width, he1, ny, geo_width, he0, y, geo_width, 0, y)

        mesh.calculateNormals(fast=True)

        scene_node.setMeshData(mesh.build())

        return scene_node
