# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from UM import i18nCatalog
from UM.Message import Message
from cura.CuraApplication import CuraApplication


I18N_CATALOG = i18nCatalog("cura")


class CloudFlowMessage(Message):
    
    def __init__(self, address: str) -> None:
        super().__init__(
            text=I18N_CATALOG.i18nc("@info:status",
                                    "Send and monitor print jobs from anywhere using your Ultimaker account."),
            lifetime=0,
            dismissable=True,
            option_state=False,
            image_source=QUrl.fromLocalFile(os.path.join(
                    CuraApplication.getInstance().getPluginRegistry().getPluginPath("UM3NetworkPrinting"),
                    "resources", "svg", "cloud-flow-start.svg"
            )),
            image_caption=I18N_CATALOG.i18nc("@info:status Ultimaker Cloud should not be translated.",
                                             "Connect to Ultimaker Cloud"),
        )
        self._address = address
        self.addAction("", I18N_CATALOG.i18nc("@action", "Get started"), "", "")
        self.actionTriggered.connect(self._onCloudFlowStarted)

    def _onCloudFlowStarted(self, messageId: str, actionId: str) -> None:
        QDesktopServices.openUrl(QUrl("http://{}/cloud_connect".format(self._address)))
        self.hide()
