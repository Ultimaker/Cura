# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from . import USBPrinterManager
from PyQt5.QtQml import qmlRegisterType, qmlRegisterSingletonType
from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "type": "extension",
        "plugin": {
            "name": i18n_catalog.i18nc("@label", "USB printing"),
            "author": "Ultimaker",
            "version": "1.0",
            "api": 2,
            "description": i18n_catalog.i18nc("@info:whatsthis","Accepts G-Code and sends them to a printer. Plugin can also update firmware.")
        }
    }

def register(app):
    qmlRegisterSingletonType(USBPrinterManager.USBPrinterManager, "UM", 1, 0, "USBPrinterManager", USBPrinterManager.USBPrinterManager.getInstance)
    return {"extension":USBPrinterManager.USBPrinterManager.getInstance(),"output_device": USBPrinterManager.USBPrinterManager.getInstance() }
