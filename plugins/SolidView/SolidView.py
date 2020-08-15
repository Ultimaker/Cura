# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os.path
from UM.View.View import View
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.Selection import Selection
from UM.Resources import Resources
from PyQt5.QtGui import QOpenGLContext, QImage
from PyQt5.QtCore import QSize

import numpy as np
import time

from UM.Application import Application
from UM.Logger import Logger
from UM.Message import Message
from UM.Math.Color import Color
from UM.PluginRegistry import PluginRegistry
from UM.Platform import Platform
from UM.Event import Event

from UM.View.RenderBatch import RenderBatch
from UM.View.GL.OpenGL import OpenGL

from UM.i18n import i18nCatalog

from cura.Settings.ExtruderManager import ExtruderManager

from cura import XRayPass

import math

catalog = i18nCatalog("cura")


class SolidView(View):
    """Standard view for mesh models."""

    _show_xray_warning_preference = "view/show_xray_warning"

    def __init__(self):
        super().__init__()
        application = Application.getInstance()
        application.getPreferences().addPreference("view/show_overhang", True)
        application.globalContainerStackChanged.connect(self._onGlobalContainerChanged)
        self._enabled_shader = None
        self._disabled_shader = None
        self._non_printing_shader = None
        self._support_mesh_shader = None

        self._xray_shader = None
        self._xray_pass = None
        self._xray_composite_shader = None
        self._composite_pass = None

        self._extruders_model = None
        self._theme = None
        self._support_angle = 90

        self._global_stack = None

        self._old_composite_shader = None
        self._old_layer_bindings = None

        self._next_xray_checking_time = time.time()
        self._xray_checking_update_time = 30.0 # seconds
        self._xray_warning_cooldown = 60 * 10 # reshow Model error message every 10 minutes
        self._xray_warning_message = Message(
            catalog.i18nc("@info:status", "Your model is not manifold. The highlighted areas indicate either missing or extraneous surfaces."),
            lifetime = 60 * 5, # leave message for 5 minutes
            title = catalog.i18nc("@info:title", "Model errors"),
            option_text = catalog.i18nc("@info:option_text", "Do not show this message again"),
            option_state = False
        )
        self._xray_warning_message.optionToggled.connect(self._onDontAskMeAgain)
        application.getPreferences().addPreference(self._show_xray_warning_preference, True)

        application.engineCreatedSignal.connect(self._onGlobalContainerChanged)

    def _onDontAskMeAgain(self, checked: bool) -> None:
        Application.getInstance().getPreferences().setValue(self._show_xray_warning_preference, not checked)

    def _onGlobalContainerChanged(self) -> None:
        if self._global_stack:
            try:
                self._global_stack.propertyChanged.disconnect(self._onPropertyChanged)
            except TypeError:
                pass
            for extruder_stack in ExtruderManager.getInstance().getActiveExtruderStacks():
                extruder_stack.propertyChanged.disconnect(self._onPropertyChanged)

        self._global_stack = Application.getInstance().getGlobalContainerStack()
        if self._global_stack:
            self._global_stack.propertyChanged.connect(self._onPropertyChanged)
            for extruder_stack in ExtruderManager.getInstance().getActiveExtruderStacks():
                extruder_stack.propertyChanged.connect(self._onPropertyChanged)
            self._onPropertyChanged("support_angle", "value")  # Force an re-evaluation

    def _onPropertyChanged(self, key: str, property_name: str) -> None:
        if key != "support_angle" or property_name != "value":
            return
        # As the rendering is called a *lot* we really, dont want to re-evaluate the property every time. So we store em!
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            support_extruder_nr = int(global_container_stack.getExtruderPositionValueWithDefault("support_extruder_nr"))
            try:
                support_angle_stack = global_container_stack.extruderList[support_extruder_nr]
            except IndexError:
                pass
            else:
                angle = support_angle_stack.getProperty("support_angle", "value")
                if angle is not None:
                    self._support_angle = angle

    def _checkSetup(self):
        if not self._extruders_model:
            self._extruders_model = Application.getInstance().getExtrudersModel()

        if not self._theme:
            self._theme = Application.getInstance().getTheme()

        if not self._enabled_shader:
            self._enabled_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "overhang.shader"))
            self._enabled_shader.setUniformValue("u_overhangColor", Color(*self._theme.getColor("model_overhang").getRgb()))
            self._enabled_shader.setUniformValue("u_renderError", 0.0)

        if not self._disabled_shader:
            self._disabled_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "striped.shader"))
            self._disabled_shader.setUniformValue("u_diffuseColor1", Color(*self._theme.getColor("model_unslicable").getRgb()))
            self._disabled_shader.setUniformValue("u_diffuseColor2", Color(*self._theme.getColor("model_unslicable_alt").getRgb()))
            self._disabled_shader.setUniformValue("u_width", 50.0)

        if not self._non_printing_shader:
            self._non_printing_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "transparent_object.shader"))
            self._non_printing_shader.setUniformValue("u_diffuseColor", Color(*self._theme.getColor("model_non_printing").getRgb()))
            self._non_printing_shader.setUniformValue("u_opacity", 0.6)

        if not self._support_mesh_shader:
            self._support_mesh_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "striped.shader"))
            self._support_mesh_shader.setUniformValue("u_vertical_stripes", True)
            self._support_mesh_shader.setUniformValue("u_width", 5.0)

        if not Application.getInstance().getPreferences().getValue(self._show_xray_warning_preference):
            self._xray_shader = None
            self._xray_composite_shader = None
            if self._composite_pass and 'xray' in self._composite_pass.getLayerBindings():
                self._composite_pass.setLayerBindings(self._old_layer_bindings)
                self._composite_pass.setCompositeShader(self._old_composite_shader)
                self._old_layer_bindings = None
                self._old_composite_shader = None
                self._enabled_shader.setUniformValue("u_renderError", 0.0)  # We don't want any error markers!.
                self._xray_warning_message.hide()
        else:
            if not self._xray_shader:
                self._xray_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "xray.shader"))

            if not self._xray_composite_shader:
                self._xray_composite_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "xray_composite.shader"))
                theme = Application.getInstance().getTheme()
                self._xray_composite_shader.setUniformValue("u_background_color", Color(*theme.getColor("viewport_background").getRgb()))
                self._xray_composite_shader.setUniformValue("u_outline_color", Color(*theme.getColor("model_selection_outline").getRgb()))
                self._xray_composite_shader.setUniformValue("u_flat_error_color_mix", 0.)  # Don't show flat error color in solid-view.

            renderer = self.getRenderer()
            if not self._composite_pass or not 'xray' in self._composite_pass.getLayerBindings():
                # Currently the RenderPass constructor requires a size > 0
                # This should be fixed in RenderPass's constructor.
                self._xray_pass = XRayPass.XRayPass(1, 1)
                self._enabled_shader.setUniformValue("u_renderError", 1.0)  # We don't want any error markers!.
                renderer.addRenderPass(self._xray_pass)

                if not self._composite_pass:
                    self._composite_pass = self.getRenderer().getRenderPass("composite")

                self._old_layer_bindings = self._composite_pass.getLayerBindings()
                self._composite_pass.setLayerBindings(["default", "selection", "xray"])
                self._old_composite_shader = self._composite_pass.getCompositeShader()
                self._composite_pass.setCompositeShader(self._xray_composite_shader)

    def beginRendering(self):
        scene = self.getController().getScene()
        renderer = self.getRenderer()

        self._checkSetup()

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            if Application.getInstance().getPreferences().getValue("view/show_overhang"):
                # Make sure the overhang angle is valid before passing it to the shader
                if self._support_angle >= 0 and self._support_angle <= 90:
                    self._enabled_shader.setUniformValue("u_overhangAngle", math.cos(math.radians(90 - self._support_angle)))
                else:
                    self._enabled_shader.setUniformValue("u_overhangAngle", math.cos(math.radians(0))) #Overhang angle of 0 causes no area at all to be marked as overhang.
            else:
                self._enabled_shader.setUniformValue("u_overhangAngle", math.cos(math.radians(0)))
        disabled_batch = renderer.createRenderBatch(shader = self._disabled_shader)
        normal_object_batch = renderer.createRenderBatch(shader = self._enabled_shader)
        renderer.addRenderBatch(disabled_batch)
        renderer.addRenderBatch(normal_object_batch)
        for node in DepthFirstIterator(scene.getRoot()):
            if node.render(renderer):
                continue

            if node.getMeshData() and node.isVisible():
                uniforms = {}
                shade_factor = 1.0

                per_mesh_stack = node.callDecoration("getStack")

                extruder_index = node.callDecoration("getActiveExtruderPosition")
                if extruder_index is None:
                    extruder_index = "0"
                extruder_index = int(extruder_index)

                try:
                    material_color = self._extruders_model.getItem(extruder_index)["color"]
                except KeyError:
                    material_color = self._extruders_model.defaultColors[0]

                if extruder_index != ExtruderManager.getInstance().activeExtruderIndex:
                    # Shade objects that are printed with the non-active extruder 25% darker
                    shade_factor = 0.6

                try:
                    # Colors are passed as rgb hex strings (eg "#ffffff"), and the shader needs
                    # an rgba list of floats (eg [1.0, 1.0, 1.0, 1.0])
                    uniforms["diffuse_color"] = [
                        shade_factor * int(material_color[1:3], 16) / 255,
                        shade_factor * int(material_color[3:5], 16) / 255,
                        shade_factor * int(material_color[5:7], 16) / 255,
                        1.0
                    ]

                    # Color the currently selected face-id. (Disable for now.)
                    #face = Selection.getHoverFace()
                    uniforms["hover_face"] = -1 #if not face or node != face[0] else face[1]
                except ValueError:
                    pass

                if node.callDecoration("isNonPrintingMesh"):
                    if per_mesh_stack and (node.callDecoration("isInfillMesh") or node.callDecoration("isCuttingMesh")):
                        renderer.queueNode(node, shader = self._non_printing_shader, uniforms = uniforms, transparent = True)
                    else:
                        renderer.queueNode(node, shader = self._non_printing_shader, transparent = True)
                elif getattr(node, "_outside_buildarea", False):
                    disabled_batch.addItem(node.getWorldTransformation(copy = False), node.getMeshData(), normal_transformation = node.getCachedNormalMatrix())
                elif per_mesh_stack and node.callDecoration("isSupportMesh"):
                    # Render support meshes with a vertical stripe that is darker
                    shade_factor = 0.6
                    uniforms["diffuse_color_2"] = [
                        uniforms["diffuse_color"][0] * shade_factor,
                        uniforms["diffuse_color"][1] * shade_factor,
                        uniforms["diffuse_color"][2] * shade_factor,
                        1.0
                    ]
                    renderer.queueNode(node, shader = self._support_mesh_shader, uniforms = uniforms)
                else:
                    normal_object_batch.addItem(node.getWorldTransformation(copy=False), node.getMeshData(), uniforms=uniforms, normal_transformation = node.getCachedNormalMatrix())
            if node.callDecoration("isGroup") and Selection.isSelected(node):
                renderer.queueNode(scene.getRoot(), mesh = node.getBoundingBoxMesh(), mode = RenderBatch.RenderMode.LineLoop)

    def endRendering(self):
        # check whether the xray overlay is showing badness
        if time.time() > self._next_xray_checking_time\
                and Application.getInstance().getPreferences().getValue(self._show_xray_warning_preference):
            self._next_xray_checking_time = time.time() + self._xray_checking_update_time

            xray_img = self._xray_pass.getOutput()
            xray_img = xray_img.convertToFormat(QImage.Format_RGB888)

            # We can't just read the image since the pixels are aligned to internal memory positions.
            # xray_img.byteCount() != xray_img.width() * xray_img.height() * 3
            # The byte count is a little higher sometimes. We need to check the data per line, but fast using Numpy.
            # See https://stackoverflow.com/questions/5810970/get-raw-data-from-qimage for a description of the problem.
            # We can't use that solution though, since it doesn't perform well in Python.
            class QImageArrayView:
                """
                Class that ducktypes to be a Numpy ndarray.
                """
                def __init__(self, qimage):
                    bits_pointer = qimage.bits()
                    if bits_pointer is None:  # If this happens before there is a window.
                        self.__array_interface__ = {
                            "shape": (0, 0),
                            "typestr": "|u4",
                            "data": (0, False),
                            "strides": (1, 3),
                            "version": 3
                        }
                    else:
                        self.__array_interface__ = {
                            "shape": (qimage.height(), qimage.width()),
                            "typestr": "|u4", # Use 4 bytes per pixel rather than 3, since Numpy doesn't support 3.
                            "data": (int(bits_pointer), False),
                            "strides": (qimage.bytesPerLine(), 3),  # This does the magic: For each line, skip the correct number of bytes. Bytes per pixel is always 3 due to QImage.Format.Format_RGB888.
                            "version": 3
                        }
            array = np.asarray(QImageArrayView(xray_img)).view(np.dtype({
                "r": (np.uint8, 0, "red"),
                "g": (np.uint8, 1, "green"),
                "b": (np.uint8, 2, "blue"),
                "a": (np.uint8, 3, "alpha")  # Never filled since QImage was reformatted to RGB888.
            }), np.recarray)
            if np.any(np.mod(array.r, 2)):
                self._next_xray_checking_time = time.time() + self._xray_warning_cooldown
                self._xray_warning_message.show()
                Logger.log("i", "X-Ray overlay found non-manifold pixels.")

    def event(self, event):
        if event.type == Event.ViewDeactivateEvent:
            if self._composite_pass and 'xray' in self._composite_pass.getLayerBindings():
                self.getRenderer().removeRenderPass(self._xray_pass)
                self._composite_pass.setLayerBindings(self._old_layer_bindings)
                self._composite_pass.setCompositeShader(self._old_composite_shader)
                self._xray_warning_message.hide()
