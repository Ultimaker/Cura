# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM import i18nCatalog
from UM.Message import Message


I18N_CATALOG = i18nCatalog("cura")


class PrintJobUploadQueueFullMessage(Message):
    """Message shown when uploading a print job to a cluster and the print queue is full."""

    def __init__(self) -> None:
        super().__init__(
            text = I18N_CATALOG.i18nc("@info:status", "Print job queue is full. The printer can't accept a new job."),
            title = I18N_CATALOG.i18nc("@info:title", "Queue Full"),
            lifetime = 10,
            message_type=Message.MessageType.ERROR
        )
