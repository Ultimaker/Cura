from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from typing import List


class GCodeListDecorator(SceneNodeDecorator):
    def __init__(self) -> None:
        super().__init__()
        self._gcode_list = []  # type: List[str]

    def getGCodeList(self) -> List[str]:
        return self._gcode_list

    def setGCodeList(self, list: List[str]) -> None:
        self._gcode_list = list

    def __deepcopy__(self, memo) -> "GCodeListDecorator":
        copied_decorator = GCodeListDecorator()
        copied_decorator.setGCodeList(self.getGCodeList())
        return copied_decorator
