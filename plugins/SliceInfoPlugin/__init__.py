# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.
from . import SliceInfo
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
    }

def register(app):
    return { "extension": SliceInfo.SliceInfo()}