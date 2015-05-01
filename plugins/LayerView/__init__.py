from . import LayerView

from UM.i18n import i18nCatalog
catalog = i18nCatalog('cura')

def getMetaData():
    return {
        'type': 'view',
        'plugin': {
            "name": "Layer View"
        },
        'view': {
            'name': catalog.i18nc('Layers View mode', 'Layers'),
            'view_panel': 'LayerView.qml'
        }
    }


def register(app):
    return { "view": LayerView.LayerView() }
