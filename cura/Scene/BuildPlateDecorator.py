from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from cura.Scene.CuraSceneNode import CuraSceneNode


##  Make a SceneNode build plate aware CuraSceneNode objects all have this decorator.
class BuildPlateDecorator(SceneNodeDecorator):
    def __init__(self, build_plate_number: int = -1) -> None:
        super().__init__()
        self._build_plate_number = build_plate_number
        self.setBuildPlateNumber(build_plate_number)

    def setBuildPlateNumber(self, nr: int) -> None:
        # Make sure that groups are set correctly
        # setBuildPlateForSelection in CuraActions makes sure that no single childs are set.
        self._build_plate_number = nr
        if isinstance(self._node, CuraSceneNode):
            self._node.transformChanged()  # trigger refresh node without introducing a new signal
        if self._node:
            for child in self._node.getChildren():
                child.callDecoration("setBuildPlateNumber", nr)

    def getBuildPlateNumber(self) -> int:
        return self._build_plate_number

    def __deepcopy__(self, memo):
        return BuildPlateDecorator()
