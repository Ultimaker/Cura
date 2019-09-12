# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM import i18nCatalog
from UM.Message import Message


I18N_CATALOG = i18nCatalog("cura")


## Message shown when a new printer was added to your account but not yet in Cura.
class CloudPrinterDetectedMessage(Message):

    # Singleton used to prevent duplicate messages of this type at the same time.
    __is_visible = False

    def __init__(self) -> None:
        super().__init__(
            title=I18N_CATALOG.i18nc("@info:title", "New cloud printers found"),
            text=I18N_CATALOG.i18nc("@info:message", "New printers have been found connected to your account, "
                                                     "you can find them in your list of discovered printers."),
            lifetime=10,
            dismissable=True
        )

    def show(self) -> None:
        if CloudPrinterDetectedMessage.__is_visible:
            return
        super().show()
        CloudPrinterDetectedMessage.__is_visible = True

    def hide(self, send_signal = True) -> None:
        super().hide(send_signal)
        CloudPrinterDetectedMessage.__is_visible = False
