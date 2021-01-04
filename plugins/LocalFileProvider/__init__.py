# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import LocalFileProvider


def getMetaData():
    return {}

def register(app):
    return { "file_provider": LocalFileProvider.LocalFileProvider() }
