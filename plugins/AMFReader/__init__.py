# Copyright (c) 2019 fieldOfView
# Cura is released under the terms of the LGPLv3 or higher.

from . import AMFReader

def getMetaData():
    return {}

def register(app):
    return {"mesh_reader": AMFReader.AMFReader()}
