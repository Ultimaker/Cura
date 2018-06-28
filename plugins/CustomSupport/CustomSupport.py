# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import math #To create the circular cursor.
import numpy #To process coordinates in bulk.
import numpy.linalg #To project window coordinates onto the scene.
from PyQt5.QtCore import Qt #For shortcut keys and colours.
from PyQt5.QtGui import QBrush, QColor, QCursor, QImage, QPainter, QPen, QPixmap #Drawing on a temporary buffer until we're ready to process the area of custom support, and changing the cursor.
import qimage2ndarray #To convert QImage to Numpy arrays.
from typing import Optional, Tuple

from cura.CuraApplication import CuraApplication #To get the camera and settings.
from cura.Operations.SetParentOperation import SetParentOperation #To make the support move along with whatever it is drawn on.
from cura.PickingPass import PickingPass
from cura.Scene.BuildPlateDecorator import BuildPlateDecorator #To put the scene node on the correct build plate.
from cura.Scene.CuraSceneNode import CuraSceneNode #To create a scene node that causes the support to be drawn/erased.
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator #To create a scene node that can be sliced.
from UM.Event import Event, MouseEvent #To register mouse movements.
from UM.Logger import Logger
from UM.Mesh.MeshBuilder import MeshBuilder #To create the support structure in 3D.
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation #To create the scene node.
from UM.Operations.GroupedOperation import GroupedOperation #To create the scene node.
from UM.Qt.QtApplication import QtApplication #To change the active view.
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator #To find the parent node to link custom support to.
from UM.Settings.SettingInstance import SettingInstance #To set the correct support overhang angle for the support mesh.
from UM.Tool import Tool #The interface we're implementing.

