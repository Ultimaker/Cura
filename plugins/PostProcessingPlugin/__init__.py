# Copyright (c) 2015 Jaime van Kessel, Ultimaker B.V.
# The PostProcessingPlugin is released under the terms of the AGPLv3 or higher.

from . import PostProcessingPlugin
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")
def getMetaData():
    return {}
        
def register(app):
    return {"extension": PostProcessingPlugin.PostProcessingPlugin()}