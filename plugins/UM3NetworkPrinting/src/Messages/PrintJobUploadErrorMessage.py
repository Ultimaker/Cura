# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM import i18nCatalog
from UM.Message import Message

I18N_CATALOG = i18nCatalog("cura")


class PrintJobUploadErrorMessage(Message):
    
    def __init__(self, message: str) -> None:
        super().__init__(
            text = message or I18N_CATALOG.i18nc("@info:text", "Could not upload the data to the printer."),
            title = I18N_CATALOG.i18nc("@info:title", "Network error"),
            lifetime = 10
        )
