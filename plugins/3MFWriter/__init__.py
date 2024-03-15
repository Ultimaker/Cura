# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.
import sys

from PyQt6.QtQml import qmlRegisterType

from UM.Logger import Logger
try:
    from . import ThreeMFWriter
    from .SettingsExportGroup import SettingsExportGroup
    threemf_writer_was_imported = True
except ImportError:
    Logger.log("w", "Could not import ThreeMFWriter; libSavitar may be missing")
    threemf_writer_was_imported = False

from . import ThreeMFWorkspaceWriter
from UM.i18n import i18nCatalog

i18n_catalog = i18nCatalog("cura")


def getMetaData():
    workspace_extension = "3mf"

    metaData = {}

    if threemf_writer_was_imported:
        metaData["mesh_writer"] = {
            "output": [
                {
                    "extension": "3mf",
                    "description": i18n_catalog.i18nc("@item:inlistbox", "3MF file"),
                    "mime_type": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml",
                    "mode": ThreeMFWriter.ThreeMFWriter.OutputMode.BinaryMode
                },
            ]
        }
        metaData["workspace_writer"] = {
            "output": [
                {
                    "extension": workspace_extension,
                    "description": i18n_catalog.i18nc("@item:inlistbox", "Cura Project 3MF file"),
                    "mime_type": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml",
                    "mode": ThreeMFWorkspaceWriter.ThreeMFWorkspaceWriter.OutputMode.BinaryMode
                },
                {
                    "extension": "3mf",
                    "description": i18n_catalog.i18nc("@item:inlistbox", "Universal Cura Project"),
                    "mime_type": "application/x-ucp",
                    "mode": ThreeMFWorkspaceWriter.ThreeMFWorkspaceWriter.OutputMode.BinaryMode
                }
            ]
        }

    return metaData


def register(app):
    if "3MFWriter.ThreeMFWriter" in sys.modules:
        qmlRegisterType(SettingsExportGroup, "ThreeMFWriter", 1, 0, "SettingsExportGroup")

        return {"mesh_writer": ThreeMFWriter.ThreeMFWriter(), 
                "workspace_writer": ThreeMFWorkspaceWriter.ThreeMFWorkspaceWriter()}
    else:
        return {}
