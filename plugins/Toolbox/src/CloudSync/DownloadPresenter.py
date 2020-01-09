import os
import tempfile
from functools import reduce
from typing import Dict, List, Optional, Any

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
        self._progress = {}  # type: Dict[str, Dict[str, Any]] # package_id, Dict
        self._error = []  # type: List[str] # package_id

    def download(self, model: SubscribedPackagesModel):
        if self._started:
            Logger.error("Download already started. Create a new %s instead", self.__class__.__name__)
            return

        manager = HttpRequestManager.getInstance()
        for item in model.items:
            package_id = item["package_id"]

            request_data = manager.get(
                item["download_url"],
                callback = lambda reply, pid = package_id: self._onFinished(pid, reply),
                download_progress_callback = lambda rx, rt, pid = package_id: self._onProgress(pid, rx, rt),
                error_callback = lambda rx, rt, pid = package_id: self._onProgress(pid, rx, rt),
                scope = self._scope)

            self._progress[package_id] = {
                "received": 0,
                "total": 1,  # make sure this is not considered done yet. Also divByZero-safe
                "file_written": None,
                "request_data": request_data
            }

        self._started = True
        self._showProgressMessage()

    def abort(self):
        manager = HttpRequestManager.getInstance()
        for item in self._progress.values():
            manager.abortRequest(item["request_data"])

    # Aborts all current operations and returns a copy with the same settings such as app and scope
    def resetCopy(self):
        self.abort()
        self.done.disconnectAll()
        return DownloadPresenter(self._app)

    def _showProgressMessage(self):
        self._progress_message = Message(i18n_catalog.i18nc(
            "@info:generic",
            "\nSyncing..."),
            lifetime = 0,
            use_inactivity_timer=False,
            progress = 0.0,
            title = i18n_catalog.i18nc("@info:title", "Changes detected from your Ultimaker account", ))
        self._progress_message.show()

    def _onFinished(self, package_id: str, reply: QNetworkReply):
        self._progress[package_id]["received"] = self._progress[package_id]["total"]

        file_fd, file_path = tempfile.mkstemp()
        os.close(file_fd)  # close the file so we can open it from python

        try:
            with open(file_path, "wb+") as temp_file:
                bytes_read = reply.read(256 * 1024)
                while bytes_read:
                    temp_file.write(bytes_read)
                    bytes_read = reply.read(256 * 1024)
                    self._app.processEvents()
            self._progress[package_id]["file_written"] = file_path
        except IOError as e:
            Logger.logException("e", "Failed to write downloaded package to temp file", e)
            self._onError(package_id)
        temp_file.close()

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

    def _onError(self, package_id: str):
        self._progress.pop(package_id)
        self._error.append(package_id)
        self._checkDone()

    def _checkDone(self) -> bool:
        for item in self._progress.values():
            if not item["file_written"]:
                return False

        success_items = {package_id : value["file_written"] for package_id, value in self._progress.items()}
        error_items = [package_id for package_id in self._error]

        self._progress_message.hide()
        self.done.emit(success_items, error_items)
