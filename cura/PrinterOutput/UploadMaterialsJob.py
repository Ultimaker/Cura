# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QUrl
import os  # To delete the archive when we're done.
import tempfile  # To create an archive before we upload it.
import enum
import functools

import cura.CuraApplication  # Imported like this to prevent circular imports.
from cura.Settings.CuraContainerRegistry import CuraContainerRegistry  # To find all printers to upload to.
from cura.UltimakerCloud import UltimakerCloudConstants  # To know where the API is.
from cura.UltimakerCloud.UltimakerCloudScope import UltimakerCloudScope  # To know how to communicate with this server.
from UM.i18n import i18nCatalog
from UM.Job import Job
from UM.Logger import Logger
from UM.Signal import Signal
from UM.TaskManagement.HttpRequestManager import HttpRequestManager  # To call the API.
from UM.TaskManagement.HttpRequestScope import JsonDecoratorScope

from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from PyQt5.QtNetwork import QNetworkReply
    from cura.UltimakerCloud.CloudMaterialSync import CloudMaterialSync

catalog = i18nCatalog("cura")


class UploadMaterialsJob(Job):
    """
    Job that uploads a set of materials to the Digital Factory.
    """

    UPLOAD_REQUEST_URL = f"{UltimakerCloudConstants.CuraCloudAPIRoot}/connect/v1/materials/upload"
    UPLOAD_CONFIRM_URL = UltimakerCloudConstants.CuraCloudAPIRoot + "/connect/v1/clusters/{cluster_id}/printers/{cluster_printer_id}/action/confirm_material_upload"

    class Result(enum.IntEnum):
        SUCCCESS = 0
        FAILED = 1

    def __init__(self, material_sync: "CloudMaterialSync"):
        super().__init__()
        self._material_sync = material_sync
        self._scope = JsonDecoratorScope(UltimakerCloudScope(cura.CuraApplication.CuraApplication.getInstance()))  # type: JsonDecoratorScope
        self._archive_filename = None  # type: Optional[str]
        self._archive_remote_id = None  # type: Optional[str]  # ID that the server gives to this archive. Used to communicate about the archive to the server.
        self._num_synced_printers = 0
        self._completed_printers = set()  # The printers that have successfully completed the upload.
        self._failed_printers = set()

    uploadCompleted = Signal()
    uploadProgressChanged = Signal()

    def run(self):
        archive_file = tempfile.NamedTemporaryFile("wb", delete = False)
        archive_file.close()
        self._archive_filename = archive_file.name

        self._material_sync.exportAll(QUrl.fromLocalFile(self._archive_filename), notify_progress = self.uploadProgressChanged)
        file_size = os.path.getsize(self._archive_filename)

        http = HttpRequestManager.getInstance()
        http.get(
            url = self.UPLOAD_REQUEST_URL + f"?file_size={file_size}&file_name=cura.umm",  # File name can be anything as long as it's .umm. It's not used by Cloud or firmware.
            callback = self.onUploadRequestCompleted,
            error_callback = self.onError,
            scope = self._scope
        )

    def onUploadRequestCompleted(self, reply: "QNetworkReply", error: Optional["QNetworkReply.NetworkError"]):
        if error is not None:
            Logger.error(f"Could not request URL to upload material archive to: {error}")
            self.setError(UploadMaterialsError(catalog.i18nc("@text:error", "Failed to connect to Digital Factory.")))
            self.setResult(self.Result.FAILED)
            self.uploadCompleted.emit(self.getResult(), self.getError())
            return

        response_data = HttpRequestManager.readJSON(reply)
        if response_data is None:
            Logger.error(f"Invalid response to material upload request. Could not parse JSON data.")
            self.setError(UploadMaterialsError(catalog.i18nc("@text:error", "The response from Digital Factory appears to be corrupted.")))
            self.setResult(self.Result.FAILED)
            self.uploadCompleted.emit(self.getResult(), self.getError())
            return
        if "upload_url" not in response_data:
            Logger.error(f"Invalid response to material upload request: Missing 'upload_url' field to upload archive to.")
            self.setError(UploadMaterialsError(catalog.i18nc("@text:error", "The response from Digital Factory is missing important information.")))
            self.setResult(self.Result.FAILED)
            self.uploadCompleted.emit(self.getResult(), self.getError())
            return
        if "material_profile_id" not in response_data:
            Logger.error(f"Invalid response to material upload request: Missing 'material_profile_id' to communicate about the materials with the server.")
            self.setError(UploadMaterialsError(catalog.i18nc("@text:error", "The response from Digital Factory is missing important information.")))
            self.setResult(self.Result.FAILED)
            self.uploadCompleted.emit(self.getResult(), self.getError())
            return

        upload_url = response_data["upload_url"]
        self._archive_remote_id = response_data["material_profile_id"]
        file_data = open(self._archive_filename, "rb").read()
        http = HttpRequestManager.getInstance()
        http.put(
            url = upload_url,
            data = file_data,
            callback = self.onUploadCompleted,
            error_callback = self.onError,
            scope = self._scope
        )

    def onUploadCompleted(self, reply: "QNetworkReply", error: Optional["QNetworkReply.NetworkError"]):
        if error is not None:
            Logger.error(f"Failed to upload material archive: {error}")
            self.setError(UploadMaterialsError(catalog.i18nc("@text:error", "Failed to connect to Digital Factory.")))
            self.setResult(self.Result.FAILED)
            self.uploadCompleted.emit(self.getResult(), self.getError())
            return

        online_cloud_printers = CuraContainerRegistry.getInstance().findContainerStacksMetadata(
            type = "machine",
            connection_type = 3,  # Only cloud printers.
            is_online = True,  # Only online printers. Otherwise the server gives an error.
            host_guid = "*",  # Required metadata field. Otherwise we get a KeyError.
            um_cloud_cluster_id = "*"  # Required metadata field. Otherwise we get a KeyError.
        )
        self._num_synced_printers = len(online_cloud_printers)
        for container_stack in online_cloud_printers:
            cluster_id = container_stack["um_cloud_cluster_id"]
            printer_id = container_stack["host_guid"]

            http = HttpRequestManager.getInstance()
            http.get(
                url = self.UPLOAD_CONFIRM_URL.format(cluster_id = cluster_id, cluster_printer_id = printer_id),
                callback = functools.partialmethod(self.onUploadConfirmed, printer_id),
                error_callback = functools.partialmethod(self.onUploadConfirmed, printer_id),  # Let this same function handle the error too.
                scope = self._scope
            )

    def onUploadConfirmed(self, printer_id: str, reply: "QNetworkReply", error: Optional["QNetworkReply.NetworkError"]) -> None:
        if error is not None:
            Logger.error(f"Failed to confirm uploading material archive to printer {printer_id}: {error}")
            self._failed_printers.add(printer_id)
        else:
            self._completed_printers.add(printer_id)

        if len(self._completed_printers) + len(self._failed_printers) >= self._num_synced_printers:  # This is the last response to be processed.
            if self._failed_printers:
                self.setResult(self.Result.FAILED)
                self.setError(UploadMaterialsError(catalog.i18nc("@text:error", "Failed to connect to Digital Factory to sync materials with some of the printers.")))
            else:
                self.setResult(self.Result.SUCCESS)
            self.uploadCompleted.emit(self.getResult(), self.getError())

    def onError(self, reply: "QNetworkReply", error: Optional["QNetworkReply.NetworkError"]):
        Logger.error(f"Failed to upload material archive: {error}")
        self.setResult(self.Result.FAILED)
        self.setError(UploadMaterialsError(catalog.i18nc("@text:error", "Failed to connect to Digital Factory.")))
        self.uploadCompleted.emit(self.getResult(), self.getError())


class UploadMaterialsError(Exception):
    """
    Marker class to indicate something went wrong while uploading.
    """
    pass
