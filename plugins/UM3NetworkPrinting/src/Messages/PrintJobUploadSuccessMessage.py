# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM import i18nCatalog
from UM.Message import Message


I18N_CATALOG = i18nCatalog("cura")


class PrintJobUploadSuccessMessage(Message):
    
    def __init__(self) -> None:
        super().__init__(
            text = I18N_CATALOG.i18nc("@info:status", "Print job was successfully sent to the printer."),
            title = I18N_CATALOG.i18nc("@info:title", "Data Sent"),
            lifetime = 5
        )
