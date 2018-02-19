# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM.Application import Application
from UM.Math.Color import Color
from UM.Resources import Resources

from UM.View.RenderPass import RenderPass
from UM.View.GL.OpenGL import OpenGL
from UM.View.RenderBatch import RenderBatch


from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator

from typing import Optional

MYPY = False
if MYPY:
    from UM.Scene.Camera import Camera


# Make color brighter by normalizing it (maximum factor 2.5 brighter)
# color_list is a list of 4 elements: [r, g, b, a], each element is a float 0..1
def prettier_color(color_list):
    maximum = max(color_list[:3])
    if maximum > 0:
        factor = min(1 / maximum, 2.5)
    else:
        factor = 1.0
    return [min(i * factor, 1.0) for i in color_list]


##  A render pass subclass that renders slicable objects with default parameters.
#   It uses the active camera by default, but it can be overridden to use a different camera.
#
#   This is useful to get a preview image of a scene taken from a different location as the active camera.
class PreviewPass(RenderPass):
    def __init__(self, width: int, height: int):
        super().__init__("preview", width, height, 0)

        self._camera = None  # type: Optional[Camera]

        self._renderer = Application.getInstance().getRenderer()

        self._shader = None
        self._scene = Application.getInstance().getController().getScene()

    #   Set the camera to be used by this render pass
    #   if it's None, the active camera is used
    def setCamera(self, camera: Optional["Camera"]):
        self._camera = camera

    def render(self) -> None:
        if not self._shader:
            self._shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "overhang.shader"))
            self._shader.setUniformValue("u_overhangAngle", 1.0)
            self._shader.setUniformValue("u_ambientColor", [0.1, 0.1, 0.1, 1.0])
            self._shader.setUniformValue("u_specularColor", [0.6, 0.6, 0.6, 1.0])
            self._shader.setUniformValue("u_shininess", 20.0)

        self._gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        self._gl.glClear(self._gl.GL_COLOR_BUFFER_BIT | self._gl.GL_DEPTH_BUFFER_BIT)

        # Create a new batch to be rendered
        batch = RenderBatch(self._shader)

        # Fill up the batch with objects that can be sliced. `
        for node in DepthFirstIterator(self._scene.getRoot()):
            if node.callDecoration("isSliceable") and node.getMeshData() and node.isVisible():
                uniforms = {}
                uniforms["diffuse_color"] = prettier_color(node.getDiffuseColor())
                batch.addItem(node.getWorldTransformation(), node.getMeshData(), uniforms = uniforms)

        self.bind()
        if self._camera is None:
            batch.render(Application.getInstance().getController().getScene().getActiveCamera())
        else:
            batch.render(self._camera)
        self.release()

