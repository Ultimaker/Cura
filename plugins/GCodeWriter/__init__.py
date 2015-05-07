from . import GCodeWriter

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "type": "mesh_writer",
        "plugin": {
            "name": "GCode Writer",
            "author": "Ultimaker",
            "version": "1.0",
            "description": catalog.i18nc("GCode Writer Plugin Description", "Writes GCode to a file")
        },

        "mesh_writer": {
            "extension": "gcode",
            "description": catalog.i18nc("GCode Writer File Description", "GCode File")
        }
    }

def register(app):
    return { "mesh_writer": GCodeWriter.GCodeWriter() }
