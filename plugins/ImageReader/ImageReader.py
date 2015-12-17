# Copyright (c) 2015 Ultimaker B.V.
# Copyright (c) 2013 David Braam
# Cura is released under the terms of the AGPLv3 or higher.

import os
import numpy

from PyQt5.QtGui import QImage, qRed, qGreen, qBlue
from PyQt5.QtCore import Qt

from UM.Mesh.MeshReader import MeshReader
from UM.Mesh.MeshData import MeshData
from UM.Scene.SceneNode import SceneNode
from UM.Math.Vector import Vector
from UM.Job import Job
from .ImageReaderUI import ImageReaderUI


class ImageReader(MeshReader):
    def __init__(self):
        super(ImageReader, self).__init__()
        self._supported_extensions = [".jpg", ".jpeg", ".bmp", ".gif", ".png"]
        self._ui = ImageReaderUI(self)
        self._wait = False
        self._canceled = False

    def read(self, file_name):
        extension = os.path.splitext(file_name)[1]
        if extension.lower() in self._supported_extensions:
            self._ui.showConfigUI()
            self._wait = True
            self._canceled = True

            while self._wait:
                pass
                # this causes the config window to not repaint...
                # Job.yieldThread()

            result = None
            if not self._canceled:
                result = self._generateSceneNode(file_name, self._ui.size, self._ui.peak_height, self._ui.base_height, self._ui.smoothing, 512)

            return result

        return None

    def _generateSceneNode(self, file_name, xz_size, peak_height, base_height, blur_iterations, max_size):
        mesh = None
        scene_node = None

        scene_node = SceneNode()

        mesh = MeshData()
        scene_node.setMeshData(mesh)

        img = QImage(file_name)
        width = max(img.width(), 2)
        height = max(img.height(), 2)
        aspect = height / width

        if img.width() < 2 or img.height() < 2:
            img = img.scaled(width, height, Qt.IgnoreAspectRatio)

        base_height = max(base_height, 0)

        xz_size = max(xz_size, 1)
        scale_vector = Vector(xz_size, max(peak_height - base_height, -base_height), xz_size)

        if width > height:
            scale_vector.setZ(scale_vector.z * aspect)
        elif height > width:
            scale_vector.setX(scale_vector.x / aspect)

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
                avg = float(qRed(qrgb) + qGreen(qrgb) + qBlue(qrgb)) / (3 * 255)
                height_data[y, x] = avg

        Job.yieldThread()

        for i in range(0, blur_iterations):
            ii = blur_iterations-i
            copy = numpy.copy(height_data)

            height_data += numpy.roll(copy, ii, axis=0)
            height_data += numpy.roll(copy, -ii, axis=0)
            height_data += numpy.roll(copy, ii, axis=1)
            height_data += numpy.roll(copy, -ii, axis=1)

            height_data /= 5
            Job.yieldThread()

        height_data *= scale_vector.y
        height_data += base_height

        heightmap_face_count = 2 * height_minus_one * width_minus_one
        total_face_count = heightmap_face_count + (width_minus_one * 2) * (height_minus_one * 2) + 2

        mesh.reserveFaceCount(total_face_count)

        # initialize to texel space vertex offsets
        heightmap_vertices = numpy.zeros(((width - 1) * (height - 1), 6, 3), dtype=numpy.float32)
        heightmap_vertices = heightmap_vertices + numpy.array([[
            [0, base_height, 0],
            [0, base_height, texel_height],
            [texel_width, base_height, texel_height],
            [texel_width, base_height, texel_height],
            [texel_width, base_height, 0],
            [0, base_height, 0]
        ]], dtype=numpy.float32)

        offsetsz, offsetsx = numpy.mgrid[0:height_minus_one, 0:width-1]
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
        mesh.addFace(0, 0, 0, 0, 0, geo_height, geo_width, 0, geo_height)
        mesh.addFace(geo_width, 0, geo_height, geo_width, 0, 0, 0, 0, 0)

        # north and south walls
        for n in range(0, width_minus_one):
            x = n * texel_width
            nx = (n + 1) * texel_width

            hn0 = height_data[0, n]
            hn1 = height_data[0, n + 1]

            hs0 = height_data[height_minus_one, n]
            hs1 = height_data[height_minus_one, n + 1]

            mesh.addFace(x, 0, 0, nx, 0, 0, nx, hn1, 0)
            mesh.addFace(nx, hn1, 0, x, hn0, 0, x, 0, 0)

            mesh.addFace(x, 0, geo_height, nx, 0, geo_height, nx, hs1, geo_height)
            mesh.addFace(nx, hs1, geo_height, x, hs0, geo_height, x, 0, geo_height)

        # west and east walls
        for n in range(0, height_minus_one):
            y = n * texel_height
            ny = (n + 1) * texel_height

            hw0 = height_data[n, 0]
            hw1 = height_data[n + 1, 0]

            he0 = height_data[n, width_minus_one]
            he1 = height_data[n + 1, width_minus_one]

            mesh.addFace(0, 0, y, 0, 0, ny, 0, hw1, ny)
            mesh.addFace(0, hw1, ny, 0, hw0, y, 0, 0, y)

            mesh.addFace(geo_width, 0, y, geo_width, 0, ny, geo_width, he1, ny)
            mesh.addFace(geo_width, he1, ny, geo_width, he0, y, geo_width, 0, y)

        mesh.calculateNormals(fast=True)

        return scene_node
