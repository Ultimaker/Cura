# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.i18n import i18nCatalog

from . import FirmwareUpdateChecker

i18n_catalog = i18nCatalog("cura")


def getMetaData():
    return {}


def register(app):
    return {"extension": FirmwareUpdateChecker.FirmwareUpdateChecker()}
