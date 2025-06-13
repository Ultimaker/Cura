# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import FlavorParser


class RepRapFlavorParser(FlavorParser.FlavorParser):
    """This parser is intended to interpret the RepRap Firmware g-code flavor."""


    def __init__(self):
        super().__init__()

    def processMCode(self, M, line, position, path):
        if M == 82:
            # Set absolute extrusion mode
            self._is_absolute_extrusion = True
        elif M == 83:
            # Set relative extrusion mode
            self._is_absolute_extrusion = False

    def _gCode90(self, position, params, path):
        """Set the absolute positioning

        RepRapFlavor code G90 sets position of X, Y, Z to absolute
        For absolute E, M82 is used
        """
        self._is_absolute_positioning = True
        return position

    def _gCode91(self, position, params, path):
        """Set the relative positioning

        RepRapFlavor code G91 sets position of X, Y, Z to relative
        For relative E, M83 is used
        """
        self._is_absolute_positioning = False
        return position