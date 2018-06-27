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
        support_positions_3d = (support_depths - 1) * direction #We want the support to appear just before the surface, not behind the surface, so - 1.
        support_positions_3d = support_positions_3d.transpose()
        camera_position_data = self._camera_position.getData()
        support_positions_3d = support_positions_3d + camera_position_data

        layer_height = CuraApplication.getInstance().getGlobalContainerStack().getProperty("layer_height", "value")
        support_z_distance = CuraApplication.getInstance().getGlobalContainerStack().getProperty("support_z_distance", "value")

        #Create the vertices for the 3D mesh.
        #This mesh consists of a diamond-shape for each position that we traced.
        n = support_positions_3d.shape[0]
        vertices = support_positions_3d.copy().astype(numpy.float32)
        vertices[:, 2] = vertices[:, 2] - support_z_distance - layer_height #Shift coordinates down so that they rise below the support Z distance and actually produce support.
        vertices = numpy.resize(vertices, (n * 6, support_positions_3d.shape[1])) #Resize will repeat all coordinates 6 times.
        #For each position, create a diamond shape around the position with 6 vertices.
        vertices[n * 0: n * 1, 0] -= support_depths * 0.0025 #First corner (-x, +y).
        vertices[n * 0: n * 1, 2] += support_depths * 0.0025
        vertices[n * 1: n * 2, 0] += support_depths * 0.0025 #Second corner (+x, +y).
        vertices[n * 1: n * 2, 2] += support_depths * 0.0025
        vertices[n * 2: n * 3, 0] -= support_depths * 0.0025 #Third corner (-x, -y).
        vertices[n * 2: n * 3, 2] -= support_depths * 0.0025
        vertices[n * 3: n * 4, 0] += support_depths * 0.0025 #Fourth corner (+x, -y)
        vertices[n * 3: n * 4, 2] -= support_depths * 0.0025
        vertices[n * 4: n * 5, 1] += support_depths * 0.0025 #Top side.
        vertices[n * 5: n * 6, 1] -= support_depths * 0.0025 #Bottom side.

        #Create the faces of the diamond.
        indices = numpy.arange(n, dtype = numpy.int32)
        indices = numpy.kron(indices, numpy.ones((3, 1))).astype(numpy.int32).transpose()
        indices = numpy.resize(indices, (n * 8, 3)) #Creates 8 triangles using 3 times the same vertex, for each position: [[0, 0, 0], [1, 1, 1], ... , [0, 0, 0], [1, 1, 1], ... ]

        #indices[n * 0: n * 1, 0] += n * 0 #First corner.
        indices[n * 0: n * 1, 1] += n * 1 #Second corner.
        indices[n * 0: n * 1, 2] += n * 4 #Top side.

        indices[n * 1: n * 2, 0] += n * 1 #Second corner.
        indices[n * 1: n * 2, 1] += n * 3 #Fourth corner.
        indices[n * 1: n * 2, 2] += n * 4 #Top side.

        indices[n * 2: n * 3, 0] += n * 3 #Fourth corner.
        indices[n * 2: n * 3, 1] += n * 2 #Third corner.
        indices[n * 2: n * 3, 2] += n * 4 #Top side.

        indices[n * 3: n * 4, 0] += n * 2 #Third corner.
        #indices[n * 3: n * 4, 1] += n * 0 #First corner.
        indices[n * 3: n * 4, 2] += n * 4 #Top side.

        indices[n * 4: n * 5, 0] += n * 1 #Second corner.
        #indices[n * 4: n * 5, 1] += n * 0 #First corner.
        indices[n * 4: n * 5, 2] += n * 5 #Bottom side.

        indices[n * 5: n * 6, 0] += n * 3 #Fourth corner.
        indices[n * 5: n * 6, 1] += n * 1 #Second corner.
        indices[n * 5: n * 6, 2] += n * 5 #Bottom side.

        indices[n * 6: n * 7, 0] += n * 2 #Third corner.
        indices[n * 6: n * 7, 1] += n * 3 #Fourth corner.
        indices[n * 6: n * 7, 2] += n * 5 #Bottom side.

        #indices[n * 7: n * 8, 0] += n * 0 #First corner.
        indices[n * 7: n * 8, 1] += n * 2 #Third corner.
        indices[n * 7: n * 8, 2] += n * 5 #Bottom side.

        builder = MeshBuilder()
        builder.addVertices(vertices)
        builder.addIndices(indices)

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