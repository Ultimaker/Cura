# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM import i18nCatalog
from UM.Message import Message


I18N_CATALOG = i18nCatalog("cura")


## Message shown when trying to connect to a printer that is not a host.
class NotClusterHostMessage(Message):
    
    # Singleton used to prevent duplicate messages of this type at the same time.
    __is_visible = False
    
    def __init__(self) -> None:
        super().__init__(
            text = I18N_CATALOG.i18nc("@info:status", "You are attempting to connect to a printer that is not "
                                                      "the host of an Ultimaker Connect group. Please connect to "
                                                      "the host instead."),
            title = I18N_CATALOG.i18nc("@info:title", "Not a cluster host"),
            lifetime = 10
        )

    def show(self) -> None:
        if NotClusterHostMessage.__is_visible:
            return
        super().show()
        NotClusterHostMessage.__is_visible = True

    def hide(self, send_signal = True) -> None:
        super().hide(send_signal)
        NotClusterHostMessage.__is_visible = False
