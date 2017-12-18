# Copyright (c) 2017 Aleph Objects, Inc.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.FileHandler.FileReader import FileReader
from UM.Mesh.MeshReader import MeshReader
from UM.i18n import i18nCatalog
from UM.Preferences import Preferences

catalog = i18nCatalog("cura")
from . import MarlinFlavorParser, RepRapFlavorParser

# Class for loading and parsing G-code files
class GCodeReader(MeshReader):

    _flavor_default = "Marlin"
    _flavor_keyword = ";FLAVOR:"
    _flavor_readers_dict = {"RepRap" : RepRapFlavorParser.RepRapFlavorParser(),
                            "Marlin" : MarlinFlavorParser.MarlinFlavorParser()}

    def __init__(self):
        super(GCodeReader, self).__init__()
        self._supported_extensions = [".gcode", ".g"]
        self._flavor_reader = None

        Preferences.getInstance().addPreference("gcodereader/show_caution", True)

    # PreRead is used to get the correct flavor. If not, Marlin is set by default
    def preRead(self, file_name, *args, **kwargs):
        with open(file_name, "r") as file:
            for line in file:
                if line[:len(self._flavor_keyword)] == self._flavor_keyword:
                    try:
                        self._flavor_reader = self._flavor_readers_dict[line[len(self._flavor_keyword):].rstrip()]
                        return FileReader.PreReadResult.accepted
                    except:
                        # If there is no entry in the dictionary for this flavor, just skip and select the by-default flavor
                        break

            # If no flavor is found in the GCode, then we use the by-default
            self._flavor_reader = self._flavor_readers_dict[self._flavor_default]
            return FileReader.PreReadResult.accepted

    def read(self, file_name):
        return self._flavor_reader.processGCodeFile(file_name)
