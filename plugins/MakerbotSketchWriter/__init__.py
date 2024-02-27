# Copyright (c) 2024 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from UM.i18n import i18nCatalog

from . import MakerbotWriter

catalog = i18nCatalog("cura")


def getMetaData():
    file_extension = "makerbot"
    return {
        "mesh_writer": {
            "output": [
                {
                    "extension": file_extension,
                    "description": catalog.i18nc("@item:inlistbox", "Makerbot Sketch Printfile"),
                    "mime_type": "application/x-makerbot-sketch",
                    "mode": MakerbotWriter.MakerbotWriter.OutputMode.BinaryMode,
                },
            ],
        }
    }


def register(app):
    return {
        "mesh_writer": MakerbotWriter.MakerbotWriter(),
    }
