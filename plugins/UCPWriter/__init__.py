# Copyright (c) 2017 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.

from . import UCPWriter

from UM.i18n import i18nCatalog

i18n_catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "mesh_writer": {
            "output": [
                {
                    "mime_type": "application/x-ucp",
                    "mode": UCPWriter.UCPWriter.OutputMode.BinaryMode,
                    "extension": "UCP",
                    "description": i18n_catalog.i18nc("@item:inlistbox", "UCP File (WIP)")
                }
            ]
        }
    }

def register(app):
    return { "mesh_writer": UCPWriter.UCPWriter() }
