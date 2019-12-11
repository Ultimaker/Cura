# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from .src.DrivePluginExtension import DrivePluginExtension


def getMetaData():
    return {}


def register(app):
    return {"extension": DrivePluginExtension()}
