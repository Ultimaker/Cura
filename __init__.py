#Shoopdawoop
from . import CuraEngineBackend

from UM.Preferences import Preferences

def getMetaData():
    return { "name": "CuraEngine Backend", "type": "Backend" }

def register(app):
    Preferences.addPreference("BackendLocation","../PinkUnicornEngine/CuraEngine")
    return CuraEngineBackend.CuraEngineBackend()

