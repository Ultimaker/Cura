# Copyright (c) 2021 Dynamical 3D

from . import Dynamical3DPause

##  Defines additional metadata for the plug-in.
#
#   Tool plug-ins can have a button in the interface. This has some metadata
#   that describes the tool and provides an image.
def getMetaData():
    return {
        "tool": {
            "name": "Dynamical3D pause",
            "description": "Gestión de pausas", #Typically displayed when hovering over the tool icon.
            "icon": "dynamical_bitonal.svg" #Displayed on the button.
        }
    }

##  Lets Uranium know that this plug-in exists.
#
#   This is called when starting the application to find out which plug-ins
#   exist and what their types are. We need to return a dictionary mapping from
#   strings representing plug-in types (in this case "tool") to objects that
#   inherit from PluginObject.
#
#   \param app The application that the plug-in needs to register with.
def register(app):
    return {"tool": Dynamical3DPause.Dynamical3DPause()}