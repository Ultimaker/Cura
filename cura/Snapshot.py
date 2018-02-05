# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import numpy

from PyQt5 import QtCore

from cura.PreviewPass import PreviewPass
from cura.Scene import ConvexHullNode

from UM.Application import Application
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Math.Matrix import Matrix
from UM.Math.Vector import Vector
from UM.Mesh.MeshData import transformVertices
from UM.Scene.Camera import Camera
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator


class Snapshot:
    ##  Return a QImage of the scene
    #   Uses PreviewPass that leaves out some elements
    #   Aspect ratio assumes a square
    @staticmethod
    def snapshot(width = 300, height = 300):
        scene = Application.getInstance().getController().getScene()
        active_camera = scene.getActiveCamera()
        render_width, render_height = active_camera.getWindowSize()
        render_width = int(render_width)
        render_height = int(render_height)
        preview_pass = PreviewPass(render_width, render_height)

        root = scene.getRoot()
        camera = Camera("snapshot", root)

        # determine zoom and look at
        bbox = None
        for node in DepthFirstIterator(root):
            if type(node) == ConvexHullNode:
                print(node)
            if node.callDecoration("isSliceable") and node.getMeshData() and node.isVisible():
                if bbox is None:
                    bbox = node.getBoundingBox()
                else:
                    bbox = bbox + node.getBoundingBox()

        if bbox is None:
            bbox = AxisAlignedBox()

        look_at = bbox.center
        # guessed size so the objects are hopefully big
        size = max(bbox.width, bbox.height, bbox.depth * 0.5)

        # Somehow the aspect ratio is also influenced in reverse by the screen width/height
        # So you have to set it to render_width/render_height to get 1
        projection_matrix = Matrix()
        projection_matrix.setPerspective(30, render_width / render_height, 1, 500)
        camera.setProjectionMatrix(projection_matrix)

        # Looking from this direction (x, y, z) in OGL coordinates
        looking_from_offset = Vector(1, 1, 2)
        if size > 0:
            # determine the watch distance depending on the size
            looking_from_offset = looking_from_offset * size * 1.3
        camera.setPosition(look_at + looking_from_offset)
        camera.lookAt(look_at)

        preview_pass.setCamera(camera)
        preview_pass.render()
        pixel_output = preview_pass.getOutput()

        # Look at the resulting image to get a good crop.
        # Get the pixels as byte array
        pixel_array = pixel_output.bits().asarray(pixel_output.byteCount())
        # Convert to numpy array, assume it's 32 bit (it should always be)
        pixels = numpy.frombuffer(pixel_array, dtype=numpy.uint8).reshape([render_height, render_width, 4])
        # Find indices of non zero pixels
        nonzero_pixels = numpy.nonzero(pixels)
        min_y, min_x, min_a_ = numpy.amin(nonzero_pixels, axis=1)
        max_y, max_x, max_a_ = numpy.amax(nonzero_pixels, axis=1)

        # make it a square
        if max_x - min_x >= max_y - min_y:
            # make y bigger
            min_y, max_y = int((max_y + min_y) / 2 - (max_x - min_x) / 2), int((max_y + min_y) / 2 + (max_x - min_x) / 2)
        else:
            # make x bigger
            min_x, max_x = int((max_x + min_x) / 2 - (max_y - min_y) / 2), int((max_x + min_x) / 2 + (max_y - min_y) / 2)
        cropped_image = pixel_output.copy(min_x, min_y, max_x - min_x, max_y - min_y)

        # Scale it to the correct size
        scaled_image = cropped_image.scaled(
            width, height,
            aspectRatioMode = QtCore.Qt.IgnoreAspectRatio,
            transformMode = QtCore.Qt.SmoothTransformation)

        return scaled_image
