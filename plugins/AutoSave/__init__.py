# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import AutoSave

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {}

def register(app):
    return { "extension": AutoSave.AutoSave() }
