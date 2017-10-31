# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.View.View import View
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.Selection import Selection
from UM.Resources import Resources
from UM.Application import Application
from UM.Preferences import Preferences
from UM.View.RenderBatch import RenderBatch
from UM.Settings.Validator import ValidatorState
from UM.Math.Color import Color
from UM.View.GL.OpenGL import OpenGL

from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.ExtrudersModel import ExtrudersModel

import math

## Standard view for mesh models.

class SolidView(View):
    def __init__(self):
        super().__init__()

        Preferences.getInstance().addPreference("view/show_overhang", True)

        self._enabled_shader = None
        self._disabled_shader = None

        self._extruders_model = ExtrudersModel()

    def beginRendering(self):
        scene = self.getController().getScene()
        renderer = self.getRenderer()

        if not self._enabled_shader:
            self._enabled_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "overhang.shader"))
            theme = Application.getInstance().getTheme()
            self._enabled_shader.setUniformValue("u_overhangColor", Color(*theme.getColor("model_overhang").getRgb()))

        if not self._disabled_shader:
            self._disabled_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "striped.shader"))
            theme = Application.getInstance().getTheme()
            self._disabled_shader.setUniformValue("u_diffuseColor1", Color(*theme.getColor("model_unslicable").getRgb()))
            self._disabled_shader.setUniformValue("u_diffuseColor2", Color(*theme.getColor("model_unslicable_alt").getRgb()))
            self._disabled_shader.setUniformValue("u_width", 50.0)

        multi_extrusion = False

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            multi_extrusion = global_container_stack.getProperty("machine_extruder_count", "value") > 1

            if multi_extrusion:
                support_extruder_nr = global_container_stack.getProperty("support_extruder_nr", "value")
                support_angle_stack = ExtruderManager.getInstance().getExtruderStack(support_extruder_nr)
                if not support_angle_stack:
                    support_angle_stack = global_container_stack
            else:
                support_angle_stack = global_container_stack

            if Preferences.getInstance().getValue("view/show_overhang"):
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
                if node.getMeshData() and node.isVisible():
                    uniforms = {}
                    shade_factor = 1.0

                    if not multi_extrusion:
                        if global_container_stack:
                            material = global_container_stack.findContainer({ "type": "material" })
                            material_color = material.getMetaDataEntry("color_code", default = self._extruders_model.defaultColors[0]) if material else self._extruders_model.defaultColors[0]
                        else:
                            material_color = self._extruders_model.defaultColors[0]
                    else:
                        # Get color to render this mesh in from ExtrudersModel
                        extruder_index = 0
                        extruder_id = node.callDecoration("getActiveExtruder")
                        if extruder_id:
                            extruder_index = max(0, self._extruders_model.find("id", extruder_id))
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

                    if hasattr(node, "_outside_buildarea"):
                        if node._outside_buildarea:
                            renderer.queueNode(node, shader = self._disabled_shader)
                        else:
                            renderer.queueNode(node, shader = self._enabled_shader, uniforms = uniforms)
                    else:
                        renderer.queueNode(node, material = self._enabled_shader, uniforms = uniforms)
                if node.callDecoration("isGroup") and Selection.isSelected(node):
                    renderer.queueNode(scene.getRoot(), mesh = node.getBoundingBoxMesh(), mode = RenderBatch.RenderMode.LineLoop)

    def endRendering(self):
        pass

    #def _onPreferenceChanged(self, preference):
        #if preference == "view/show_overhang": ## Todo: This a printer only setting. Should be removed from Uranium.
            #self._enabled_material = None
