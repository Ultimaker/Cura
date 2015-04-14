from . import USBPrinterManager
def getMetaData():
    return {
        'type': 'extension',
        'plugin': {
            'name': 'USB printing',
            'author': 'Jaime van Kessel',
            'version': '1.0',
            'description': 'Accepts G-Code and sends them to a printer. Plugin can also update firmware '
        }
    }

def register(app):
    return USBPrinterManager.USBPrinterManager()
