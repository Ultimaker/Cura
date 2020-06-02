# Copyright (c) 2020 Jaime van Kessel, Ultimaker B.V.
# The PostProcessingPlugin is released under the terms of the AGPLv3 or higher.

# Workaround for a race condition on certain systems where there
# is a race condition between Arcus and PyQt. Importing Arcus
# first seems to prevent Sip from going into a state where it
# tries to create PyQt objects on a non-main thread.
import Arcus  # @UnusedImport
import Savitar  # @UnusedImport

from . import PostProcessingPlugin


def getMetaData():
    return {}

def register(app):
    return {"extension": PostProcessingPlugin.PostProcessingPlugin()}