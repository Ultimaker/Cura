# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import numpy #To process coordinates in bulk.
import numpy.linalg #To project window coordinates onto the scene.
from PyQt5.QtGui import QImage
import qimage2ndarray #To convert QImage to Numpy arrays.

from UM.Application import Application
from UM.Job import Job #The interface we're implementing.
from UM.Logger import Logger

##  Background task to process an image of where the user would like support.
#
#   The coordinates on the cursor are projected onto the scene to place a mesh
#   that creates or removes support.
class ConstructSupportJob(Job):
    def __init__(self, buffer: QImage, depth_image: QImage):
        super().__init__()
        #These parameters need to be obtained outside of the thread so that they are all in sync with the original capture.
        self._buffer = buffer
        self._depth_image = depth_image
        camera = Application.getInstance().getController().getScene().getActiveCamera()
        self._camera_projection = camera.getProjectionMatrix()
        self._camera_transformation = camera.getWorldTransformation()
        self._camera_position = camera.getPosition()

    def run(self):
        Logger.log("d", "Constructing/removing support.")

        to_support = qimage2ndarray.raw_view(self._buffer)
        depth = qimage2ndarray.recarray_view(self._depth_image)
        depth.a = 0 #Discard alpha channel.
        depth = depth.view(dtype = numpy.int32).astype(numpy.float32) #Conflate the R, G and B channels to one 24-bit (cast to 32) float.