import os
import tempfile
from functools import reduce
from typing import Dict, List, Optional

from PyQt5.QtNetwork import QNetworkReply

from UM import i18n_catalog
from UM.Logger import Logger
from UM.Message import Message
from UM.Signal import Signal
from UM.TaskManagement.HttpRequestManager import HttpRequestManager
from cura.CuraApplication import CuraApplication
from plugins.Toolbox.src.UltimakerCloudScope import UltimakerCloudScope
from plugins.Toolbox.src.CloudSync.SubscribedPackagesModel import SubscribedPackagesModel


## Downloads a set of packages from the Ultimaker Cloud Marketplace
# use download() exactly once: should not be used for multiple sets of downloads since this class contains state
class DownloadPresenter:

    def __init__(self, app: CuraApplication):
        # Emits (Dict[str, str], List[str]) # (success_items, error_items)
        # Dict{success_package_id, temp_file_path}
        # List[errored_package_id]
        self.done = Signal()

        self._app = app
        self._scope = UltimakerCloudScope(app)

        self._started = False
        self._progress_message = None  # type: Optional[Message]
        self._progress = {}  # type: Dict[str, Dict[str, int]] # package_id, Dict
        self._error = []  # type: List[str] # package_id

    def download(self, model: SubscribedPackagesModel):
        if self._started:
            Logger.error("Download already started. Create a new %s instead", self.__class__.__name__)
            return

        manager = HttpRequestManager.getInstance()
        for item in model.items:
            package_id = item["package_id"]
            self._progress[package_id] = {
                "received": 0,
                "total": 1  # make sure this is not considered done yet. Also divByZero-safe
            }

            manager.get(
                item["download_url"],
                callback = lambda reply: self._onFinished(package_id, reply),
                download_progress_callback = lambda rx, rt: self._onProgress(package_id, rx, rt),
                error_callback = lambda rx, rt: self._onProgress(package_id, rx, rt),
                scope = self._scope)

        self._started = True
        self._showProgressMessage()

    def _showProgressMessage(self):
        self._progress_message = Message(i18n_catalog.i18nc(
            "@info:generic",
            "\nSyncing..."),
            lifetime = 0,
            progress = 0.0,
            title = i18n_catalog.i18nc("@info:title", "Changes detected from your Ultimaker account", ))
        self._progress_message.show()

    def _onFinished(self, package_id: str, reply: QNetworkReply):
        self._progress[package_id]["received"] = self._progress[package_id]["total"]

        file_path = self._getTempFile(package_id)
        try:
            with open(file_path) as temp_file:
                # todo buffer this
                temp_file.write(reply.readAll())
        except IOError:
            self._onError(package_id)

        self._checkDone()

    def _onProgress(self, package_id: str, rx: int, rt: int):
        self._progress[package_id]["received"] = rx
        self._progress[package_id]["total"] = rt

        received = 0
        total = 0
        for item in self._progress.values():
            received += item["received"]
            total += item["total"]

        self._progress_message.setProgress(100.0 * (received / total))  # [0 .. 100] %

        self._checkDone()

    def _onError(self, package_id: str):
        self._progress.pop(package_id)
        self._error.append(package_id)
        self._checkDone()

    def _checkDone(self) -> bool:
        for item in self._progress.values():
            if item["received"] != item["total"] or item["total"] == -1:
                return False

        success_items = {package_id : self._getTempFile(package_id) for package_id in self._progress.keys()}
        error_items = [package_id for package_id in self._error]

        self._progress_message.hide()
        self.done.emit(success_items, error_items)

    def _getTempFile(self, package_id: str) -> str:
        temp_dir = tempfile.gettempdir()
        return os.path.join(temp_dir, package_id)

