# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import cast, Optional

import numpy
from PyQt6.QtCore import Qt

from UM.Application import Application
from UM.Event import Event, MouseEvent, KeyEvent
from UM.Scene.Selection import Selection
from UM.Tool import Tool
from cura.PickingPass import PickingPass


class PaintTool(Tool):
    """Provides the tool to paint meshes.
    """

    def __init__(self) -> None:
        super().__init__()

        self._shortcut_key = Qt.Key.Key_P

        self._node_cache = None
        self._mesh_transformed_cache = None
        self._cache_dirty = True

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

    def _nodeTransformChanged(self, *args) -> None:
        self._cache_dirty = True

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

            node = Selection.getAllSelectedObjects()[0]
            if node is None:
                return False

            if node != self._node_cache:
                if self._node_cache is not None:
                    self._node_cache.transformationChanged.disconnect(self._nodeTransformChanged)
                self._node_cache = node
                self._node_cache.transformationChanged.connect(self._nodeTransformChanged)
            if self._cache_dirty:
                self._cache_dirty = False
                self._mesh_transformed_cache = self._node_cache.getMeshDataTransformed()
            if not self._mesh_transformed_cache:
                return False

            evt = cast(MouseEvent, event)

            self._selection_pass.renderFacesMode()
            face_id = self._selection_pass.getFaceIdAtPosition(evt.x, evt.y)
            if face_id < 0:
                return False

            ppass = PickingPass(camera.getViewportWidth(), camera.getViewportHeight())
            ppass.render()
            pt = ppass.getPickedPosition(evt.x, evt.y).getData()

            va, vb, vc = self._mesh_transformed_cache.getFaceNodes(face_id)
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
