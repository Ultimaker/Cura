# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM import i18nCatalog
from UM.Message import Message
from cura.CuraApplication import CuraApplication


class NewPrinterDetectedMessage(Message):
    i18n_catalog = i18nCatalog("cura")

    def __init__(self, num_printers_found: int) -> None:
        super().__init__(title = self.i18n_catalog.i18ncp("info:status",
                                                          "New printer detected from your Ultimaker account",
                                                          "New printers detected from your Ultimaker account",
                                                          num_printers_found),
                         progress = 0,
                         lifetime = 0,
                         message_type = Message.MessageType.POSITIVE)
        self._printers_added = 0
        self._num_printers_found = num_printers_found

    def updateProgressText(self, output_device):
        """
        While the progress of adding printers is running, update the text displayed.
        :param output_device: The output device that is being added.
        :return:
        """
        message_text = self.i18n_catalog.i18nc("info:status Filled in with printer name and printer model.",
                                               "Adding printer {name} ({model}) from your account").format(
            name=output_device.name, model=output_device.printerTypeName)
        self.setText(message_text)
        if self._num_printers_found > 1:
            self.setProgress((self._printers_added / self._num_printers_found) * 100)
            self._printers_added += 1

        CuraApplication.getInstance().processEvents()

    def finalize(self, new_devices_added, new_output_devices):
        self.setProgress(None)
        num_devices_added = len(new_devices_added)
        max_disp_devices = 3

        if num_devices_added > max_disp_devices:
            num_hidden = num_devices_added - max_disp_devices
            device_name_list = ["<li>{} ({})</li>".format(device.name, device.printerTypeName) for device in
                                new_output_devices[0: max_disp_devices]]
            device_name_list.append(
                "<li>" + self.i18n_catalog.i18ncp("info:{0} gets replaced by a number of printers", "... and {0} other",
                                                  "... and {0} others", num_hidden) + "</li>")
            device_names = "".join(device_name_list)
        else:
            device_names = "".join(
                ["<li>{} ({})</li>".format(device.name, device.printerTypeName) for device in new_devices_added])

        if new_devices_added:
            message_text = self.i18n_catalog.i18nc("info:status",
                                                   "Printers added from Digital Factory:") + f"<ul>{device_names}</ul>"
            self.setText(message_text)
        else:
            self.hide()
