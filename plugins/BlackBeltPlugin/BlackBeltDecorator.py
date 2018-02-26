# Copyright (c) 2018 fieldOfView
# The Blackbelt plugin is released under the terms of the LGPLv3 or higher.

from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from UM.Application import Application

from UM.Math.Matrix import Matrix

import math

## Decorator for easy access to gantry angle and transform matrix.
class BlackBeltDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        self._gantry_angle = 0
        self._transform_matrix = Matrix()
        self._scene_front_offset = 0

    def calculateTransformData(self):
        global_stack = Application.getInstance().getGlobalContainerStack()

        self._scene_front_offset = 0
        gantry_angle = global_stack.getProperty("blackbelt_gantry_angle", "value")
        if not gantry_angle:
            self._gantry_angle = 0
            self._transform_matrix = Matrix()
            return
        self._gantry_angle = math.radians(float(gantry_angle))

        machine_depth = global_stack.getProperty("machine_depth", "value")

        matrix = Matrix()
        matrix.setColumn(1, [0, 1 / math.tan(self._gantry_angle), 1, (machine_depth / 2) * (1 - math.cos(self._gantry_angle))])
        matrix.setColumn(2, [0, - 1 / math.sin(self._gantry_angle), 0, machine_depth / 2])
        self._transform_matrix = matrix

        # The above magic transform matrix is composed as follows:
        """
        import numpy
        matrix_data = numpy.identity(4)
        matrix_data[2, 2] = 1/math.sin(self._gantry_angle)  # scale Z
        matrix_data[1, 2] = -1/math.tan(self._gantry_angle) # shear ZY
        matrix = Matrix(matrix_data)

        matrix_data = numpy.identity(4)
        # use front buildvolume face instead of bottom face
        matrix_data[1, 1] = 0
        matrix_data[1, 2] = 1
        matrix_data[2, 1] = -1
        matrix_data[2, 2] = 0
        axes_matrix = Matrix(matrix_data)

        matrix.multiply(axes_matrix)

        # bottom face has origin at the center, front face has origin at one side
        matrix.translate(Vector(0, - math.sin(self._gantry_angle) * machine_depth / 2, 0))
        # make sure objects are not transformed to be below the buildplate
        matrix.translate(Vector(0, 0, machine_depth / 2))

        self._transform_matrix = matrix
        """

    def getGantryAngle(self):
        return self._gantry_angle

    def getTransformMatrix(self):
        return self._transform_matrix

    def setSceneFrontOffset(self, front_offset):
        self._scene_front_offset = front_offset

    def getSceneFrontOffset(self):
        return self._scene_front_offset