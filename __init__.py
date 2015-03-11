#Shoopdawoop
from . import CuraEngineBackend

def getMetaData():
    return {
        'type': 'backend',
        'plugin': {
            'name': "CuraEngine Backend"
        }
    }

def register(app):
    return CuraEngineBackend.CuraEngineBackend()

