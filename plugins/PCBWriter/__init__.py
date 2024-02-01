# Copyright (c) 2024 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import sys

from PyQt6.QtQml import qmlRegisterType

from UM.i18n import i18nCatalog

from . import PCBWriter
from .SettingsExportModel import SettingsExportModel
from .SettingsExportGroup import SettingsExportGroup

i18n_catalog = i18nCatalog("cura")

def getMetaData():
    return {"mesh_writer": {
        "output": [{
            "extension": "pcb",
            "description": i18n_catalog.i18nc("@item:inlistbox", "Pre-Configured Batch file"),
            "mime_type": "application/x-pcb",
            "mode": PCBWriter.PCBWriter.OutputMode.BinaryMode
        }]
    }}

def register(app):
    qmlRegisterType(SettingsExportModel, "PCBWriter", 1, 0, "SettingsExportModel")
    qmlRegisterType(SettingsExportGroup, "PCBWriter", 1, 0, "SettingsExportGroup")

    return {"mesh_writer": PCBWriter.PCBWriter() }
