# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.View.View import View
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.Selection import Selection
from UM.Resources import Resources
from UM.Application import Application
from UM.View.RenderBatch import RenderBatch
from UM.Math.Color import Color
from UM.View.GL.OpenGL import OpenGL

from cura.Settings.ExtruderManager import ExtruderManager

import math

## Standard view for mesh models.

class SolidView(View):
    def __init__(self):
        super().__init__()
        application = Application.getInstance()
        application.getPreferences().addPreference("view/show_overhang", True)
        application.globalContainerStackChanged.connect(self._onGlobalContainerChanged)
        self._enabled_shader = None
        self._disabled_shader = None
        self._non_printing_shader = None
        self._support_mesh_shader = None

        self._extruders_model = None
        self._theme = None
        self._support_angle = 90

        self._global_stack = None

        Application.getInstance().engineCreatedSignal.connect(self._onGlobalContainerChanged)

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
            support_extruder_nr = global_container_stack.getExtruderPositionValueWithDefault("support_extruder_nr")
            support_angle_stack = global_container_stack.extruders.get(str(support_extruder_nr))
            if support_angle_stack:
                self._support_angle = support_angle_stack.getProperty("support_angle", "value")

    def beginRendering(self):
        scene = self.getController().getScene()
        renderer = self.getRenderer()

        if not self._extruders_model:
            self._extruders_model = Application.getInstance().getExtrudersModel()

        if not self._theme:
            self._theme = Application.getInstance().getTheme()

        if not self._enabled_shader:
            self._enabled_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "overhang.shader"))
            self._enabled_shader.setUniformValue("u_overhangColor", Color(*self._theme.getColor("model_overhang").getRgb()))

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

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            if Application.getInstance().getPreferences().getValue("view/show_overhang"):
                # Make sure the overhang angle is valid before passing it to the shader
                if self._support_angle is not None and self._support_angle >= 0 and self._support_angle <= 90:
                    self._enabled_shader.setUniformValue("u_overhangAngle", math.cos(math.radians(90 - self._support_angle)))
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

                        # Color the currently selected face-id.
                        face = Selection.getSelectedFace()
                        uniforms["selected_face"] = Selection.getEndFaceSelectionId() if not face or node != face[0] else face[1]
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
                        renderer.queueNode(node, shader = self._enabled_shader, uniforms = uniforms)
                if node.callDecoration("isGroup") and Selection.isSelected(node):
                    renderer.queueNode(scene.getRoot(), mesh = node.getBoundingBoxMesh(), mode = RenderBatch.RenderMode.LineLoop)

    def endRendering(self):
        pass
