from . import LayerView

def getMetaData():
    return {
        'type': 'view',
        'plugin': {
            "name": "Layer View"
        },
        'view': {
            'name': 'Layers'
        }
    }

def register(app):
    return LayerView.LayerView()
