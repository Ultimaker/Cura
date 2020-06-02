from UM.Scene.SceneNodeDecorator import SceneNodeDecorator


class ZOffsetDecorator(SceneNodeDecorator):
    """A decorator that stores the amount an object has been moved below the platform."""

    def __init__(self) -> None:
        super().__init__()
        self._z_offset = 0.

    def setZOffset(self, offset: float) -> None:
        self._z_offset = offset

    def getZOffset(self) -> float:
        return self._z_offset

    def __deepcopy__(self, memo) -> "ZOffsetDecorator":
        copied_decorator = ZOffsetDecorator()
        copied_decorator.setZOffset(self.getZOffset())
        return copied_decorator
