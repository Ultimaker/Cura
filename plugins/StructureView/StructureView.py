# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional

from cura.CuraView import CuraView
from cura.Scene.CuraSceneNode import CuraSceneNode
from UM.PluginRegistry import PluginRegistry

class StructureView(CuraView):
    def __init__(self):
        super().__init__(parent = None, use_empty_menu_placeholder = True)
        self._root_node = None  # type: Optional[CuraSceneNode]  # All structure data will be under this node. Will be generated on first message received (since there is no scene yet at init).

        plugin_registry = PluginRegistry.getInstance()
        self._enabled = "StructureView" not in plugin_registry.getDisabledPlugins()  # Don't influence performance if this plug-in is disabled.
        if self._enabled:
            engine = plugin_registry.getPluginObject("CuraEngineBackend")
            engine.structurePolygonReceived.connect(self._onStructurePolygonReceived)  # type: ignore

    def _onStructurePolygonReceived(self, message):
        print("Received structure polygon for layer", message.layer_index)
