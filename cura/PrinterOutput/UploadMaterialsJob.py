# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QUrl
import os  # To delete the archive when we're done.
import tempfile  # To create an archive before we upload it.
import enum

import cura.CuraApplication  # Imported like this to prevent circular imports.
from cura.UltimakerCloud import UltimakerCloudConstants  # To know where the API is.
from cura.UltimakerCloud.UltimakerCloudScope import UltimakerCloudScope  # To know how to communicate with this server.
from UM.Job import Job
from UM.Logger import Logger
from UM.Signal import Signal
from UM.TaskManagement.HttpRequestManager import HttpRequestManager  # To call the API.
from UM.TaskManagement.HttpRequestScope import JsonDecoratorScope

from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from PyQt5.QtNetwork import QNetworkReply
    from cura.UltimakerCloud.CloudMaterialSync import CloudMaterialSync

class UploadMaterialsJob(Job):
    """
    Job that uploads a set of materials to the Digital Factory.
    """

    UPLOAD_REQUEST_URL = f"{UltimakerCloudConstants.CuraDigitalFactoryURL}/materials/profile_upload"

    class Result(enum.IntEnum):
        SUCCCESS = 0
        FAILED = 1

    def __init__(self, material_sync: "CloudMaterialSync"):
        super().__init__()
        self._material_sync = material_sync
        self._scope = JsonDecoratorScope(UltimakerCloudScope(cura.CuraApplication.CuraApplication.getInstance()))  # type: JsonDecoratorScope

    uploadCompleted = Signal()

    def run(self):
        archive_file = tempfile.NamedTemporaryFile("wb", delete = False)
        archive_file.close()

        self._material_sync.exportAll(QUrl.fromLocalFile(archive_file.name))

        http = HttpRequestManager.getInstance()
        http.get(
            url = self.UPLOAD_REQUEST_URL,
            callback = self.onUploadRequestCompleted,
            error_callback = self.onError,
            scope = self._scope
        )

    def onUploadRequestCompleted(self, reply: "QNetworkReply", error: Optional["QNetworkReply.NetworkError"]):
        if error is not None:
            Logger.error(f"Could not request URL to upload material archive to: {error}")
            self.setResult(self.Result.FAILED)
            return

        response_data = HttpRequestManager.readJSON(reply)
        if response_data is None:
            Logger.error(f"Invalid response to material upload request. Could not parse JSON data.")
            self.setResult(self.Result.FAILED)
            return
        if "upload_url" not in response_data:
            Logger.error(f"Invalid response to material upload request: Missing 'upload_url' field to upload archive to.")
            self.setResult(self.Result.Failed)
            return

        upload_url = response_data["upload_url"]
        http = HttpRequestManager.getInstance()
        http.put(
            url = upload_url,
            callback = self.onUploadCompleted,
            error_callback = self.onError,
            scope = self._scope
        )

    def onUploadCompleted(self, reply: "QNetworkReply", error: Optional["QNetworkReply.NetworkError"]):
        if error is not None:
            Logger.error(f"Failed to upload material archive: {error}")
            self.setResult(self.Result.FAILED)
        else:
            self.setResult(self.Result.SUCCESS)
        self.uploadCompleted.emit(self.getResult())

    def onError(self, reply: "QNetworkReply", error: Optional["QNetworkReply.NetworkError"]):
        Logger.error(f"Failed to upload material archive: {error}")
        self.setResult(self.Result.FAILED)
        self.uploadCompleted.emit(self.getResult())