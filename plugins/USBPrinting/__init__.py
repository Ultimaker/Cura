from . import USBPrinterManager

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "type": "extension",
        "plugin": {
            "name": "USB printing",
            "author": "Ultimaker",
            "version": "1.0",
            "description": i18n_catalog.i18nc("USB Printing plugin description","Accepts G-Code and sends them to a printer. Plugin can also update firmware")
        }
    }
        
def register(app):
    return {"extension":USBPrinterManager.USBPrinterManager()}
