# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
import os
from typing import List, Optional, Dict

from PyQt5.QtCore import QObject, pyqtSignal, QUrl, pyqtProperty
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest

from UM import i18nCatalog
from UM.FileHandler.FileHandler import FileHandler
from UM.Logger import Logger
from UM.Scene.SceneNode import SceneNode
from UM.Settings import ContainerRegistry
from cura.CuraApplication import CuraApplication
from cura.PrinterOutput import PrinterOutputController, PrintJobOutputModel
from cura.PrinterOutput.MaterialOutputModel import MaterialOutputModel
from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice, AuthState
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
from .Models import CloudClusterPrinter, CloudClusterPrinterConfiguration, CloudClusterPrinterConfigurationMaterial, CloudClusterPrintJob, CloudClusterPrintJobConstraint

from .CloudOutputController import CloudOutputController
from ..UM3PrintJobOutputModel import UM3PrintJobOutputModel


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
    # TODO: Make sure that this url goes to the live api before release
    API_ROOT_PATH_FORMAT = "https://api-staging.ultimaker.com/connect/v1/clusters/{cluster_id}"
    
    # Signal triggered when the printers in the remote cluster were changed.
    printersChanged = pyqtSignal()

    # Signal triggered when the print jobs in the queue were changed.
    printJobsChanged = pyqtSignal()

    def __init__(self, device_id: str, parent: QObject = None):
        super().__init__(device_id = device_id, address = "", properties = {}, parent = parent)
        self._setInterfaceElements()
        
        self._device_id = device_id
        self._account = CuraApplication.getInstance().getCuraAPI().account

        # We re-use the Cura Connect monitor tab to get the most functionality right away.
        self._monitor_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "../../resources/qml/ClusterMonitorItem.qml")
        self._control_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "../../resources/qml/ClusterControlItem.qml")
        
        # Properties to populate later on with received cloud data.
        self._printers = {}  # type: Dict[str, PrinterOutputModel]
        self._print_jobs = {}  # type: Dict[str, PrintJobOutputModel]
        self._number_of_extruders = 2  # All networked printers are dual-extrusion Ultimaker machines.
    
    ##  We need to override _createEmptyRequest to work for the cloud.
    def _createEmptyRequest(self, path: str, content_type: Optional[str] = "application/json") -> QNetworkRequest:
        url = QUrl(self.API_ROOT_PATH_FORMAT.format(cluster_id = self._device_id) + path)
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
        self.setPriority(3)
        self.setName(self._id)
        # TODO: how to name these?
        self.setShortDescription(self.I18N_CATALOG.i18nc("@action:button", "Print via Cloud"))
        self.setDescription(self.I18N_CATALOG.i18nc("@properties:tooltip", "Print via Cloud"))
        self.setConnectionText(self.I18N_CATALOG.i18nc("@info:status", "Connected via Cloud"))
    
    ##  Called when Cura requests an output device to receive a (G-code) file.
    def requestWrite(self, nodes: List[SceneNode], file_name: Optional[str] = None, limit_mime_types: bool = False,
                     file_handler: Optional[FileHandler] = None, **kwargs: str) -> None:
        self.writeStarted.emit(self)
        self._addPrintJobToQueue()

    ##  Get remote printers.
    @pyqtProperty("QVariantList", notify = printersChanged)
    def printers(self):
        return self._printers

    ##  Get remote print jobs.
    @pyqtProperty("QVariantList", notify = printJobsChanged)
    def queuedPrintJobs(self) -> List[UM3PrintJobOutputModel]:
        return [print_job for print_job in self._print_jobs if print_job.state == "queued" or print_job.state == "error"]

    ##  Called when the connection to the cluster changes.
    def connect(self) -> None:
        super().connect()

    ##  Called when the network data should be updated.
    def _update(self) -> None:
        super()._update()
        self.get("/status", on_finished = self._onStatusCallFinished)

    ##  Method called when HTTP request to status endpoint is finished.
    #   Contains both printers and print jobs statuses in a single response.
    def _onStatusCallFinished(self, reply: QNetworkReply) -> None:
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code != 200:
            Logger.log("w", "Got unexpected response while trying to get cloud cluster data: {}, {}"
                       .format(status_code, reply.readAll()))
            return
        
        printers, print_jobs = self._parseStatusResponse(reply)
        if not printers and not print_jobs:
            return
        
        # Update all data from the cluster.
        self._updatePrinters(printers)
        self._updatePrintJobs(print_jobs)

    @staticmethod
    def _parseStatusResponse(reply: QNetworkReply): # Optional[(CloudClusterPrinter, CloudClusterPrintJob)] doesn't work

        printers = []
        print_jobs = []
        s = ''
        try:
            s = json.loads(bytes(reply.readAll()).decode("utf-8"))

            for p in s["printers"]:
                printer = CloudClusterPrinter(**p)
                configuration = printer.configuration
                printer.configuration = []
                for c in configuration:
                    extruder = CloudClusterPrinterConfiguration(**c)
                    extruder.material = CloudClusterPrinterConfigurationMaterial(extruder.material)
                    printer.configuration.append(extruder)

                printers.append(printer)

            for j in s["print_jobs"]:
                job = CloudClusterPrintJob(**j)
                constraints = job.constraints
                job.constraints = []
                for c in constraints:
                    job.constraints.append(CloudClusterPrintJobConstraint(**c))

                configuration = job.configuration
                job.configuration = []
                for c in configuration:
                    configuration = CloudClusterPrinterConfiguration(**c)
                    configuration.material = CloudClusterPrinterConfigurationMaterial(configuration.material)
                    job.configuration.append(configuration)

                print_jobs.append(job)

        except json.decoder.JSONDecodeError:
            Logger.logException("w", "Unable to decode JSON from reply.")
            return None

        return printers, print_jobs

    def _updatePrinters(self, printers: List[CloudClusterPrinter]) -> None:
        remote_printers = {p.uuid: p for p in printers}

        removed_printers = set(self._printers.keys()).difference(set(remote_printers.keys()))
        new_printers = set(remote_printers.keys()).difference(set(self._printers.keys()))
        updated_printers = set(self._printers.keys()).intersection(set(remote_printers.keys()))

        for p in removed_printers:
            self._removePrinter(p)

        for p in new_printers:
            self._addPrinter(printers[p])
            self._updatePrinter(printers[p])

        for p in updated_printers:
            self._updatePrinter(printers[p])

        # TODO: properly handle removed and updated printers
        self.printersChanged.emit()


    def _addPrinter(self, printer):
        self._printers[printer.uuid] = self._createPrinterOutputModel(self, printer)

    def _createPrinterOutputModel(self, printer: CloudClusterPrinter) -> PrinterOutputModel:
        return PrinterOutputModel(PrinterOutputController(self), len(printer.configuration),
                                  firmware_version=printer.firmware_version)

    def _updatePrinter(self, guid : str, printer : CloudClusterPrinter):
        model = self._printers[guid]
        self._printers[guid] = self._updatePrinterOutputModel(self, printer)

    def _updatePrinterOutputModel(self, printer: CloudClusterPrinter, model : PrinterOutputModel) -> PrinterOutputModel:
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

            material_data = extruder_data.material
            if extruder.activeMaterial is None or extruder.activeMaterial.guid != material.guid:
                material = self._createMaterialOutputModel(material_data)
                extruder.updateActiveMaterial(material)

    def _createMaterialOutputModel(self, material: CloudClusterPrinterConfigurationMaterial) -> MaterialOutputModel:
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


    def _removePrinter(self, guid):
        del self._printers[guid]

    def _updatePrintJobs(self, jobs: List[CloudClusterPrintJob]) -> None:
        remote_jobs = {j.uuid: j for j in jobs}

        removed_jobs = set(self._print_jobs.keys()).difference(set(remote_jobs.keys()))
        new_jobs = set(remote_jobs.keys()).difference(set(self._print_jobs.keys()))
        updated_jobs = set(self._print_jobs.keys()).intersection(set(remote_jobs.keys()))

        for j in removed_jobs:
            self._removePrintJob(j)

        for j in new_jobs:
            self._addPrintJob(jobs[j])

        for j in updated_jobs:
            self._updatePrintJob(jobs[j])

        # TODO: properly handle removed and updated printers
        self.printJobsChanged()

    def _addPrintJob(self, job: CloudClusterPrintJob):
        self._print_jobs[job.uuid] = self._createPrintJobOutputModel(job)

    def _createPrintJobOutputModel(self, job:CloudClusterPrintJob) -> PrintJobOutputModel:
        controller = self._printers[job.printer_uuid]._controller  # TODO: Can we access this property?
        model = PrintJobOutputModel(controller, job.uuid, job.name)
        assigned_printer = self._printes[job.printer_uuid]  # TODO: Or do we have to use the assigned_to field?
        model.updateAssignedPrinter(assigned_printer)

    def _updatePrintJobOutputModel(self, guid: str, job:CloudClusterPrintJob):
        model =self._print_jobs[guid]

        model.updateTimeTotal(job.time_total)
        model.updateTimeElapsed(job.time_elapsed)
        model.updateOwner(job.owner)
        model.updateState(job.status)

    def _removePrintJob(self, guid:str):
        del self._print_jobs[guid]

    def _addPrintJobToQueue(self):
        # TODO: implement this
        pass
