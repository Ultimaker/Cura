# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import TYPE_CHECKING

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from UM import i18nCatalog
from UM.Message import Message


if TYPE_CHECKING:
    from ..UltimakerNetworkedPrinterOutputDevice import UltimakerNetworkedPrinterOutputDevice


I18N_CATALOG = i18nCatalog("cura")


class NotClusterHostMessage(Message):
    """Message shown when trying to connect to a printer that is not a host."""

    __is_visible = False
    """Singleton used to prevent duplicate messages of this type at the same time."""

    def __init__(self, device: "UltimakerNetworkedPrinterOutputDevice") -> None:
        super().__init__(
            text = I18N_CATALOG.i18nc("@info:status", "You are attempting to connect to {0} but it is not "
                                                      "the host of a group. You can visit the web page to configure "
                                                      "it as a group host.", device.name),
            title = I18N_CATALOG.i18nc("@info:title", "Not a group host"),
            lifetime = 0,
            dismissable = True
        )
        self._address = device.address
        self.addAction("", I18N_CATALOG.i18nc("@action", "Configure group"), "", "")
        self.actionTriggered.connect(self._onConfigureClicked)

    def show(self) -> None:
        if NotClusterHostMessage.__is_visible:
            return
        super().show()
        NotClusterHostMessage.__is_visible = True

    def hide(self, send_signal = True) -> None:
        super().hide(send_signal)
        NotClusterHostMessage.__is_visible = False

    def _onConfigureClicked(self, messageId: str, actionId: str) -> None:
        QDesktopServices.openUrl(QUrl("http://{}/print_jobs".format(self._address)))
        self.hide()
