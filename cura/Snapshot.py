# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from PyQt5 import QtCore

from cura.PreviewPass import PreviewPass

from UM.Application import Application
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Math.Matrix import Matrix
from UM.Math.Vector import Vector
from UM.Scene.Camera import Camera
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator


class Snapshot:
    @staticmethod
    def snapshot(width = 300, height = 300):
        scene = Application.getInstance().getController().getScene()
        cam = scene.getActiveCamera()
        render_width, render_height = cam.getWindowSize()
        pp = PreviewPass(render_width, render_height)

        root = scene.getRoot()
        camera = Camera("snapshot", root)

        # determine zoom and look at
        bbox = None
        for node in DepthFirstIterator(root):
            if node.callDecoration("isSliceable") and node.getMeshData() and node.isVisible():
                if bbox is None:
                    bbox = node.getBoundingBox()
                else:
                    bbox += node.getBoundingBox()
        if bbox is None:
            bbox = AxisAlignedBox()
        look_at = bbox.center
        size = max(bbox.width, bbox.height, bbox.depth * 0.5)

        looking_from_offset = Vector(1, 1, 2)
        if size > 0:
            # determine the watch distance depending on the size
            looking_from_offset = looking_from_offset * size * 1.3
        camera.setViewportSize(render_width, render_height)
        camera.setWindowSize(render_width, render_height)
        camera.setPosition(look_at + looking_from_offset)
        camera.lookAt(look_at)

        # Somehow the aspect ratio is also influenced in reverse by the screen width/height
        # So you have to set it to render_width/render_height to get 1
        projection_matrix = Matrix()
        projection_matrix.setPerspective(30, render_width / render_height, 1, 500)

        camera.setProjectionMatrix(projection_matrix)

        pp.setCamera(camera)
        pp.setSize(render_width, render_height)  # texture size
        pp.render()
        pixel_output = pp.getOutput()

        # It's a bit annoying that window size has to be taken into account
        if pixel_output.width() >= pixel_output.height():
            # Scale it to the correct height
            image = pixel_output.scaledToHeight(height, QtCore.Qt.SmoothTransformation)
            # Then chop of the width
            cropped_image = image.copy(image.width() // 2 - width // 2, 0, width, height)
        else:
            # Scale it to the correct width
            image = pixel_output.scaledToWidth(width, QtCore.Qt.SmoothTransformation)
            # Then chop of the height
            cropped_image = image.copy(0, image.height() // 2 - height // 2, width, height)

        return cropped_image
        # if cropped_image.save("/home/jack/preview.png"):
        #     print("yooo")
