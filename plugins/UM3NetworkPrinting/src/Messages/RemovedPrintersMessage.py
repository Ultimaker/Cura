#  Copyright (c) 2022 UltiMaker
#  Cura is released under the terms of the LGPLv3 or higher.

from UM import i18nCatalog
from UM.Message import Message
from cura.CuraApplication import CuraApplication


class RemovedPrintersMessage(Message):
    i18n_catalog = i18nCatalog("cura")

    def __init__(self, removed_devices, device_names) -> None:
        self._removed_devices = removed_devices

        message_text = self.i18n_catalog.i18ncp(
            "info:status",
            "This printer is not linked to the Digital Factory:",
            "These printers are not linked to the Digital Factory:",
            len(self._removed_devices)
        )
        message_text += "<br/><ul>{}</ul><br/>".format(device_names)

        digital_factory_string = self.i18n_catalog.i18nc("info:name", "Ultimaker Digital Factory")
        website_link = f"<a href='https://digitalfactory.ultimaker.com?utm_source=cura&" \
                       f"utm_medium=software&utm_campaign=change-account-connect-printer'>{digital_factory_string}</a>."

        message_text += self.i18n_catalog.i18nc(
            "info:status",
            f"To establish a connection, please visit the {website_link}"
        )

        super().__init__(title=self.i18n_catalog.i18ncp("info:status",
                                                        "A cloud connection is not available for a printer",
                                                        "A cloud connection is not available for some printers",
                                                        len(self._removed_devices)),
                         message_type=Message.MessageType.WARNING,
                         text = message_text)

        self.addAction("keep_printer_configurations_action",
                                                 name=self.i18n_catalog.i18nc("@action:button",
                                                                              "Keep printer configurations"),
                                                 icon="",
                                                 description="Keep cloud printers in Ultimaker Cura when not connected to your account.",
                                                 button_align=Message.ActionButtonAlignment.ALIGN_RIGHT)
        self.addAction("remove_printers_action",
                                                 name=self.i18n_catalog.i18nc("@action:button", "Remove printers"),
                                                 icon="",
                                                 description="Remove cloud printer(s) which aren't linked to your account.",
                                                 button_style=Message.ActionButtonStyle.SECONDARY,
                                                 button_align=Message.ActionButtonAlignment.ALIGN_LEFT)



