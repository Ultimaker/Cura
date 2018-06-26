# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import math
from PyQt5.QtCore import Qt #For the extra overhang buffer.
from PyQt5.QtGui import QImage #For the extra overhang buffer.
from typing import Optional

from UM.View.View import View
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.Selection import Selection
from UM.Resources import Resources
from UM.Qt.QtApplication import QtApplication
from UM.View.RenderBatch import RenderBatch
from UM.View.GL.Texture import Texture
from UM.Settings.Validator import ValidatorState
from UM.Math.Color import Color
from UM.View.GL.OpenGL import OpenGL

from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.ExtrudersModel import ExtrudersModel

## Standard view for mesh models.

class SolidView(View):
    def __init__(self):
        super().__init__()

        QtApplication.getInstance().getPreferences().addPreference("view/show_overhang", True)

        self._enabled_shader = None
        self._disabled_shader = None
        self._non_printing_shader = None
        self._support_mesh_shader = None

        self._extruders_model = ExtrudersModel()
        self._theme = None

        self._extra_overhang = None #type: Optional[Texture]

    def beginRendering(self):
        scene = self.getController().getScene()
        renderer = self.getRenderer()

        if not self._theme:
            self._theme = QtApplication.getInstance().getTheme()

        if not self._enabled_shader:
            self._enabled_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "overhang.shader"))
            self._enabled_shader.setUniformValue("u_overhangColor", Color(*self._theme.getColor("model_overhang").getRgb()))
        self._enabled_shader.setUniformValue("u_extraOverhang", 0)
        if self._extra_overhang is None:
            self.setExtraOverhang(None)
        self._enabled_shader.setTexture(0, self._extra_overhang)
        self._enabled_shader.setUniformValue("u_windowSize", [QtApplication.getInstance().getMainWindow().width(), QtApplication.getInstance().getMainWindow().height()])

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
            self._support_mesh_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "color.shader"))
            self._support_mesh_shader.setUniformValue("u_color", Color(1.0, 0.0, 0.0, 1.0))

        global_container_stack = QtApplication.getInstance().getGlobalContainerStack()
        if global_container_stack:
            support_extruder_nr = global_container_stack.getExtruderPositionValueWithDefault("support_extruder_nr")
            support_angle_stack = QtApplication.getInstance().getExtruderManager().getExtruderStack(support_extruder_nr)

            if support_angle_stack is not None and QtApplication.getInstance().getPreferences().getValue("view/show_overhang"):
                angle = support_angle_stack.getProperty("support_angle", "value")
                # Make sure the overhang angle is valid before passing it to the shader
                # Note: if the overhang angle is set to its default value, it does not need to get validated (validationState = None)
                if angle is not None and global_container_stack.getProperty("support_angle", "validationState") in [None, ValidatorState.Valid]:
                    self._enabled_shader.setUniformValue("u_overhangAngle", math.cos(math.radians(90 - angle)))
                else:
                    self._enabled_shader.setUniformValue("u_overhangAngle", math.cos(math.radians(0))) #Overhang angle of 0 causes no area at all to be marked as overhang.
            else:
                self._enabled_shader.setUniformValue("u_overhangAngle", math.cos(math.radians(0)))

        for node in DepthFirstIterator(scene.getRoot()):
            if not node.render(renderer):
                if node.getMeshData() and node.isVisible() and not node.callDecoration("getLayerData"):
                    uniforms = {}
                    shade_factor = 1.0

                    per_mesh_stack = node.callDecoration("getStack")

                    extruder_index = node.callDecoration("getActiveExtruderPosition")
                    if extruder_index is None:
                        extruder_index = "0"
                    extruder_index = int(extruder_index)

                    # Use the support extruder instead of the active extruder if this is a support_mesh
                    if per_mesh_stack:
                        if per_mesh_stack.getProperty("support_mesh", "value"):
                            extruder_index = int(global_container_stack.getExtruderPositionValueWithDefault("support_extruder_nr"))

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
                    except ValueError:
                        pass

                    if node.callDecoration("isNonPrintingMesh"):
                        if per_mesh_stack and (per_mesh_stack.getProperty("infill_mesh", "value") or per_mesh_stack.getProperty("cutting_mesh", "value")):
                            renderer.queueNode(node, shader = self._non_printing_shader, uniforms = uniforms, transparent = True)
                        else:
                            renderer.queueNode(node, shader = self._non_printing_shader, transparent = True)
                    elif getattr(node, "_outside_buildarea", False):
                        renderer.queueNode(node, shader = self._disabled_shader)
                    elif per_mesh_stack and per_mesh_stack.getProperty("support_mesh", "value"):
                        renderer.queueNode(node, shader = self._support_mesh_shader, uniforms = uniforms)
                    else:
                        renderer.queueNode(node, shader = self._enabled_shader, uniforms = uniforms)
                if node.callDecoration("isGroup") and Selection.isSelected(node):
                    renderer.queueNode(scene.getRoot(), mesh = node.getBoundingBoxMesh(), mode = RenderBatch.RenderMode.LineLoop)

    def endRendering(self):
        pass

    ##  Change the overlay image that colours extra overhang.
    #   \param extra_overhang_image A new image where white indicates that there
    #   should be extra overhang and black indicates that there should not be
    #   overhang.
    def setExtraOverhang(self, extra_overhang_image: Optional[QImage]) -> None:
        if extra_overhang_image is None:
            extra_overhang_image = QImage(QtApplication.getInstance().getMainWindow().width(), QtApplication.getInstance().getMainWindow().height(), QImage.Format_Grayscale8)
            extra_overhang_image.fill(Qt.black)
        self._extra_overhang = OpenGL.getInstance().createTexture()
        self._extra_overhang.setImage(extra_overhang_image)