# Copyright (c) 2017 Ultimaker B.V.
# PluginBrowser is released under the terms of the LGPLv3 or higher.

from . import PluginBrowser


def getMetaData():
    return {}


def register(app):
    return {"extension": PluginBrowser.PluginBrowser()}
