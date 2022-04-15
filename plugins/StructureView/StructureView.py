# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, TYPE_CHECKING
import numpy

from cura.CuraApplication import CuraApplication
from cura.CuraView import CuraView
from UM.Mesh.MeshData import MeshData
from UM.PluginRegistry import PluginRegistry

from .StructureNode import StructureNode

if TYPE_CHECKING:
    import pyArcus

class StructureView(CuraView):
    def __init__(self):
        super().__init__(parent = None, use_empty_menu_placeholder = True)
        self._scene_node = None  # type: Optional[StructureNode]  # All structure data will be under this node. Will be generated on first message received (since there is no scene yet at init).
        self._capacity = 3 * 10000  # Start with some allocation to prevent having to reallocate all the time. Preferably a multiple of 3 (for triangles).
        self._vertices = numpy.ndarray((self._capacity, 3), dtype = numpy.single)
        self._indices = numpy.arange(self._capacity * 3, dtype = numpy.int32).reshape((self._capacity, 3))  # Since we're using a triangle list, the indices are simply increasing linearly.
        self._normals = numpy.repeat([[0.0, 1.0, 0.0]], self._capacity, axis = 0)  # All normals are pointing up (to positive Y).
        self._colors = numpy.repeat([[0.0, 0.0, 0.0]], self._capacity, axis = 0)  # No colors yet.
        self._layers = numpy.repeat(-1, self._capacity)  # To mask out certain layers for layer view.

        self._current_index = 0  # type: int  # Where to add new data.

        plugin_registry = PluginRegistry.getInstance()
        self._enabled = "StructureView" not in plugin_registry.getDisabledPlugins()  # Don't influence performance if this plug-in is disabled.
        if self._enabled:
            engine = plugin_registry.getPluginObject("CuraEngineBackend")
            engine.structurePolygonReceived.connect(self._onStructurePolygonReceived)  # type: ignore

        CuraApplication.getInstance().initializationFinished.connect(self._createSceneNode)

    def _createSceneNode(self):
        if not self._scene_node:
            self._scene_node = StructureNode(parent = CuraApplication.getInstance().getController().getScene().getRoot())

    def _onStructurePolygonReceived(self, message: "pyArcus.PythonMessage") -> None:
        """
        Store the structure polygon in the scene node's mesh data when we receive one.
        :param message: A message received from CuraEngine containing a structure polygon.
        """
        num_vertices = int(len(message.points) / 4 / 3)  # Number of bytes, / 4 for bytes per float, / 3 for X, Y and Z coordinates.
        vertex_data = numpy.frombuffer(message.points, dtype = numpy.single)
        vertex_data = numpy.reshape(vertex_data, newshape = (num_vertices, 3))

        if self._current_index + num_vertices >= self._capacity:
            self._reallocate(self._current_index + num_vertices)

        to = self._current_index + num_vertices
        self._vertices[self._current_index:to, 0:3] = vertex_data
        self._colors[self._current_index:to] = [1.0, 0.0, 0.0]  # TODO: Placeholder color red. Use proper colour depending on structure type.
        self._layers[self._current_index:to] = message.layer_index

        self._current_index += num_vertices

        self._updateScene()

    def _reallocate(self, minimum_capacity: int) -> None:
        """
        Increase capacity to be able to hold at least a given amount of vertices.
        """
        new_capacity = self._capacity
        while minimum_capacity > new_capacity:
            new_capacity *= 2

        self._vertices.resize((new_capacity, 3))
        self._indices = numpy.arange(new_capacity).reshape((new_capacity, 3))
        self._normals = numpy.repeat([0, 1, 0], self._capacity, axis = 0)
        self._colors.resize((new_capacity, 3))
        self._layers.resize((new_capacity, ))

        self._capacity = new_capacity

    def _updateScene(self) -> None:
        """
        After receiving new data, makes sure that the data gets visualised in the 3D scene.
        """
        if not self._scene_node:
            return
        self._scene_node.setMeshData(MeshData(
            vertices = self._vertices[0:self._current_index].copy(),
            normals = self._normals[0:self._current_index].copy(),
            indices = self._indices[0:int(self._current_index / 3)].copy(),
            colors = self._colors[0:self._current_index].copy()
        ))
