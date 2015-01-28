from . import LayerView

def getMetaData():
    return { "name": "LayerView", "type": "View"  }

def register(app):
    app.getController().addView("LayerView", LayerView.LayerView())
