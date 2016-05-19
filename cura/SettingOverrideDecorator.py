# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.
from UM.Scene.SceneNodeDecorator import SceneNodeDecorator


##  A decorator that adds a container stack to a Node. This stack should be queried for all settings regarding
#   the linked node. The Stack in question will refer to the global stack (so that settings that are not defined by
#   this stack still resolve.
class SettingOverrideDecorator(SceneNodeDecorator):

    def __init__(self):
        super().__init__()

