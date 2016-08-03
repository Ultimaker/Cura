# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.PluginRegistry import PluginRegistry
from UM.View.View import View
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Resources import Resources
from UM.Event import Event, KeyEvent
from UM.Scene.Selection import Selection
from UM.Math.Color import Color

from UM.View.GL.OpenGL import OpenGL

from cura.ConvexHullNode import ConvexHullNode

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from . import LayerViewProxy

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

from . import LayerPass

import os.path

## View used to display g-code paths.
class LayerView(View):
    def __init__(self):
        super().__init__()
        self._proxy = LayerViewProxy.LayerViewProxy()

        self._ghost_shader = None
        self._layer_pass = None
        self._composite_pass = None
        self._old_layer_bindings = None
        self._layerview_composite_shader = None
        self._old_composite_shader = None

    def getLayerPass(self):
        if not self._layer_pass:
            # Currently the RenderPass constructor requires a size > 0
            # This should be fixed in RenderPass's constructor.
            self._layer_pass = LayerPass.LayerPass(1, 1)
            self.getRenderer().addRenderPass(self._layer_pass)

        return self._layer_pass

    ##  Hackish way to ensure the proxy is already created, which ensures that the layerview.qml is already created
    #   as this caused some issues.
    def getProxy(self, engine, script_engine):
        return self._proxy

    def beginRendering(self):
        scene = self.getController().getScene()
        renderer = self.getRenderer()

        if not self._ghost_shader:
            self._ghost_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "color.shader"))
            self._ghost_shader.setUniformValue("u_color", Color(32, 32, 32, 96))

        for node in DepthFirstIterator(scene.getRoot()):
            # We do not want to render ConvexHullNode as it conflicts with the bottom layers.
            # However, it is somewhat relevant when the node is selected, so do render it then.
            if type(node) is ConvexHullNode and not Selection.isSelected(node.getWatchedNode()):
                continue

            if not node.render(renderer):
                if node.getMeshData() and node.isVisible():
                    renderer.queueNode(node, transparent = True, shader = self._ghost_shader)

    def endRendering(self):
        pass

    def event(self, event):
        modifiers = QApplication.keyboardModifiers()
        ctrl_is_active = modifiers == Qt.ControlModifier
        if event.type == Event.KeyPressEvent and ctrl_is_active:
            if event.key == KeyEvent.UpKey:
                self.getLayerPass().setLayer(self._current_layer_num + 1)
                return True
            if event.key == KeyEvent.DownKey:
                self.getLayerPass().setLayer(self._current_layer_num - 1)
                return True

        if event.type == Event.ViewActivateEvent:
            # Make sure the LayerPass is created
            self.getLayerPass()

            if not self._layerview_composite_shader:
                self._layerview_composite_shader = OpenGL.getInstance().createShaderProgram(os.path.join(PluginRegistry.getInstance().getPluginPath("LayerView"), "layerview_composite.shader"))

            if not self._composite_pass:
                self._composite_pass = self.getRenderer().getRenderPass("composite")

            self._old_layer_bindings = self._composite_pass.getLayerBindings()
            layer_bindings = self._old_layer_bindings[:] # make a copy
            layer_bindings.append("layerview")
            self._composite_pass.setLayerBindings(layer_bindings)
            self._old_composite_shader = self._composite_pass.getCompositeShader()
            self._composite_pass.setCompositeShader(self._layerview_composite_shader)

        if event.type == Event.ViewDeactivateEvent:
            self._composite_pass.setLayerBindings(self._old_layer_bindings)
            self._composite_pass.setCompositeShader(self._old_composite_shader)
