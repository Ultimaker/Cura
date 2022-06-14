# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from .CloudSync.SyncOrchestrator import SyncOrchestrator
from .Marketplace import Marketplace

def getMetaData():
    """
    Extension-type plug-ins don't have any specific metadata being used by Cura.
    """
    return {}


def register(app):
    """
    Register the plug-in object with Uranium.
    """
    return { "extension": [SyncOrchestrator(app), Marketplace()] }
