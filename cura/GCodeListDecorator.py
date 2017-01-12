from UM.Scene.SceneNodeDecorator import SceneNodeDecorator


class GCodeListDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        self._gcode_list = []

    def getGCodeList(self):
        return self._gcode_list

    def setGCodeList(self, list):
        self._gcode_list = list
