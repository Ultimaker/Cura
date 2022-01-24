from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from typing import List, Optional


class GCodeListDecorator(SceneNodeDecorator):
    def __init__(self) -> None:
        super().__init__()
        self._gcode_list = []  # type: List[str]
        self._filename = None  # type: Optional[str]

    def getGcodeFileName(self) -> Optional[str]:
        return self._filename

    def setGcodeFileName(self, filename: str) -> None:
        self._filename = filename

    def getGCodeList(self) -> List[str]:
        return self._gcode_list

    def setGCodeList(self, gcode_list: List[str]) -> None:
        self._gcode_list = gcode_list

    def __deepcopy__(self, memo) -> "GCodeListDecorator":
        copied_decorator = GCodeListDecorator()
        copied_decorator.setGCodeList(self.getGCodeList())
        return copied_decorator
