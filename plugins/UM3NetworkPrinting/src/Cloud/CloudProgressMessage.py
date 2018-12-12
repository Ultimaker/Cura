# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM import i18nCatalog
from UM.Message import Message


## Class that contains all the translations for this module.
class T:
    _I18N_CATALOG = i18nCatalog("cura")

    SENDING_DATA_TEXT = _I18N_CATALOG.i18nc("@info:status", "Sending data to remote cluster")
    SENDING_DATA_TITLE = _I18N_CATALOG.i18nc("@info:status", "Sending data to remote cluster")


class CloudProgressMessage(Message):
    def __init__(self):
        super().__init__(
            text = T.SENDING_DATA_TEXT,
            title = T.SENDING_DATA_TITLE,
            progress = -1,
            lifetime = 0,
            dismissable = False,
            use_inactivity_timer = False
        )

    def show(self):
        self.setProgress(0)
        super().show()

    def update(self, percentage: int) -> None:
        if not self._visible:
            super().show()
        self.setProgress(percentage)

    @property
    def visible(self) -> bool:
        return self._visible
