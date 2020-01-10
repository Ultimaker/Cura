import os
import tempfile
from functools import reduce
from typing import Dict, List, Optional, Any

from PyQt5.QtNetwork import QNetworkReply

from UM import i18n_catalog, i18nCatalog
from UM.Logger import Logger
from UM.Message import Message
from UM.Signal import Signal
from UM.TaskManagement.HttpRequestManager import HttpRequestManager
from cura.CuraApplication import CuraApplication
from plugins.Toolbox.src.UltimakerCloudScope import UltimakerCloudScope
from plugins.Toolbox.src.CloudSync.SubscribedPackagesModel import SubscribedPackagesModel


## Presents a dialog telling the user that a restart is required to apply changes
# Since we cannot restart Cura, the app is closed instead when the button is clicked
class RestartApplicationPresenter:

    def __init__(self, app: CuraApplication):
        # Emits (Dict[str, str], List[str]) # (success_items, error_items)
        # Dict{success_package_id, temp_file_path}
        # List[errored_package_id]
        self.done = Signal()

        self._app = app
        self._i18n_catalog = i18nCatalog("cura")

    def present(self):
        app_name = self._app.getApplicationDisplayName()

        message = Message(title=self._i18n_catalog.i18nc(
            "@info:generic",
            "You need to quit and restart {} before changes have effect.", app_name
        ))

        message.addAction("quit",
                          name="Quit " + app_name,
                          icon = "",
                          description="Close the application",
                          button_align=Message.ActionButtonAlignment.ALIGN_RIGHT)

        message.actionTriggered.connect(self._quitClicked)
        message.show()

    def _quitClicked(self, *_):
        self._app.windowClosed()
