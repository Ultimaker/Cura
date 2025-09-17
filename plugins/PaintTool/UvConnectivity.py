# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import numpy
from random import shuffle
from typing import Set, List, Tuple, Callable

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPolygonF

from UM.Math.Polygon import Polygon
from UM.Mesh.MeshData import MeshData

class UvConnectivity:

    def __init__(self, model: MeshData, uv_model: MeshData) -> None:
        self._model = model
        self._uv_model = uv_model
        self._islands = self._collectIslands()

        # PROBABLY NOT NEEDED: plane_norm, center, axes

        self._island_norms = [None] * len(self._islands)
        self._island_centers = [None] * len(self._islands)
        self._island_axes = [(None, None)] * len(self._islands)
        self._island_large_triangles_3d = [(None, None, None)] * len(self._islands)
        self._island_large_triangles_uv = [(None, None, None)] * len(self._islands)
        self._face_to_island = [-1] * self._model.getFaceCount()
        for island_idx, island in enumerate(self._islands):
            self._island_norms[island_idx], self._island_centers[island_idx], self._island_axes[island_idx], self._island_large_triangles_3d[island_idx], self._island_large_triangles_uv[island_idx] =(
                self._islandToPlane(island))
            for face_idx in island:
                self._face_to_island[face_idx] = island_idx

        self._island_connections = self._connectIslands()
        self._island_polygons = [self._islandToPolygon(island) for island in self._islands]

    def _collectIslands(self) -> List[Set[int]]:
        if self._model.getFaceCount() == 0:
            return []

        islands = []
        found_faces = set()
        for face_id in range(self._model.getFaceCount()):
            if face_id in found_faces:
                continue
            #found_faces.add(face_id)

            active_faces = {face_id}
            island = set()
            while active_faces:
                next_face_id = active_faces.pop()
                if next_face_id in found_faces:
                    continue
                island.add(next_face_id)
                found_faces.add(next_face_id)
                active_faces.update(self._uv_model.getUvFaceNeighbourIDs(next_face_id))

            if len(island) <= 0:
                continue
            islands.append(island)

        return islands

    def _connectIslands(self) -> List[Set[int]]:

        # MAY NOT BE NEEDED?

        island_connections = [set()] * len(self._islands)
        for island_idx, island in enumerate(self._islands):
            for face_idx in island:
                for neighbour_idx in self._uv_model.getUvFaceNeighbourIDs(face_idx):
                    neighbour_island_idx = self._face_to_island[neighbour_idx]
                    if neighbour_island_idx < 0:
                        continue
                    island_connections[island_idx].add(neighbour_island_idx)
                    island_connections[neighbour_island_idx].add(island_idx)
        return island_connections

    def _islandToPlane(self, island: Set[int]) -> (
            Tuple[numpy.ndarray, numpy.ndarray, Tuple[numpy.ndarray, numpy.ndarray], Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray], Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]]):

        # find normal and center
        plane_norm = numpy.array([0.0, 0, 0])
        plane_center = numpy.array([0.0, 0, 0])
        all_points = []
        for face_id in island:
            a, b, c = self._model.getFaceNodes(face_id)
            plane_norm += numpy.linalg.norm(numpy.cross((b - a), (c - a)))
            plane_center += a + b + c

            aa, bb, cc = self._uv_model.getFaceUvCoords(face_id)
            all_points.extend([(aa, a), (bb, b), (cc, c)])

        # PROBABLY NOT NEEDED: plane_norm, center, axes

        plane_norm /= float(len(island))
        plane_center /= len(island) * 3.0

        # fabricate (arbitrary) unit-axes
        axis_up = numpy.array([0, -1.0, 0]) if abs(plane_norm[1]) < abs(plane_norm[2]) else numpy.array([0, 0, 1.0])
        axis_q = numpy.cross(plane_norm, axis_up)
        axis_q /= numpy.linalg.norm(axis_q)
        axis_r = numpy.cross(axis_q, plane_norm)
        axis_r /= numpy.linalg.norm(axis_r)

        # find a 'large enough' triangle (and save it as both the UV and real-world versions, for Barycentric purposes)
        # note that all_points contains duplicates, and this is a randomized process at the moment <- FIXME(s)
        """  # BUGGY?
        shuffle(all_points)
        largest_sqd = -1
        largest_idx = -1
        for i in range(len(all_points) // 3):
            j = i * 3
            len_a = numpy.linalg.norm(all_points[j + 1][0] - all_points[j    ][0])
            len_b = numpy.linalg.norm(all_points[j + 2][0] - all_points[j + 1][0])
            len_c = numpy.linalg.norm(all_points[j    ][0] - all_points[j + 2][0])
            s = (len_a + len_b + len_c) * 0.5
            heron_sqd = s * (s - len_a) * (s - len_b) * (s - len_c)
            if heron_sqd > largest_sqd:
                largest_sqd = heron_sqd
                largest_idx = j
        large_a, large_b, large_c = all_points[largest_idx:largest_idx + 3]   #if len(all_points) > 0 else ((0, 0, 0), (0, 0, 0), (0, 0, 0))
        """
        large_a, large_b, large_c = all_points[0:3]

        return plane_norm, plane_center, (axis_q, axis_r), (large_a[1], large_b[1], large_c[1]), (large_a[0], large_b[0], large_c[0])

    """  # NOT NEEDED
    def pointToIslandPlane(self, island_idx: int, pt: numpy.ndarray) -> numpy.ndarray:
        center = self._island_centers[island_idx]
        norm = self._island_norms[island_idx]
        axes = self._island_axes[island_idx]
        proj_pt = (pt - numpy.dot(norm, pt - center) * norm) - center
        y_coord = numpy.dot(axes[island_idx][0], proj_pt)
        x_coord = numpy.dot(axes[island_idx][1], proj_pt)
        return numpy.array([x_coord, y_coord])
    """

    def _islandToPolygon(self, island: Set[int]) -> QPolygonF:
        res = QPolygonF()

        for face_id in island:
            a, b, c = self._uv_model.getFaceUvCoords(face_id)

            # enlarge triangle _just_ enough so that the union process works (TODO?: does this work without this step?)
            """ # BUGGY?
            center = (a + b + c) / 3
            a = a + ((center - a)/numpy.linalg.norm(center - a)) * 0.0001
            b = b + ((center - b)/numpy.linalg.norm(center - b)) * 0.0001
            c = c + ((center - c)/numpy.linalg.norm(center - c)) * 0.0001
            """

            res = res.united(QPolygonF([QPointF(a[0], a[1]), QPointF(b[0], b[1]), QPointF(c[0], c[1])]))

        return res

    def islandCount(self) -> int:
        return len(self._islands)

    """  # NOT NEEDED
    def islandToProjectedPolygon(self, island_idx: int, func: Callable) -> Polygon:
        res = QPolygonF()

        for face_id in self._islands[island_idx] :
            a, b, c = self._model.getFaceNodes(face_id)

            # enlarge triangle _just_ enough so that the union process works (TODO?: does this work without that step?)
            center = (a + b + c) / 3
            a = func(a + numpy.linalg.norm(center - a) * 0.0001)
            b = func(b + numpy.linalg.norm(center - b) * 0.0001)
            c = func(c + numpy.linalg.norm(center - c) * 0.0001)

            res = res.united(QPolygonF([a, b, c]))

        # FIXME?: Considering that the polygon will need to be converted _to_ QPolyF in the end anyway, should probably remove this.
        poly = []
        for p_idx in range(res.size()):
            poly.append(res.at(p_idx))
        return Polygon(poly)
    """

    @staticmethod
    def _remapBarycentric(triangle_a: Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray], pt: numpy.ndarray, triangle_b: Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]) -> numpy.ndarray:

        a1, b1, c1 = triangle_a
        a2, b2, c2 = triangle_b

        area_full = 0.5 * numpy.linalg.norm(numpy.cross(b1 - a1, c1 - a1))

        if area_full < 1e-6:  # Degenerate triangle
            return a2

        # Area of sub-triangle opposite to vertex [a,b,c]1
        area_a = 0.5 * numpy.linalg.norm(numpy.cross(b1 - pt, c1 - pt))
        area_b = 0.5 * numpy.linalg.norm(numpy.cross(pt - a1, c1 - a1))
        area_c = 0.5 * numpy.linalg.norm(numpy.cross(b1 - a1, pt - a1))

        u = area_a / area_full
        v = area_b / area_full
        w = area_c / area_full

        total = u + v + w
        if abs(total - 1.0) > 1e-6:
            u /= total
            v /= total
            w /= total

        return u * a2 + v * b2 + w * c2

    def pointToIslandUv(self, island_idx: int, pt: numpy.ndarray) -> numpy.ndarray:
        return self._remapBarycentric(self._island_large_triangles_3d[island_idx], pt, self._island_large_triangles_uv[island_idx])

    def islandUvPolygon(self, island_idx: int) -> QPolygonF:
        return self._island_polygons[island_idx]
