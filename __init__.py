#Shoopdawoop
from plugins.UMEngineBackend import UMEngineBackend

def getMetaData():
    return { "name": "UMBackend", "type": "Backend" }

def register(app):

    engine = UMEngineBackend()
    app.setBackend(engine)
    #engine.addCommand(TransferMeshCommand())