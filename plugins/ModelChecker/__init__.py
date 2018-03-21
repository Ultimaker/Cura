# Copyright (c) 2018 Ultimaker B.V.
# This example is released under the terms of the AGPLv3 or higher.

from . import ModelChecker

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")


def getMetaData():
    return {}

def register(app):
    return { "extension": ModelChecker.ModelChecker() }
