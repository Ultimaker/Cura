# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import ModelChecker


def getMetaData():
    return {}

def register(app):
    return {"extension": ModelChecker.ModelChecker()}
