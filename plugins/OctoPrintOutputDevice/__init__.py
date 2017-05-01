from . import OctoPrintPlugin

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "type": "extension",
        "plugin": {
            "name": catalog.i18nc("@label", "OctoPrint"),
            "author": "Mark Walker",
            "description": catalog.i18nc("@info:whatsthis", "Provides direct upload of gcode to an OctoPrint server."),
            "version": "1.0",
            "api": 3
        }
    }

def register(app):
    plugin = OctoPrintPlugin.OctoPrintExtension()
    return {
        "extension": plugin,
        "output_device": plugin
    }
