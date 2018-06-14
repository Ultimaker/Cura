# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt #For shortcut keys.

from UM.Tool import Tool #The interface we're implementing.

class CustomSupport(Tool):
    def __init__(self):
        super().__init__()
        self._shortcut_key = Qt.Key_S