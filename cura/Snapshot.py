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
    @staticmethod
    def snapshot(width = 300, height = 300):
        scene = Application.getInstance().getController().getScene()
        active_camera = scene.getActiveCamera()
        render_width, render_height = active_camera.getWindowSize()
        preview_pass = PreviewPass(render_width, render_height)

        root = scene.getRoot()
        camera = Camera("snapshot", root)

        # determine zoom and look at
        bbox = None
        hulls = None
        for node in DepthFirstIterator(root):
            if type(node) == ConvexHullNode:
                print(node)
            if node.callDecoration("isSliceable") and node.getMeshData() and node.isVisible():
                if bbox is None:
                    bbox = node.getBoundingBox()
                else:
                    bbox = bbox + node.getBoundingBox()
                convex_hull = node.getMeshData().getConvexHullTransformedVertices(node.getWorldTransformation())
                if hulls is None:
                    hulls = convex_hull
                else:
                    hulls = numpy.concatenate((hulls, convex_hull), axis = 0)

        if bbox is None:
            bbox = AxisAlignedBox()

        look_at = bbox.center
        size = max(bbox.width, bbox.height, bbox.depth * 0.5)

        # Somehow the aspect ratio is also influenced in reverse by the screen width/height
        # So you have to set it to render_width/render_height to get 1
        projection_matrix = Matrix()
        projection_matrix.setPerspective(30, render_width / render_height, 1, 500)
        camera.setProjectionMatrix(projection_matrix)

        looking_from_offset = Vector(1, 1, 2)
        if size > 0:
            # determine the watch distance depending on the size
            looking_from_offset = looking_from_offset * size * 1.3
        camera.setViewportSize(render_width, render_height)
        camera.setWindowSize(render_width, render_height)
        camera.setPosition(look_at + looking_from_offset)
        camera.lookAt(look_at)

        # we need this for the projection calculation
        hulls4 = numpy.ones((hulls.shape[0], 4))
        hulls4[:, :-1] = hulls
        #position = Vector(10, 10, 10)
        # projected_position = camera.project(position)

        preview_pass.setCamera(camera)
        preview_pass.setSize(render_width, render_height)  # texture size
        preview_pass.render()
        pixel_output = preview_pass.getOutput()

        print("Calculating image coordinates...")
        view = camera.getWorldTransformation().getInverse()
        min_x, max_x, min_y, max_y = render_width, 0, render_height, 0
        for hull_coords in hulls4:
            projected_position = view.getData().dot(hull_coords)
            projected_position2 = projection_matrix.getData().dot(projected_position)
            #xx, yy = camera.project(Vector(data = hull_coords))
            # xx, yy range from -1 to 1
            xx = projected_position2[0] / projected_position2[2] / 2.0
            yy = projected_position2[1] / projected_position2[2] / 2.0
            # x, y 0..render_width/height
            x = int(render_width / 2 + xx * render_width / 2)
            y = int(render_height / 2 + yy * render_height / 2)
            min_x = min(x, min_x)
            max_x = max(x, max_x)
            min_y = min(y, min_y)
            max_y = max(y, max_y)
        print(min_x, max_x, min_y, max_y)

        # print("looping all pixels in python...")
        # min_x_, max_x_, min_y_, max_y_ = render_width, 0, render_height, 0
        # for y in range(int(render_height)):
        #     for x in range(int(render_width)):
        #         color = pixel_output.pixelColor(x, y)
        #         if color.alpha() > 0:
        #             min_x_ = min(x, min_x_)
        #             max_x_ = max(x, max_x_)
        #             min_y_ = min(y, min_y_)
        #             max_y_ = max(y, max_y_)
        # print(min_x_, max_x_, min_y_, max_y_)

        # make it a square
        if max_x - min_x >= max_y - min_y:
            # make y bigger
            min_y, max_y = int((max_y + min_y) / 2 - (max_x - min_x) / 2), int((max_y + min_y) / 2 + (max_x - min_x) / 2)
        else:
            # make x bigger
            min_x, max_x = int((max_x + min_x) / 2 - (max_y - min_y) / 2), int((max_x + min_x) / 2 + (max_y - min_y) / 2)
        copy_pixel_output = pixel_output.copy(min_x, min_y, max_x - min_x, max_y - min_y)

        # Scale it to the correct height
        image = copy_pixel_output.scaledToHeight(height, QtCore.Qt.SmoothTransformation)
        # Then chop of the width
        cropped_image = image.copy(image.width() // 2 - width // 2, 0, width, height)

        return cropped_image
