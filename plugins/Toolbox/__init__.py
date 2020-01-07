# Copyright (c) 2018 Ultimaker B.V.
# Toolbox is released under the terms of the LGPLv3 or higher.

from .src import Toolbox
from plugins.Toolbox.src.CloudSync.CloudPackageChecker import CloudPackageChecker
from .src.CloudSync.SyncOrchestrator import SyncOrchestrator


def getMetaData():
    return {}


def register(app):
    return {
        "extension": [Toolbox.Toolbox(app), SyncOrchestrator(app)]
    }
