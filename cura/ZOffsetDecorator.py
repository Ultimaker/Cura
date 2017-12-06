from UM.Scene.SceneNodeDecorator import SceneNodeDecorator

##  A decorator that stores the amount an object has been moved below the platform.
class ZOffsetDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        self._z_offset = 0

    def setZOffset(self, offset):
        self._z_offset = offset

    def getZOffset(self):
        return self._z_offset

    def __deepcopy__(self, memo):
        copied_decorator = ZOffsetDecorator()
        copied_decorator.setZOffset(self.getZOffset())
        return copied_decorator
