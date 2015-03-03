from . import LayerView

def getMetaData():
    return { "name": "LayerView", "type": "View"  }

def register(app):
    return LayerView.LayerView()
