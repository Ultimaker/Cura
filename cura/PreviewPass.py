# Copyright (c) 2017 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.

from UM.Application import Application
from UM.View.RenderPass import RenderPass
from UM.Scene.Camera import Camera

##  A render pass subclass that renders everything with default parameters, but can be used with a non-default camera
#
#   This is useful to get a preview image of a scene taken from a different location as the active camera.
class PreviewPass(RenderPass):
    def __init__(self, width, height):
        super().__init__("preview", width, height, 0)

        self._camera = Application.getInstance().getController().getScene().getActiveCamera()
        self._renderer = Application.getInstance().getRenderer()

    #   Override the camera to be used for this render pass
    def setCamera(self, camera: Camera):
        self._camera = camera

    def render(self):
        self.bind()

        for batch in self._renderer.getBatches():
            batch.render(self._camera)

        self.release()
