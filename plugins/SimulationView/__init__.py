# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtQml import qmlRegisterSingletonType

from UM.i18n import i18nCatalog
from . import SimulationViewProxy, SimulationView

catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "view": {
            "name": catalog.i18nc("@item:inlistbox", "Layer view"),
            "view_panel": "SimulationView.qml",
            "weight": 2
        }
    }

def createSimulationViewProxy(engine, script_engine):
    return SimulationViewProxy.SimulatorViewProxy()

def register(app):
    simulation_view = SimulationView.SimulationView()
    qmlRegisterSingletonType(SimulationViewProxy.SimulationViewProxy, "UM", 1, 0, "SimulationView", simulation_view.getProxy)
    return { "view": SimulationView.SimulationView()}
