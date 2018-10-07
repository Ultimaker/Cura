# Copyright (c) 2018 fieldOfView
# The FadeHeightSettingPlugin is released under the terms of the AGPLv3 or higher.

from . import FadeHeightSettingPlugin
from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("FadeHeightSettingPlugin")


def getMetaData():
    return {}

def register(app):
    return {"extension": FadeHeightSettingPlugin.FadeHeightSettingPlugin()}
