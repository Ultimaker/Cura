from UM.Math.Matrix import Matrix
from UM.Math.Vector import Vector

from cura.CuraApplication import CuraApplication
from cura.Scene.CuraSceneNode import CuraSceneNode

from typing import Optional

class FlavorParserPatches():
    def __init__(self, flavor_parser):
        self._flavor_parser = flavor_parser

        self.__processGCodeStream = self._flavor_parser.processGCodeStream
        self._flavor_parser.processGCodeStream = self.processGCodeStream

    # Calls original FlavorParser.processGCodeStream and untransform the parsed layers if necessary
    def processGCodeStream(self, stream: str) -> Optional[CuraSceneNode]:
        scene_node = self.__processGCodeStream(stream)
        if not scene_node:
            return None

        root = CuraApplication.getInstance().getController().getScene().getRoot()
        root.callDecoration("calculateTransformData")
        transform = root.callDecoration("getTransformMatrix")

        if transform and transform != Matrix():
            transform_matrix = scene_node.getLocalTransformation().preMultiply(transform.getInverse())
            scene_node.setTransformation(transform_matrix)

            bounding_box = scene_node.getBoundingBox()
            scene_node.translate(Vector(0, 0, -bounding_box.back), CuraSceneNode.TransformSpace.World)

        return scene_node