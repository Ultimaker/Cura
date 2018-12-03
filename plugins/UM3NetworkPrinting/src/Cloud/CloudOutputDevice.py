# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import io
import json
import os
from json import JSONDecodeError
from typing import List, Optional, Dict, cast, Union, Tuple

from PyQt5.QtCore import QObject, pyqtSignal, QUrl, pyqtProperty
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest

from UM import i18nCatalog
from UM.FileHandler.FileWriter import FileWriter
from UM.FileHandler.FileHandler import FileHandler
from UM.Logger import Logger
from UM.Message import Message
from UM.OutputDevice import OutputDeviceError
from UM.Scene.SceneNode import SceneNode
from UM.Version import Version
from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.PrinterOutputController import PrinterOutputController
from cura.PrinterOutput.MaterialOutputModel import MaterialOutputModel
from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice, AuthState
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
from plugins.UM3NetworkPrinting.src.UM3PrintJobOutputModel import UM3PrintJobOutputModel
from .Models import (
    CloudClusterPrinter, CloudClusterPrintJob, JobUploadRequest, JobUploadResponse, PrintResponse, CloudClusterStatus,
    CloudClusterPrinterConfigurationMaterial
)


##  The cloud output device is a network output device that works remotely but has limited functionality.
#   Currently it only supports viewing the printer and print job status and adding a new job to the queue.
#   As such, those methods have been implemented here.
#   Note that this device represents a single remote cluster, not a list of multiple clusters.
#
#   TODO: figure our how the QML interface for the cluster networking should operate with this limited functionality.
class CloudOutputDevice(NetworkedPrinterOutputDevice):
    
    # The translation catalog for this device.
    I18N_CATALOG = i18nCatalog("cura")

    # The cloud URL to use for this remote cluster.
    # TODO: Make sure that this URL goes to the live api before release
    ROOT_PATH = "https://api-staging.ultimaker.com"
    CLUSTER_API_ROOT = "{}/connect/v1/".format(ROOT_PATH)
    CURA_API_ROOT = "{}/cura/v1/".format(ROOT_PATH)

    # Signal triggered when the printers in the remote cluster were changed.
    printersChanged = pyqtSignal()

    # Signal triggered when the print jobs in the queue were changed.
    printJobsChanged = pyqtSignal()

    def __init__(self, device_id: str, parent: QObject = None):
        super().__init__(device_id = device_id, address = "", properties = {}, parent = parent)
        self._setInterfaceElements()
        
        self._device_id = device_id
        self._account = CuraApplication.getInstance().getCuraAPI().account

        # Cluster does not have authentication, so default to authenticated
        self._authentication_state = AuthState.Authenticated

        # We re-use the Cura Connect monitor tab to get the most functionality right away.
        self._monitor_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "../../resources/qml/ClusterMonitorItem.qml")
        self._control_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "../../resources/qml/ClusterControlItem.qml")
        
        # Properties to populate later on with received cloud data.
        self._print_jobs = []  # type: List[UM3PrintJobOutputModel]
        self._number_of_extruders = 2  # All networked printers are dual-extrusion Ultimaker machines.

    @staticmethod
    def _parseReply(reply: QNetworkReply) -> Tuple[int, Union[None, str, bytes]]:
        """
        Parses a reply from the stardust server.
        :param reply: The reply received from the server.
        :return: The status code and the response dict.
        """
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        response = None
        try:
            response = bytes(reply.readAll()).decode("utf-8")
            response = json.loads(response)
        except JSONDecodeError:
            Logger.logException("w", "Unable to decode JSON from reply.")
        return status_code, response

    ##  We need to override _createEmptyRequest to work for the cloud.
    def _createEmptyRequest(self, path: str, content_type: Optional[str] = "application/json") -> QNetworkRequest:
        # noinspection PyArgumentList
        url = QUrl(path)
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.ContentTypeHeader, content_type)
        request.setHeader(QNetworkRequest.UserAgentHeader, self._user_agent)
        
        if not self._account.isLoggedIn:
            # TODO: show message to user to sign in
            self.setAuthenticationState(AuthState.NotAuthenticated)
        else:
            # TODO: not execute call at all when not signed in?
            self.setAuthenticationState(AuthState.Authenticated)
            request.setRawHeader(b"Authorization", "Bearer {}".format(self._account.accessToken).encode())

        return request
    
    ##  Set all the interface elements and texts for this output device.
    def _setInterfaceElements(self):
        self.setPriority(2)  # make sure we end up below the local networking and above 'save to file'
        self.setName(self._id)
        self.setShortDescription(self.I18N_CATALOG.i18nc("@action:button", "Print via Cloud"))
        self.setDescription(self.I18N_CATALOG.i18nc("@properties:tooltip", "Print via Cloud"))
        self.setConnectionText(self.I18N_CATALOG.i18nc("@info:status", "Connected via Cloud"))
    
    ##  Called when Cura requests an output device to receive a (G-code) file.
    def requestWrite(self, nodes: List[SceneNode], file_name: Optional[str] = None, limit_mime_types: bool = False,
                     file_handler: Optional[FileHandler] = None, **kwargs: str) -> None:
        self.writeStarted.emit(self)

        file_format = self._determineFileFormat(file_handler)
        writer = self._determineWriter(file_handler, file_format)

        # This function pauses with the yield, waiting on instructions on which printer it needs to print with.
        if not writer:
            Logger.log("e", "Missing file or mesh writer!")
            return

        stream = io.StringIO() if file_format["mode"] == FileWriter.OutputMode.TextMode else io.BytesIO()
        writer.write(stream, nodes)
        self._sendPrintJob(file_name + "." + file_format["extension"], file_format["mime_type"], stream)

    # TODO: This is yanked right out of ClusterUM3OutputDevice, great candidate for a utility or base class
    def _determineFileFormat(self, file_handler) -> Optional[Dict[str, Union[str, int]]]:
        # Formats supported by this application (file types that we can actually write).
        if file_handler:
            file_formats = file_handler.getSupportedFileTypesWrite()
        else:
            file_formats = CuraApplication.getInstance().getMeshFileHandler().getSupportedFileTypesWrite()

        global_stack = CuraApplication.getInstance().getGlobalContainerStack()
        # Create a list from the supported file formats string.
        if not global_stack:
            Logger.log("e", "Missing global stack!")
            return

        machine_file_formats = global_stack.getMetaDataEntry("file_formats").split(";")
        machine_file_formats = [file_type.strip() for file_type in machine_file_formats]
        # Exception for UM3 firmware version >=4.4: UFP is now supported and should be the preferred file format.
        if "application/x-ufp" not in machine_file_formats and Version(self.firmwareVersion) >= Version("4.4"):
            machine_file_formats = ["application/x-ufp"] + machine_file_formats

        # Take the intersection between file_formats and machine_file_formats.
        format_by_mimetype = {f["mime_type"]: f for f in file_formats}

        # Keep them ordered according to the preference in machine_file_formats.
        file_formats = [format_by_mimetype[mimetype] for mimetype in machine_file_formats]

        if len(file_formats) == 0:
            Logger.log("e", "There are no file formats available to write with!")
            raise OutputDeviceError.WriteRequestFailedError(
                self.I18N_CATALOG.i18nc("@info:status", "There are no file formats available to write with!")
            )
        return file_formats[0]

    # TODO: This is yanked right out of ClusterUM3OutputDevice, great candidate for a utility or base class
    @staticmethod
    def _determineWriter(file_handler, file_format) -> Optional[FileWriter]:
        # Just take the first file format available.
        if file_handler is not None:
            writer = file_handler.getWriterByMimeType(cast(str, file_format["mime_type"]))
        else:
            writer = CuraApplication.getInstance().getMeshFileHandler().getWriterByMimeType(
                cast(str, file_format["mime_type"])
            )

        if not writer:
            Logger.log("e", "Unexpected error when trying to get the FileWriter")
            return

        return writer

    ##  Get remote printers.
    @pyqtProperty("QVariantList", notify = printersChanged)
    def printers(self):
        return self._printers

    @pyqtProperty("QVariantList", notify = printJobsChanged)
    def printJobs(self)-> List[UM3PrintJobOutputModel]:
        return self._print_jobs

    ##  Get remote print jobs.
    @pyqtProperty("QVariantList", notify = printJobsChanged)
    def queuedPrintJobs(self) -> List[UM3PrintJobOutputModel]:
        return [print_job for print_job in self._print_jobs
                if print_job.state == "queued" or print_job.state == "error"]

    ##  Called when the connection to the cluster changes.
    def connect(self) -> None:
        super().connect()

    ##  Called when the network data should be updated.
    def _update(self) -> None:
        super()._update()
        Logger.log("i", "Calling the cloud cluster")
        self.get("{root}/cluster/{cluster_id}/status".format(root=self.CLUSTER_API_ROOT, cluster_id=self._device_id),
                 on_finished = self._onStatusCallFinished)

    ##  Method called when HTTP request to status endpoint is finished.
    #   Contains both printers and print jobs statuses in a single response.
    def _onStatusCallFinished(self, reply: QNetworkReply) -> None:
        status_code, response = self._parseReply(reply)
        if status_code > 204 or not isinstance(response, dict) or "data" not in response:
            Logger.log("w", "Got unexpected response while trying to get cloud cluster data: %s, %s",
                       status_code, response)
            return

        Logger.log("d", "Got response form the cloud cluster %s, %s", status_code, response)
        status = CloudClusterStatus(**response["data"])

        # Update all data from the cluster.
        self._updatePrinters(status.printers)
        self._updatePrintJobs(status.print_jobs)

    def _updatePrinters(self, printers: List[CloudClusterPrinter]) -> None:
        remote_printers = {p.uuid: p for p in printers}  # type: Dict[str, CloudClusterPrinter]
        current_printers = {p.key: p for p in self._printers}  # type: Dict[str, PrinterOutputModel]

        removed_printer_ids = set(current_printers).difference(remote_printers)
        new_printer_ids = set(remote_printers).difference(current_printers)
        updated_printer_ids = set(current_printers).intersection(remote_printers)

        for printer_guid in removed_printer_ids:
            self._printers.remove(current_printers[printer_guid])

        for printer_guid in new_printer_ids:
            self._addPrinter(remote_printers[printer_guid])

        for printer_guid in updated_printer_ids:
            self._updatePrinter(current_printers[printer_guid], remote_printers[printer_guid])

        self.printersChanged.emit()

    def _addPrinter(self, printer: CloudClusterPrinter) -> None:
        model = PrinterOutputModel(
            PrinterOutputController(self), len(printer.configuration), firmware_version=printer.firmware_version
        )
        self._printers.append(model)
        self._updatePrinter(model, printer)

    def _updatePrinter(self, model: PrinterOutputModel, printer: CloudClusterPrinter) -> None:
        model.updateKey(printer.uuid)
        model.updateName(printer.friendly_name)
        model.updateType(printer.machine_variant)
        model.updateState(printer.status if printer.enabled else "disabled")

        for index in range(0, len(printer.configuration)):
            try:
                extruder = model.extruders[index]
                extruder_data = printer.configuration[index]
            except IndexError:
                break

            extruder.updateHotendID(extruder_data.print_core_id)

            if extruder.activeMaterial is None or extruder.activeMaterial.guid != extruder_data.material.guid:
                material = self._createMaterialOutputModel(extruder_data.material)
                extruder.updateActiveMaterial(material)

    @staticmethod
    def _createMaterialOutputModel(material: CloudClusterPrinterConfigurationMaterial) -> MaterialOutputModel:
        material_manager = CuraApplication.getInstance().getMaterialManager()
        material_group_list = material_manager.getMaterialGroupListByGUID(material.guid) or []

        # Sort the material groups by "is_read_only = True" first, and then the name alphabetically.
        read_only_material_group_list = list(filter(lambda x: x.is_read_only, material_group_list))
        non_read_only_material_group_list = list(filter(lambda x: not x.is_read_only, material_group_list))
        material_group = None
        if read_only_material_group_list:
            read_only_material_group_list = sorted(read_only_material_group_list, key=lambda x: x.name)
            material_group = read_only_material_group_list[0]
        elif non_read_only_material_group_list:
            non_read_only_material_group_list = sorted(non_read_only_material_group_list, key=lambda x: x.name)
            material_group = non_read_only_material_group_list[0]

        if material_group:
            container = material_group.root_material_node.getContainer()
            color = container.getMetaDataEntry("color_code")
            brand = container.getMetaDataEntry("brand")
            material_type = container.getMetaDataEntry("material")
            name = container.getName()
        else:
            Logger.log("w",
                       "Unable to find material with guid {guid}. Using data as provided by cluster".format(
                           guid=material.guid))
            color = material.color
            brand = material.brand
            material_type = material.material
            name = "Empty" if material.material == "empty" else "Unknown"

        return MaterialOutputModel(guid=material.guid, type=material_type, brand=brand, color=color, name=name)

    def _updatePrintJobs(self, jobs: List[CloudClusterPrintJob]) -> None:
        remote_jobs = {j.uuid: j for j in jobs}  # type: Dict[str, CloudClusterPrintJob]
        current_jobs = {j.key: j for j in self._print_jobs}  # type: Dict[str, UM3PrintJobOutputModel]

        removed_job_ids = set(current_jobs).difference(set(remote_jobs))
        new_job_ids = set(remote_jobs.keys()).difference(set(current_jobs))
        updated_job_ids = set(current_jobs).intersection(set(remote_jobs))

        for job_id in removed_job_ids:
            self._print_jobs.remove(current_jobs[job_id])

        for job_id in new_job_ids:
            self._addPrintJob(remote_jobs[job_id])

        for job_id in updated_job_ids:
            self._updateUM3PrintJobOutputModel(current_jobs[job_id], remote_jobs[job_id])

        # TODO: properly handle removed and updated printers
        self.printJobsChanged.emit()

    def _addPrintJob(self, job: CloudClusterPrintJob) -> None:
        try:
            printer = next(p for p in self._printers if job.printer_uuid == p.key)
        except StopIteration:
            return Logger.log("w", "Missing printer %s for job %s in %s", job.printer_uuid, job.uuid,
                              [p.key for p in self._printers])

        model = UM3PrintJobOutputModel(printer.getController(), job.uuid, job.name)
        model.updateAssignedPrinter(printer)
        self._print_jobs.append(model)

    @staticmethod
    def _updateUM3PrintJobOutputModel(model: UM3PrintJobOutputModel, job: CloudClusterPrintJob) -> None:
        model.updateTimeTotal(job.time_total)
        model.updateTimeElapsed(job.time_elapsed)
        model.updateOwner(job.owner)
        model.updateState(job.status)

    def _sendPrintJob(self, file_name: str, content_type: str, stream: Union[io.StringIO, io.BytesIO]) -> None:
        mesh = stream.getvalue()

        request = JobUploadRequest()
        request.job_name = file_name
        request.file_size = len(mesh)
        request.content_type = content_type

        Logger.log("i", "Creating new cloud print job: %s", request.__dict__)
        self.put("{}/jobs/upload".format(self.CURA_API_ROOT), data = json.dumps({"data": request.__dict__}),
                 on_finished = lambda reply: self._onPrintJobCreated(mesh, reply))

    def _onPrintJobCreated(self, mesh: bytes, reply: QNetworkReply) -> None:
        status_code, response = self._parseReply(reply)
        if status_code > 204 or not isinstance(response, dict) or "data" not in response:
            Logger.log("w", "Got unexpected response while trying to add print job to cluster: {}, {}"
                       .format(status_code, response))
            self.writeError.emit()
            return

        # TODO: add progress messages so we have visual feedback when uploading to cloud
        # TODO: Multipart upload
        job_response = JobUploadResponse(**response.get("data"))
        Logger.log("i", "Print job created successfully: %s", job_response.__dict__)
        self.put(job_response.upload_url, data=mesh,
                 on_finished=lambda r: self._onPrintJobUploaded(job_response.job_id, r))

    def _onPrintJobUploaded(self, job_id: str, reply: QNetworkReply) -> None:
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code > 204:
            Logger.logException("w", "Received unexpected response from the job upload: %s, %s.", status_code,
                                bytes(reply.readAll()).decode())
            self.writeError.emit()
            return

        Logger.log("i", "Print job uploaded successfully: %s", reply.readAll())
        url = "{}/cluster/{}/print/{}".format(self.CLUSTER_API_ROOT, self._device_id, job_id)
        self.post(url, data="", on_finished=self._onPrintJobRequested)

    def _onPrintJobRequested(self, reply: QNetworkReply) -> None:
        status_code, response = self._parseReply(reply)
        if status_code > 204 or not isinstance(response, dict) or "data" not in response:
            Logger.log("w", "Got unexpected response while trying to request printing: %s, %s",
                       status_code, response)
            self.writeError.emit()
            return

        print_response = PrintResponse(**response["data"])
        Logger.log("i", "Print job requested successfully: %s", print_response.__dict__)
        self.writeFinished.emit()

    def _showUploadErrorMessage(self):
        message = Message(self.I18N_CATALOG.i18nc(
            "@info:status", "Sending new jobs (temporarily) blocked, still sending the previous print job."))
        message.show()

    def _showOrUpdateUploadProgressMessage(self, new_progress = 0):
        # TODO: implement this
        # See ClusterUM3OutputDevice for inspiration
        pass

    def _showUploadSuccessMessage(self):
        # TODO: implement this
        pass
