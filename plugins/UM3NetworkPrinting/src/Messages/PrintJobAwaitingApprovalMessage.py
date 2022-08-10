# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM import i18nCatalog
from UM.Message import Message


I18N_CATALOG = i18nCatalog("cura")


class PrintJobPendingApprovalMessage(Message):
    """Message shown when waiting for approval on an uploaded print job."""

    def __init__(self) -> None:
        super().__init__(
            text = I18N_CATALOG.i18nc("@info:status", "The print job was succesfully submitted"),
            title=I18N_CATALOG.i18nc("@info:title", "You will recieve a confirmation via email when the print job is approved"),
            message_type=Message.MessageType.POSITIVE
        )
        self.self.addAction("learn_more",
                            I18N_CATALOG.i18nc("@action", "Learn more"),
                            "",
                            "",
                            "",
                            button_style = Message.ActionButtonStyle.LINK,
                            button_align = Message.ActionButtonAlignment.ALIGN_LEFT)
