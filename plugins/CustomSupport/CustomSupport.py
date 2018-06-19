# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt #For shortcut keys and colours.
from PyQt5.QtGui import QBrush, QImage, QPainter, QPen #Drawing on a temporary buffer until we're ready to process the area of custom support.
from typing import Optional, Tuple

from UM.Qt.QtApplication import QtApplication #To change the active view.
from UM.Event import Event, MouseEvent #To register mouse movements.
from UM.Tool import Tool #The interface we're implementing.
from .ConstructSupportJob import ConstructSupportJob #A background task to construct or remove the actual support.

class CustomSupport(Tool):
    brush_size = 20 #Diameter of the brush.

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

    def event(self, event: Event):
        if event.type == Event.ToolActivateEvent:
            active_view = QtApplication.getInstance().getController().getActiveView()
            if active_view is not None:
                self._previous_view = active_view.getPluginId()
            QtApplication.getInstance().getController().setActiveView("SolidView")
            QtApplication.getInstance().getController().disableSelection()
        elif event.type == Event.ToolDeactivateEvent:
            if self._previous_view is not None:
                QtApplication.getInstance().getController().setActiveView(self._previous_view)
                self._previous_view = None
            QtApplication.getInstance().getController().enableSelection()

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
        job = ConstructSupportJob(buffer)
        job.start()

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