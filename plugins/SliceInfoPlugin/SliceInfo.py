# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Extension import Extension
from UM.Application import Application

class SliceInfo(Extension):
    def __init__(self):
        super().__init__()
        Application.getInstance().getOutputDeviceManager().writeStarted.connect(self._onWriteStarted)

    def _onWriteStarted(self, output_device):
        print("Write started")
        pass