class CustomSupport(Tool):
    #Diameter of the brush.
    brush_size = 20

    #Size of each piece of the support mesh in pixels.
    #If you make this too small you can't create support since it'll be less
    #than a layer high or less than a line wide. If you make this too large the
    #drawing will be inaccurate.
    globule_size = 1.5

    def __init__(self):
        super().__init__()
        self._shortcut_key = Qt.Key_S
        self._previous_view = None #type: Optional[str] #This tool forces SolidView. When the tool is disabled, it goes back to the original view.

        self._draw_buffer = None #type: Optional[QImage] #An image to temporarily draw support on until we've processed the draw command completely.
        self._painter = None #type: Optional[QPainter] #A pen tool that paints on the draw buffer.
        self._last_x = 0 #type: int #The last position that was drawn in the previous frame, if we are currently drawing.
        self._last_y = 0 #type: int
        self._endcap_pen = QPen(Qt.white) #type: QPen #Pen to use for the end caps of the drawn line. This draws a circle when pressing and releasing the mouse.
        self._line_pen = QPen(Qt.white) #type: QPen #Pen to use for drawing connecting lines while dragging the mouse.
        self._line_pen.setWidth(self.brush_size)
        self._line_pen.setCapStyle(Qt.RoundCap)

        #Create the cursor.
        cursor_image = QImage(self.brush_size, self.brush_size, QImage.Format_ARGB32)
        cursor_image.fill(QColor(0, 0, 0, 0))
        for angle in (i / 2 / math.pi for i in range(4 * self.brush_size)):
            x = int(math.cos(angle) * self.brush_size / 2 + self.brush_size / 2)
            y = int(math.sin(angle) * self.brush_size / 2 + self.brush_size / 2)
            cursor_image.setPixelColor(x, y, QColor(128, 128, 128, 255))
        cursor_bitmap = QPixmap.fromImage(cursor_image)
        self._cursor = QCursor(cursor_bitmap)

    def event(self, event: Event):
        if event.type == Event.ToolActivateEvent:
            active_view = QtApplication.getInstance().getController().getActiveView()
            if active_view is not None:
                self._previous_view = active_view.getPluginId()
            QtApplication.getInstance().getController().setActiveView("SolidView")
            QtApplication.getInstance().getController().disableSelection()
            QtApplication.getInstance().setOverrideCursor(self._cursor)
        elif event.type == Event.ToolDeactivateEvent:
            if self._previous_view is not None:
                QtApplication.getInstance().getController().setActiveView(self._previous_view)
                self._previous_view = None
            QtApplication.getInstance().getController().enableSelection()
            QtApplication.getInstance().restoreOverrideCursor()

        elif event.type == Event.MousePressEvent and MouseEvent.LeftButton in event.buttons:
            #Reset the draw buffer and start painting.
            self._draw_buffer = QImage(QtApplication.getInstance().getMainWindow().width(), QtApplication.getInstance().getMainWindow().height(), QImage.Format_Grayscale8)
            self._draw_buffer.fill(Qt.black)
            self._painter = QPainter(self._draw_buffer)
            self._painter.setBrush(QBrush(Qt.white))
            self._painter.setPen(self._endcap_pen)
            self._last_x, self._last_y = self._cursorCoordinates()
            self._painter.drawEllipse(self._last_x - self.brush_size / 2, self._last_y - self.brush_size / 2, self.brush_size, self.brush_size) #Paint an initial ellipse at the spot you're clicking.
            QtApplication.getInstance().getController().getView("SolidView").setExtraOverhang(self._draw_buffer)
        elif event.type == Event.MouseReleaseEvent and MouseEvent.LeftButton in event.buttons:
            #Complete drawing.
            self._last_x, self._last_y = self._cursorCoordinates()
            if self._painter:
                self._painter.setPen(self._endcap_pen)
                self._painter.drawEllipse(self._last_x - self.brush_size / 2, self._last_y - self.brush_size / 2, self.brush_size, self.brush_size) #Paint another ellipse when you're releasing as endcap.
                self._painter = None
            QtApplication.getInstance().getController().getView("SolidView").setExtraOverhang(self._draw_buffer)
            self._constructSupport(self._draw_buffer) #Actually place the support.
            self._resetDrawBuffer()
        elif event.type == Event.MouseMoveEvent and self._painter is not None: #While dragging.
            self._painter.setPen(self._line_pen)
            new_x, new_y = self._cursorCoordinates()
            self._painter.drawLine(self._last_x, self._last_y, new_x, new_y)
            self._last_x = new_x
            self._last_y = new_y
            QtApplication.getInstance().getController().getView("SolidView").setExtraOverhang(self._draw_buffer)

    ##  Construct the actual support intersection structure from an image.
    #   \param buffer The temporary buffer indicating where support should be
    #   added and where it should be removed.
    def _constructSupport(self, buffer: QImage) -> None:
        depth_pass = PickingPass(buffer.width(), buffer.height()) #Instead of using the picking pass to pick for us, we need to bulk-pick digits so do this in Numpy.
        depth_pass.render()
        depth_image = depth_pass.getOutput()
        camera = CuraApplication.getInstance().getController().getScene().getActiveCamera()

        to_support = qimage2ndarray.raw_view(buffer)
        depth = qimage2ndarray.recarray_view(depth_image)
        depth.a = 0 #Discard alpha channel.
        depth = depth.view(dtype = numpy.int32).astype(numpy.float32) / 1000 #Conflate the R, G and B channels to one 24-bit (cast to 32) float. Divide by 1000 to get mm.
        support_positions_2d = numpy.array(numpy.where(numpy.bitwise_and(to_support == 255, depth < 16777))) #All the 2D coordinates on the screen where we want support. The 16777 is for points that don't land on a model.
        support_depths = numpy.take(depth, support_positions_2d[0, :] * depth.shape[1] + support_positions_2d[1, :]) #The depth at those pixels.
        support_positions_2d = support_positions_2d.transpose() #We want rows with pixels, not columns with pixels.
        if len(support_positions_2d) == 0:
            Logger.log("i", "Support was not drawn on the surface of any objects. Not creating support.")
            return
        support_positions_2d[:, [0, 1]] = support_positions_2d[:, [1, 0]] #Swap columns to get OpenGL's coordinate system.
        camera_viewport = numpy.array([camera.getViewportWidth(), camera.getViewportHeight()])
        support_positions_2d = support_positions_2d * 2.0 / camera_viewport - 1.0 #Scale to view coordinates (range -1 to 1).
        inverted_projection = numpy.linalg.inv(camera.getProjectionMatrix().getData())
        transformation = camera.getWorldTransformation().getData()
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
        camera_position_data = camera.getPosition().getData()
        support_positions_3d = support_positions_3d + camera_position_data

        #Create the vertices for the 3D mesh.
        #This mesh consists of a diamond-shape for each position that we traced.
        n = support_positions_3d.shape[0]
        Logger.log("i", "Adding support in {num_pixels} locations.".format(num_pixels = n))
        vertices = support_positions_3d.copy().astype(numpy.float32)
        vertices = numpy.resize(vertices, (n * 6, support_positions_3d.shape[1])) #Resize will repeat all coordinates 6 times.
        #For each position, create a diamond shape around the position with 6 vertices.
        vertices[n * 0: n * 1, 0] -= support_depths * 0.001 * self.globule_size #First corner (-x, +y).
        vertices[n * 0: n * 1, 2] += support_depths * 0.001 * self.globule_size
        vertices[n * 1: n * 2, 0] += support_depths * 0.001 * self.globule_size #Second corner (+x, +y).
        vertices[n * 1: n * 2, 2] += support_depths * 0.001 * self.globule_size
        vertices[n * 2: n * 3, 0] -= support_depths * 0.001 * self.globule_size #Third corner (-x, -y).
        vertices[n * 2: n * 3, 2] -= support_depths * 0.001 * self.globule_size
        vertices[n * 3: n * 4, 0] += support_depths * 0.001 * self.globule_size #Fourth corner (+x, -y)
        vertices[n * 3: n * 4, 2] -= support_depths * 0.001 * self.globule_size
        vertices[n * 4: n * 5, 1] += support_depths * 0.001 * self.globule_size #Top side.
        vertices[n * 5: n * 6, 1] -= support_depths * 0.001 * self.globule_size #Bottom side.

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
        new_node.setSelectable(False)
        new_node.setMeshData(builder.build())
        new_node.addDecorator(BuildPlateDecorator(CuraApplication.getInstance().getMultiBuildPlateModel().activeBuildPlate))
        new_node.addDecorator(SliceableObjectDecorator())
        operation = GroupedOperation()

        #Figure out which mesh this piece of support belongs to.
        #TODO: You can draw support in one stroke over multiple meshes. The support would belong to an arbitrary one of these.
        selection_pass = CuraApplication.getInstance().getRenderer().getRenderPass("selection")
        parent_id = selection_pass.getIdAtPosition(support_positions_2d[0][0], support_positions_2d[0][1]) #Find the selection under the first support pixel.
        parent_node = scene.getRoot()
        if not parent_id:
            Logger.log("d", "Can't link custom support to any scene node.")
        else:
            for node in BreadthFirstIterator(scene.getRoot()):
                if id(node) == parent_id:
                    parent_node = node
                    break

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
        operation.addOperation(AddSceneNodeOperation(new_node, scene.getRoot())) #Set the parent to root initially, then change the parent, so that we don't have to alter the transformation.
        operation.addOperation(SetParentOperation(new_node, parent_node))
        operation.push()

        scene.sceneChanged.emit(new_node)

    ##  Resets the draw buffer so that no pixels are marked as needing support.
    def _resetDrawBuffer(self) -> None:
        #Create a new buffer so that we don't change the data of a job that's still processing.
        self._draw_buffer = QImage(QtApplication.getInstance().getMainWindow().width(), QtApplication.getInstance().getMainWindow().height(), QImage.Format_Grayscale8)
        self._draw_buffer.fill(Qt.black)
        QtApplication.getInstance().getController().getView("SolidView").setExtraOverhang(self._draw_buffer)
        QtApplication.getInstance().getMainWindow().update() #Force a redraw.

    ##  Get the current mouse coordinates.
    #   \return A tuple containing first the X coordinate and then the Y
    #   coordinate.
    def _cursorCoordinates(self) -> Tuple[int, int]:
        return QtApplication.getInstance().getMainWindow().mouseX, QtApplication.getInstance().getMainWindow().mouseY