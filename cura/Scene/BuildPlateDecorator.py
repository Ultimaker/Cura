from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from UM.Scene.Selection import Selection


class BuildPlateDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        self._build_plate_number = -1

    def setBuildPlateNumber(self, nr):
        self._build_plate_number = nr

    def getBuildPlateNumber(self):
        return self._build_plate_number

    def __deepcopy__(self, memo):
        return BuildPlateDecorator()
