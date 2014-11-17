#Shoopdawoop
from plugins.CuraEngineBackend import CuraEngineBackend

def getMetaData():
    return { "name": "CuraBackend", "type": "Backend" }

def register(app):
    app.setBackend(CuraEngineBackend())