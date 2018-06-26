# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import numpy #To process coordinates in bulk.
import numpy.linalg #To project window coordinates onto the scene.
from PyQt5.QtGui import QImage
import qimage2ndarray #To convert QImage to Numpy arrays.

from cura.CuraApplication import CuraApplication
from cura.Scene.BuildPlateDecorator import BuildPlateDecorator #To put the scene node on the correct build plate.
from cura.Scene.CuraSceneNode import CuraSceneNode #To create a scene node that causes the support to be drawn/erased.
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator #To create a scene node that can be sliced.
from UM.Job import Job #The interface we're implementing.
from UM.Logger import Logger
from UM.Math.Vector import Vector #To use the mesh builder.
from UM.Mesh.MeshBuilder import MeshBuilder #To create the support structure in 3D.
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation #To create the scene node.
from UM.Settings.SettingInstance import SettingInstance #To set the correct support overhang angle for the support mesh.

##  Background task to process an image of where the user would like support.
#
#   The coordinates on the cursor are projected onto the scene to place a mesh
#   that creates or removes support.
class ConstructSupportJob(Job):
    def __init__(self, buffer: QImage, depth_image: QImage):
        super().__init__()
        #These parameters need to be obtained outside of the thread so that they are all in sync with the original capture.
        self._buffer = buffer
        self._depth_image = depth_image
        camera = CuraApplication.getInstance().getController().getScene().getActiveCamera()
        self._camera_projection = camera.getProjectionMatrix()
        self._camera_transformation = camera.getWorldTransformation()
        self._camera_position = camera.getPosition()
        self._camera_viewport = numpy.array([camera.getViewportWidth(), camera.getViewportHeight()])
        self._window_size = numpy.array(camera.getWindowSize())

    def run(self):
        Logger.log("d", "Constructing/removing support.")

        to_support = qimage2ndarray.raw_view(self._buffer)
        depth = qimage2ndarray.recarray_view(self._depth_image)
        depth.a = 0 #Discard alpha channel.
        depth = depth.view(dtype = numpy.int32).astype(numpy.float32) / 1000 #Conflate the R, G and B channels to one 24-bit (cast to 32) float. Divide by 1000 to get mm.
        support_positions_2d = numpy.array(numpy.where(numpy.bitwise_and(to_support == 255, depth < 16777))) #All the 2D coordinates on the screen where we want support. The 16777 is for points that don't land on a model.
        support_depths = numpy.take(depth, support_positions_2d[0, :] * depth.shape[1] + support_positions_2d[1, :]) #The depth at those pixels.
        support_positions_2d = support_positions_2d.transpose() #We want rows with pixels, not columns with pixels.
        support_positions_2d[:, [0, 1]] = support_positions_2d[:, [1, 0]] #Swap columns to get OpenGL's coordinate system.
        support_positions_2d = support_positions_2d * 2.0 / self._camera_viewport - 1.0 #Scale to view coordinates (range -1 to 1).
        inverted_projection = numpy.linalg.inv(self._camera_projection.getData())
        transformation = self._camera_transformation.getData()
        transformation[:, 1] = -transformation[:, 1] #Invert Z to get OpenGL's coordinate system.

        #For each pixel, get the near and far plane.
        near = numpy.ndarray((support_positions_2d.shape[0], 4))
        near.fill(1)
        near[0: support_positions_2d.shape[0], 0: support_positions_2d.shape[1]] = support_positions_2d
        near[:, 2].fill(-1)
        near = numpy.dot(inverted_projection, near.transpose())
        near = numpy.dot(transformation, near)
        near = near[0:3] / near[3]
        far = numpy.ndarray((support_positions_2d.shape[0], 4))
        far.fill(1)
        far[0: support_positions_2d.shape[0], 0: support_positions_2d.shape[1]] = support_positions_2d
        far = numpy.dot(inverted_projection, far.transpose())
        far = numpy.dot(transformation, far)
        far = far[0:3] / far[3]

        #Direction is from near plane pixel to far plane pixel, normalised.
        direction = near - far
        direction /= numpy.linalg.norm(direction, axis = 0)

        #Final position is in the direction of the pixel, moving with <depth> mm away from the camera position.
        support_positions_3d = support_depths * direction
        support_positions_3d = support_positions_3d.transpose()
        camera_position_data = self._camera_position.getData()
        support_positions_3d = support_positions_3d + camera_position_data

        #Create the 3D mesh.
        builder = MeshBuilder()
        for index, position in enumerate(support_positions_3d):
            distance = support_depths[index]
            #Create diamonds with a diameter of 1/1000 the distance. Since we use a view depth of 1000mm, this should coincide with exactly 1 pixel (but 2 pixels high; you need some overlap you know...).
            builder.addDiamond(width = 0.001 * distance, height = 0.002 * distance, depth = 0.001 * distance, center = Vector(x = position[0], y = position[1], z = position[2]))

        #Create the scene node.
        scene = CuraApplication.getInstance().getController().getScene()
        new_node = CuraSceneNode(parent = scene.getRoot(), name = "CustomSupport")
        new_node.setSelectable(True)
        new_node.setMeshData(builder.build())
        new_node.addDecorator(BuildPlateDecorator(CuraApplication.getInstance().getMultiBuildPlateModel().activeBuildPlate))
        new_node.addDecorator(SliceableObjectDecorator())

        #Add the appropriate per-object settings.
        stack = new_node.callDecoration("getStack") #Created by SettingOverrideDecorator that is automatically added to CuraSceneNode.
        settings = stack.getTop()
        support_mesh_instance = SettingInstance(stack.getSettingDefinition("support_mesh"), settings)
        support_mesh_instance.setProperty("value", True)
        support_mesh_instance.resetState()
        settings.addInstance(support_mesh_instance)
        drop_down_instance = SettingInstance(stack.getSettingDefinition("support_mesh_drop_down"), settings)
        drop_down_instance.setProperty("value", True)
        drop_down_instance.resetState()
        settings.addInstance(drop_down_instance)

        #Add the scene node to the scene (and allow for undo).
        operation = AddSceneNodeOperation(new_node, scene.getRoot())
        operation.push()

        scene.sceneChanged.emit(new_node)