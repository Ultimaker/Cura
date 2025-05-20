# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import cast, Optional

import numpy
from PyQt6.QtCore import Qt

from UM.Application import Application
from UM.Event import Event, MouseEvent, KeyEvent
from UM.Tool import Tool
from cura.PickingPass import PickingPass


class PaintTool(Tool):
    """Provides the tool to paint meshes.
    """

    def __init__(self) -> None:
        super().__init__()

        self._shortcut_key = Qt.Key.Key_P

        """
        # CURA-5966 Make sure to render whenever objects get selected/deselected.
        Selection.selectionChanged.connect(self.propertyChanged)
        """

    @staticmethod
    def _get_intersect_ratio_via_pt(a, pt, b, c):
        # compute the intersection of (param) A - pt with (param) B - (param) C

        # compute unit vectors of directions of lines A and B
        udir_a = a - pt
        udir_a /= numpy.linalg.norm(udir_a)
        udir_b = b - c
        udir_b /= numpy.linalg.norm(udir_b)

        # find unit direction vector for line C, which is perpendicular to lines A and B
        udir_res = numpy.cross(udir_b, udir_a)
        udir_res /= numpy.linalg.norm(udir_res)

        # solve system of equations
        rhs = b - a
        lhs = numpy.array([udir_a, -udir_b, udir_res]).T
        solved = numpy.linalg.solve(lhs, rhs)

        # get the ratio
        intersect = ((a + solved[0] * udir_a) + (b + solved[1] * udir_b)) * 0.5
        return numpy.linalg.norm(pt - intersect) / numpy.linalg.norm(a - intersect)

    def event(self, event: Event) -> bool:
        """Handle mouse and keyboard events.

        :param event: The event to handle.
        :return: Whether this event has been caught by this tool (True) or should
        be passed on (False).
        """
        super().event(event)

        # Make sure the displayed values are updated if the bounding box of the selected mesh(es) changes
        if event.type == Event.ToolActivateEvent:
            return False

        if event.type == Event.ToolDeactivateEvent:
            return False

        if event.type == Event.KeyPressEvent and cast(KeyEvent, event).key == KeyEvent.ShiftKey:
            return False

        if event.type == Event.MousePressEvent and self._controller.getToolsEnabled():
            if MouseEvent.LeftButton not in cast(MouseEvent, event).buttons:
                return False
            if not self._selection_pass:
                return False

            camera = self._controller.getScene().getActiveCamera()
            if not camera:
                return False

            evt = cast(MouseEvent, event)

            ppass = PickingPass(self._selection_pass._width, self._selection_pass._height)
            ppass.render()
            pt = ppass.getPickedPosition(evt.x, evt.y).getData()

            self._selection_pass._renderObjectsMode()  # TODO: <- Fix this!

            node_id = self._selection_pass.getIdAtPosition(evt.x, evt.y)
            if node_id is None:
                return False
            node = Application.getInstance().getController().getScene().findObject(node_id)
            if node is None:
                return False

            self._selection_pass._renderFacesMode()  # TODO: <- Fix this!

            face_id = self._selection_pass.getFaceIdAtPosition(evt.x, evt.y)
            if face_id < 0:
                return False

            meshdata = node.getMeshDataTransformed()  # TODO: <- don't forget to optimize, if the mesh hasn't changed (transforms) then it should be reused!
            if not meshdata:
                return False

            va, vb, vc = meshdata.getFaceNodes(face_id)
            ta, tb, tc = node.getMeshData().getFaceUvCoords(face_id)

            # 'Weight' of each vertex that would produce point pt, so we can generate the texture coordinates from the uv ones of the vertices.
            # See (also) https://mathworld.wolfram.com/BarycentricCoordinates.html
            wa = PaintTool._get_intersect_ratio_via_pt(va, pt, vb, vc)
            wb = PaintTool._get_intersect_ratio_via_pt(vb, pt, vc, va)
            wc = PaintTool._get_intersect_ratio_via_pt(vc, pt, va, vb)
            wt = wa + wb + wc
            wa /= wt
            wb /= wt
            wc /= wt
            texcoords = wa * ta + wb * tb + wc * tc

            solidview = Application.getInstance().getController().getActiveView()
            if solidview.getPluginId() != "SolidView":
                return False

            solidview.setUvPixel(texcoords[0], texcoords[1], [255, 128, 0, 255])

            return True

        if event.type == Event.MouseMoveEvent:
            evt = cast(MouseEvent, event)
            return False #True

        if event.type == Event.MouseReleaseEvent:
            return False #True

        return False
