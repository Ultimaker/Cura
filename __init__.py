from . import USBPrinterManager
def getMetaData():
    return {
        'type': 'storage_device',
        'plugin': {
            'name': 'Local File Storage',
            'author': 'Jaime van Kessel',
            'version': '1.0',
            'description': 'Accepts G-Code and sends them to a printer. '
        }
    }

def register(app):
    return USBPrinterManager.USBPrinterManager()
