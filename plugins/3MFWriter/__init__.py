# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.i18n import i18nCatalog
from . import ThreeMFWorkspaceWriter
from . import ThreeMFWriter

i18n_catalog = i18nCatalog("uranium")

def getMetaData():
    return {
        "plugin": {
            "name": i18n_catalog.i18nc("@label", "3MF Writer"),
            "author": "Ultimaker",
            "version": "1.0",
            "description": i18n_catalog.i18nc("@info:whatsthis", "Provides support for writing 3MF files."),
            "api": 3
        },
        "mesh_writer": {
            "output": [{
                "extension": "3mf",
                "description": i18n_catalog.i18nc("@item:inlistbox", "3MF file"),
                "mime_type": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml",
                "mode": ThreeMFWriter.ThreeMFWriter.OutputMode.BinaryMode
            }]
        },
        "workspace_writer": {
            "output": [{
                "extension": "3mf",
                "description": i18n_catalog.i18nc("@item:inlistbox", "3MF file"),
                "mime_type": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml",
                "mode": ThreeMFWorkspaceWriter.ThreeMFWorkspaceWriter.OutputMode.BinaryMode
            }]
        }
    }

def register(app):
    return {"mesh_writer": ThreeMFWriter.ThreeMFWriter(), "workspace_writer": ThreeMFWorkspaceWriter.ThreeMFWorkspaceWriter()}
