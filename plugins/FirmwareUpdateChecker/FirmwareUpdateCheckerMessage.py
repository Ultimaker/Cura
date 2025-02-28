# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.i18n import i18nCatalog
from UM.Message import Message

i18n_catalog = i18nCatalog("cura")


# Make a separate class, since we need an extra field: The machine-id that this message is about.
class FirmwareUpdateCheckerMessage(Message):
    STR_ACTION_DOWNLOAD = "download"

    def __init__(self, machine_id: int, machine_name: str, latest_version: str, download_url: str) -> None:
        super().__init__(i18n_catalog.i18nc(
            "@info Don't translate {machine_name}, since it gets replaced by a printer name!",
            "New features or bug-fixes may be available for your {machine_name}! If you haven't done so already, "
            "it is recommended to update the firmware on your printer to version {latest_version}.").format(
            machine_name=machine_name, latest_version=latest_version),
            title=i18n_catalog.i18nc(
                "@info:title The %s gets replaced with the printer name.",
                "New %s stable firmware available") % machine_name)

        self._machine_id = machine_id
        self._download_url = download_url

        self.addAction(self.STR_ACTION_DOWNLOAD,
                          i18n_catalog.i18nc("@action:button", "How to update"),
                          "[no_icon]",
                          "[no_description]",
                          button_style=Message.ActionButtonStyle.LINK,
                          button_align=Message.ActionButtonAlignment.ALIGN_LEFT)

    def getMachineId(self) -> int:
        return self._machine_id

    def getDownloadUrl(self) -> str:
        return self._download_url
