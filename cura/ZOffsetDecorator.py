from UM.Scene.SceneNodeDecorator import SceneNodeDecorator

##  A decorator that stores the amount an object has been moved below the platform.
class ZOffsetDecorator(SceneNodeDecorator):
    def __init__(self):
        self._z_offset = 0

    def setZOffset(self, offset):
        self._z_offset = offset

    def getZOffset(self):
        return self._z_offset
