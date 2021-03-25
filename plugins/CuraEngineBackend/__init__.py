# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

#Shoopdawoop
from . import CuraEngineBackend

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {}

def register(app):
    return { "backend": CuraEngineBackend.CuraEngineBackend(parent = app) }
