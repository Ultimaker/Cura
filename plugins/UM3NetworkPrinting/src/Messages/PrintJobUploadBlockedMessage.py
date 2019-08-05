# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM import i18nCatalog
from UM.Message import Message

I18N_CATALOG = i18nCatalog("cura")


class PrintJobUploadBlockedMessage(Message):
    
    def __init__(self) -> None:
        super().__init__(
            text = I18N_CATALOG.i18nc("@info:status", "Please wait until the current job has been sent."),
            title = I18N_CATALOG.i18nc("@info:title", "Print error"),
            lifetime = 10
        )
