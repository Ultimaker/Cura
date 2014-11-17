#Shoopdawoop
from plugins.CuraEngineBackend import CuraEngineBackend

def getMetaData():
    return { "name": "CuraBackend", "type": "Backend" }

def register(app):
    engine = CuraEngineBackend()
    app.setBackend(engine)
    engine.addCommand(TransferMeshCommand())