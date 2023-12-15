# Copyright (c) 2023 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.
import numpy

from typing import Optional

from PyQt6 import QtCore
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QImage

from UM.Logger import Logger
from cura.PreviewPass import PreviewPass

from UM.Application import Application
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Math.Matrix import Matrix
from UM.Math.Vector import Vector
from UM.Scene.Camera import Camera
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Qt.QtRenderer import QtRenderer

class Snapshot:
    @staticmethod
    def getImageBoundaries(image: QImage):
        # Look at the resulting image to get a good crop.
        # Get the pixels as byte array
        pixel_array = image.bits().asarray(image.sizeInBytes())
        width, height = image.width(), image.height()
        # Convert to numpy array, assume it's 32 bit (it should always be)
        pixels = numpy.frombuffer(pixel_array, dtype=numpy.uint8).reshape([height, width, 4])
        # Find indices of non zero pixels
        nonzero_pixels = numpy.nonzero(pixels)
        min_y, min_x, min_a_ = numpy.amin(nonzero_pixels, axis=1)  # type: ignore
        max_y, max_x, max_a_ = numpy.amax(nonzero_pixels, axis=1)  # type: ignore

        return min_x, max_x, min_y, max_y

    @staticmethod
    def isometricSnapshot(width: int = 300, height: int = 300, *, node: Optional[SceneNode] = None) -> Optional[QImage]:
        """
        Create an isometric snapshot of the scene.

        :param width: width of the aspect ratio default 300
        :param height: height of the aspect ratio default 300
        :param node: node of the scene default is the root of the scene
        :return: None when there is no model on the build plate otherwise it will return an image

        """

        if node is None:
            node = Application.getInstance().getController().getScene().getRoot()

        # the direction the camera is looking at to create the isometric view
        iso_view_dir = Vector(-1, -1, -1).normalized()

        bounds = Snapshot.nodeBounds(node)
        if bounds is None:
            Logger.log("w", "There appears to be nothing to render")
            return None

        camera = Camera("snapshot")

        # find local x and y directional vectors of the camera
        tangent_space_x_direction = iso_view_dir.cross(Vector.Unit_Y).normalized()
        tangent_space_y_direction = tangent_space_x_direction.cross(iso_view_dir).normalized()

        # find extreme screen space coords of the scene
        x_points = [p.dot(tangent_space_x_direction) for p in bounds.points]
        y_points = [p.dot(tangent_space_y_direction) for p in bounds.points]
        min_x = min(x_points)
        max_x = max(x_points)
        min_y = min(y_points)
        max_y = max(y_points)
        camera_width = max_x - min_x
        camera_height = max_y - min_y

        if camera_width == 0 or camera_height == 0:
            Logger.log("w", "There appears to be nothing to render")
            return None

        # increase either width or height to match the aspect ratio of the image
        if camera_width / camera_height > width / height:
            camera_height = camera_width * height / width
        else:
            camera_width = camera_height * width / height

        # Configure camera for isometric view
        ortho_matrix = Matrix()
        ortho_matrix.setOrtho(
            -camera_width / 2,
            camera_width / 2,
            -camera_height / 2,
            camera_height / 2,
            -10000,
            10000
        )
        camera.setPerspective(False)
        camera.setProjectionMatrix(ortho_matrix)
        camera.setPosition(bounds.center)
        camera.lookAt(bounds.center + iso_view_dir)

        # Render the scene
        renderer = QtRenderer()
        render_pass = PreviewPass(width, height, root=node)
        renderer.setViewportSize(width, height)
        renderer.setWindowSize(width, height)
        render_pass.setCamera(camera)
        renderer.addRenderPass(render_pass)
        renderer.beginRendering()
        renderer.render()

        return render_pass.getOutput()

    @staticmethod
    def nodeBounds(root_node: SceneNode) -> Optional[AxisAlignedBox]:
        axis_aligned_box = None
        for node in DepthFirstIterator(root_node):
            if not getattr(node, "_outside_buildarea", False):
                if node.callDecoration(
                        "isSliceable") and node.getMeshData() and node.isVisible() and not node.callDecoration(
                        "isNonThumbnailVisibleMesh"):
                    if axis_aligned_box is None:
                        axis_aligned_box = node.getBoundingBox()
                    else:
                        axis_aligned_box = axis_aligned_box + node.getBoundingBox()
        return axis_aligned_box

    @staticmethod
    def snapshot(width = 300, height = 300):
        """Return a QImage of the scene

        Uses PreviewPass that leaves out some elements Aspect ratio assumes a square

        :param width: width of the aspect ratio default 300
        :param height: height of the aspect ratio default 300
        :return: None when there is no model on the build plate otherwise it will return an image
        """

        scene = Application.getInstance().getController().getScene()
        active_camera = scene.getActiveCamera() or scene.findCamera("3d")
        render_width, render_height = (width, height) if active_camera is None else active_camera.getWindowSize()
        render_width = int(render_width)
        render_height = int(render_height)
        QCoreApplication.processEvents()  # This ensures that the opengl context is correctly available
        preview_pass = PreviewPass(render_width, render_height)

        root = scene.getRoot()
        camera = Camera("snapshot", root)

        # determine zoom and look at
        bbox = Snapshot.nodeBounds(root)
        # If there is no bounding box, it means that there is no model in the buildplate
        if bbox is None:
            Logger.log("w", "Unable to create snapshot as we seem to have an empty buildplate")
            return None

        look_at = bbox.center
        # guessed size so the objects are hopefully big
        size = max(bbox.width, bbox.height, bbox.depth * 0.5)

        # Looking from this direction (x, y, z) in OGL coordinates
        looking_from_offset = Vector(-1, 1, 2)
        if size > 0:
            # determine the watch distance depending on the size
            looking_from_offset = looking_from_offset * size * 1.75
        camera.setPosition(look_at + looking_from_offset)
        camera.lookAt(look_at)

        satisfied = False
        size = None
        fovy = 30

        while not satisfied:
            if size is not None:
                satisfied = True  # always be satisfied after second try
            projection_matrix = Matrix()
            # Somehow the aspect ratio is also influenced in reverse by the screen width/height
            # So you have to set it to render_width/render_height to get 1
            projection_matrix.setPerspective(fovy, render_width / render_height, 1, 500)
            camera.setProjectionMatrix(projection_matrix)
            preview_pass.setCamera(camera)
            preview_pass.render()
            pixel_output = preview_pass.getOutput()
            try:
                min_x, max_x, min_y, max_y = Snapshot.getImageBoundaries(pixel_output)
            except (ValueError, AttributeError):
                Logger.logException("w", "Failed to crop the snapshot!")
                return None

            size = max((max_x - min_x) / render_width, (max_y - min_y) / render_height)
            if size > 0.5 or satisfied:
                satisfied = True
            else:
                # make it big and allow for some empty space around
                fovy *= 0.5  # strangely enough this messes up the aspect ratio: fovy *= size * 1.1

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
            aspectRatioMode = QtCore.Qt.AspectRatioMode.IgnoreAspectRatio,
            transformMode = QtCore.Qt.TransformationMode.SmoothTransformation)

        return scaled_image
