# Copyright (c) 2017 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.

from UM.Application import Application
from UM.Resources import Resources

from UM.View.RenderPass import RenderPass
from UM.View.GL.OpenGL import OpenGL
from UM.View.RenderBatch import RenderBatch


from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator

from typing import Optional

MYPY = False
if MYPY:
    from UM.Scene.Camera import Camera

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
            self._shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "object.shader"))

        # Create a new batch to be rendered
        batch = RenderBatch(self._shader)

        # Fill up the batch with objects that can be sliced. `
        for node in DepthFirstIterator(self._scene.getRoot()):
            if node.callDecoration("isSliceable") and node.getMeshData() and node.isVisible():
                batch.addItem(node.getWorldTransformation(), node.getMeshData())

        self.bind()
        if self._camera is None:
            batch.render(Application.getInstance().getController().getScene().getActiveCamera())
        else:
            batch.render(self._camera)
        self.release()
