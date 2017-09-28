# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import LayerView, LayerViewProxy
from PyQt5.QtQml import qmlRegisterType, qmlRegisterSingletonType

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "view": {
            "name": catalog.i18nc("@item:inlistbox", "Layer view"),
            "view_panel": "LayerView.qml",
            "weight": 2
        }
    }

def createLayerViewProxy(engine, script_engine):
    return LayerViewProxy.LayerViewProxy()

def register(app):
    layer_view = LayerView.LayerView()
    qmlRegisterSingletonType(LayerViewProxy.LayerViewProxy, "UM", 1, 0, "LayerView", layer_view.getProxy)
    return { "view": LayerView.LayerView() }
