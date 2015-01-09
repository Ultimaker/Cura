#Shoopdawoop
from . import CuraEngineBackend

from UM.Preferences import Preferences

def getMetaData():
    return { "name": "CuraBackend", "type": "Backend" }

def register(app):
    Preferences.addPreference("BackendLocation","../PinkUnicornEngine/CuraEngine")
    engine = CuraEngineBackend.CuraEngineBackend()
    app.setBackend(engine)
    #engine.addCommand(TransferMeshCommand())
