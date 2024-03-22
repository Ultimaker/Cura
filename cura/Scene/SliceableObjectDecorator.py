# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Scene.SceneNodeDecorator import SceneNodeDecorator


class SliceableObjectDecorator(SceneNodeDecorator):
    def __init__(self) -> None:
        super().__init__()

    def isSliceable(self) -> bool:
        return True

    def __deepcopy__(self, memo) -> "SliceableObjectDecorator":
        return type(self)()
