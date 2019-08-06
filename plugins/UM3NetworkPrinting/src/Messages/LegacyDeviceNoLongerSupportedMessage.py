# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM import i18nCatalog
from UM.Message import Message


I18N_CATALOG = i18nCatalog("cura")


## Message shown when uploading a print job to a cluster is blocked because another upload is already in progress.
class LegacyDeviceNoLongerSupportedMessage(Message):
    
    def __init__(self) -> None:
        super().__init__(
                text = I18N_CATALOG.i18nc("@info:status", "You are attempting to connect to a printer that is not "
                                                          "running Ultimaker Connect. Please update the printer to the "
                                                          "latest firmware."),
                title = I18N_CATALOG.i18nc("@info:title", "Update your printer"),
                lifetime = 10
        )
