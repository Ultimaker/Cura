# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM import i18nCatalog
from UM.Message import Message


I18N_CATALOG = i18nCatalog("cura")


class PrintJobUploadProgressMessage(Message):
    """Class responsible for showing a progress message while a mesh is being uploaded to the cloud."""

    def __init__(self):
        super().__init__(
            title = I18N_CATALOG.i18nc("@info:status", "Sending Print Job"),
            text = I18N_CATALOG.i18nc("@info:status", "Uploading print job to printer."),
            progress = -1,
            lifetime = 0,
            dismissable = False,
            use_inactivity_timer = False
        )

    def show(self):
        """Shows the progress message."""

        self.setProgress(0)
        super().show()

    def update(self, percentage: int) -> None:
        """Updates the percentage of the uploaded.
        
        :param percentage: The percentage amount (0-100).
        """
        if not self._visible:
            super().show()
        self.setProgress(percentage)
