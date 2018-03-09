# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser #To parse preference files.
import io #To serialise the preference files afterwards.

from UM.VersionUpgrade import VersionUpgrade #We're inheriting from this.

##  Upgrades configurations from the state they were in at version 3.2 to the
#   state they should be in at version 3.3.
class VersionUpgrade32to33(VersionUpgrade):
    ##  Gets the version number from a CFG file.
    def getCfgVersion(self, serialized):
        raise NotImplementedError("This has not yet been implemented.")

    ##  Upgrades a quality container to the new format.
    def upgradeQuality(self, serialized, filename):
        raise NotImplementedError("This has not yet been implemented.")