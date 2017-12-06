# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Stage import Stage

class CuraStage(Stage):

    def __init__(self):
        super().__init__()

    def getMainView(self):
        return self.getView("main")

    def getSidebarView(self):
        return self.getView("sidebar")
