# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import GCodeFlavor

class GriffinFlavor(GCodeFlavor.GCodeFlavor):

    def __init__(self):
        super().__init__()