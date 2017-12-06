# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from cura.Stages.CuraStage import CuraStage


##  Stage for monitoring a 3D printing while it's printing.
class MonitorStage(CuraStage):

    def __init__(self):
        super().__init__()
