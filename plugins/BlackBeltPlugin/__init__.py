# Copyright (c) 2017 fieldOfView
# The BlackBeltPlugin is released under the terms of the AGPLv3 or higher.

from . import BlackBeltPlugin
from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("BlackBeltPlugin")

def getMetaData():
    return {}

def register(app):
    return {"extension": BlackBeltPlugin.BlackBeltPlugin()}
