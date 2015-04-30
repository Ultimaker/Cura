from . import LayerView


def getMetaData():
    return {
        'type': 'view',
        'plugin': {
            "name": "Layer View"
        },
        'view': {
            'name': 'Layers',
            'view_panel': 'LayerView.qml'
        }
    }


def register(app):
    return {"view":LayerView.LayerView()}
