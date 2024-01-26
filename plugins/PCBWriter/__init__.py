# Copyright (c) 2024 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import sys

from . import PCBWriter
from UM.i18n import i18nCatalog

i18n_catalog = i18nCatalog("cura")

def getMetaData():
    return {"mesh_writer": {
        "output": [{
            "extension": "pcb",
            "description": i18n_catalog.i18nc("@item:inlistbox", "Pre-Configured Batch file"),
            "mime_type": "application/vnd.um.preconfigured-batch+3mf",
            "mode": PCBWriter.PCBWriter.OutputMode.BinaryMode
        }]
    }}

def register(app):
    return {"mesh_writer": PCBWriter.PCBWriter() }
