#Shoopdawoop
from . import CuraEngineBackend

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "type": "backend",
        "plugin": {
            "name": "CuraEngine Backend",
            "author": "Ultimaker",
            "description": catalog.i18nc("CuraEngine backend plugin description", "Provides the link to the CuraEngine slicing backend")
        }
    }

def register(app):
    return { "backend": CuraEngineBackend.CuraEngineBackend() }

