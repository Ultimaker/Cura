# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from UM import i18nCatalog
from UM.Message import Message
from cura.CuraApplication import CuraApplication


I18N_CATALOG = i18nCatalog("cura")


class CloudFlowMessage(Message):

    def __init__(self, printer_name: str) -> None:
        image_path = os.path.join(
            CuraApplication.getInstance().getPluginRegistry().getPluginPath("UM3NetworkPrinting") or "",
            "resources", "svg", "CloudPlatform.svg"
        )
        super().__init__(
            text = I18N_CATALOG.i18nc("@info:status",
                                    f"Your printer <b>{printer_name}</b> could be connected via cloud.\n Manage your print queue and monitor your prints from anywhere connecting your printer to Digital Factory"),
            title = I18N_CATALOG.i18nc("@info:title", "Are you ready for cloud printing?"),
            image_source = QUrl.fromLocalFile(image_path)
        )
        self._printer_name = printer_name
        self.addAction("get_started", I18N_CATALOG.i18nc("@action", "Get started"), "", "")
        self.addAction("learn_more", I18N_CATALOG.i18nc("@action", "Learn more"), "", "", button_style = Message.ActionButtonStyle.LINK, button_align = Message.ActionButtonAlignment.ALIGN_LEFT)

        self.actionTriggered.connect(self._onCloudFlowStarted)

    def _onCloudFlowStarted(self, message_id: str, action_id: str) -> None:
        if action_id == "get_started":
            QDesktopServices.openUrl(QUrl("https://digitalfactory.ultimaker.com/app/printers?add_printer=true&utm_source=cura&utm_medium=software&utm_campaign=message-networkprinter-added"))
            self.hide()
        else:
            QDesktopServices.openUrl(QUrl("https://support.ultimaker.com/hc/en-us/articles/360012019239?utm_source=cura&utm_medium=software&utm_campaign=add-cloud-printer"))
