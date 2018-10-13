
from UM.i18n import i18nCatalog
from UM.Message import Message

i18n_catalog = i18nCatalog("cura")


# Make a separate class, since we need an extra field: The machine-id that this message is about.
class FirmwareUpdateCheckerMessage(Message):
    STR_ACTION_DOWNLOAD = "download"

    def __init__(self, machine_id: int, machine_name: str) -> None:
        super().__init__(i18n_catalog.i18nc(
            "@info Don't translate {machine_name}, since it gets replaced by a printer name!",
            "New features are available for your {machine_name}! It is recommended to update the firmware on your printer.").format(
            machine_name=machine_name),
            title=i18n_catalog.i18nc(
                "@info:title The %s gets replaced with the printer name.",
                "New %s firmware available") % machine_name)

        self._machine_id = machine_id

        self.addAction(self.STR_ACTION_DOWNLOAD,
                          i18n_catalog.i18nc("@action:button", "How to update"),
                          "[no_icon]",
                          "[no_description]",
                          button_style=Message.ActionButtonStyle.LINK,
                          button_align=Message.ActionButtonStyle.BUTTON_ALIGN_LEFT)

    def getMachineId(self) -> int:
        return self._machine_id
