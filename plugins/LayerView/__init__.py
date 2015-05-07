from . import LayerView

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "type": "view",
        "plugin": {
            "name": "Layer View",
            "author": "Ultimaker",
            "version": "1.0",
            "description": catalog.i18nc("Layer View plugin description", "Provides the Layer view.")
        },
        "view": {
            "name": catalog.i18nc("Layers View mode", "Layers"),
            "view_panel": "LayerView.qml"
        }
    }


def register(app):
    return { "view": LayerView.LayerView() }
