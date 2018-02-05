#Copyright (c) 2018 Ultimaker B.V.
#Cura is released under the terms of the LGPLv3 or higher.

import sys

from UM.Logger import Logger
try:
    from . import UFPWriter
except ImportError:
    Logger.log("w", "Could not import UFPWriter; libCharon may be missing")

from UM.i18n import i18nCatalog #To translate the file format description.
from UM.Mesh.MeshWriter import MeshWriter #For the binary mode flag.

i18n_catalog = i18nCatalog("cura")

def getMetaData():
    if "UFPWriter.UFPWriter" not in sys.modules:
        return {}

    return {
        "mesh_writer": {
            "output": [
                {
                    "mime_type": "application/x-ufp",
                    "mode": MeshWriter.OutputMode.BinaryMode,
                    "extension": "ufp",
                    "description": i18n_catalog.i18nc("@item:inlistbox", "Ultimaker Format Package")
                }
            ]
        }
    }

def register(app):
    if "UFPWriter.UFPWriter" not in sys.modules:
        return {}

    return { "mesh_writer": UFPWriter.UFPWriter() }
