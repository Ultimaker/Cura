# Seva Alekseyev with National Institutes of Health, 2016

from . import X3DReader

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "mesh_reader": [
            {
                "extension": "x3d",
                "description": catalog.i18nc("@item:inlistbox", "X3D File")
            }
        ]
    }


def register(app):
    return {"mesh_reader": X3DReader.X3DReader()}
