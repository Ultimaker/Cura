# Copyright (c) 2018 Ultimaker B.V.
# Marketplace is released under the terms of the LGPLv3 or higher.

from .src import Marketplace


def getMetaData():
    return {}


def register(app):
    return {"extension": Marketplace.Marketplace(app)}
