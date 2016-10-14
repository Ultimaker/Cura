# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from . import MachineSettingsAction

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "Machine Settings action"),
            "author": "fieldOfView",
            "version": "1.0",
            "description": catalog.i18nc("@info:whatsthis", "Provides a way to change machine settings (such as build volume, nozzle size, etc)"),
            "api": 3
        }
    }

def register(app):
    return { "machine_action": MachineSettingsAction.MachineSettingsAction() }
