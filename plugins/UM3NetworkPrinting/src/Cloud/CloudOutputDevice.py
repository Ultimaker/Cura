# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
from typing import List, Optional, Dict

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest

from UM import i18nCatalog
from UM.FileHandler.FileHandler import FileHandler
from UM.Logger import Logger
from UM.Scene.SceneNode import SceneNode
from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice, AuthState
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
from plugins.UM3NetworkPrinting.src.Cloud.CloudOutputController import CloudOutputController
from plugins.UM3NetworkPrinting.src.UM3PrintJobOutputModel import UM3PrintJobOutputModel


##  The cloud output device is a network output device that works remotely but has limited functionality.
#   Currently it only supports viewing the printer and print job status and adding a new job to the queue.
#   As such, those methods have been implemented here.
#   Note that this device represents a single remote cluster, not a list of multiple clusters.
#
#   TODO: figure our how the QML interface for the cluster networking should operate with this limited functionality.
#   TODO: figure out how to pair remote clusters, local networked clusters and local cura printer presets.
class CloudOutputDevice(NetworkedPrinterOutputDevice):
    
    # The translation catalog for this device.
    I18N_CATALOG = i18nCatalog("cura")

    # The cloud URL to use for remote clusters.
    API_ROOT_PATH_FORMAT = "https://api.ultimaker.com/connect/v1/clusters/{cluster_id}"
    
    # Signal triggered when the printers in the remote cluster were changed.
    printersChanged = pyqtSignal()

    # Signal triggered when the print jobs in the queue were changed.
    printJobsChanged = pyqtSignal()
    
    def __init__(self, device_id: str, address: str, properties: Dict[bytes, bytes], parent: QObject = None):
        super().__init__(device_id = device_id, address = address, properties = properties, parent = parent)
        self._setInterfaceElements()
        
        # The API prefix is automatically added when doing any HTTP call on the device.
        self._api_prefix = self.API_ROOT_PATH_FORMAT.format(device_id)  # TODO: verify we can use device_id here
        self._authentication_state = AuthState.Authenticated  # TODO: use cura.API.Account to set this?
        
        # Properties to populate later on with received cloud data.
        self._printers = []
        self._print_jobs = []
        self._number_of_extruders = 2  # All networked printers are dual-extrusion Ultimaker machines.
    
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
        
        # TODO: actually implement this
        self._addPrintJobToQueue()

    ##  Get remote printers.
    @pyqtProperty("QVariantList", notify = printersChanged)
    def printers(self):
        return self._printers

    ##  Get remote print jobs.
    @pyqtProperty("QVariantList", notify = printJobsChanged)
    def printJobs(self) -> List[UM3PrintJobOutputModel]:
        return self._print_jobs

    ##  Called when the connection to the cluster changes.
    def connect(self) -> None:
        super().connect()

    ##  Called when the network data should be updated.
    def _update(self) -> None:
        super()._update()
        self.get("/status", on_finished = self._onStatusCallFinished)

    def _onStatusCallFinished(self, reply: QNetworkReply) -> None:
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code != 200:
            Logger.log("w", "Got unexpected response while trying to get cloud cluster data: {}, {}"
                       .format(status_code, reply.getErrorString()))
            return
        
        data = self._parseStatusResponse(reply)
        if data is None:
            return
        
        # Update all data from the cluster.
        self._updatePrinters(data.get("printers", []))
        self._updatePrintJobs(data.get("print_jobs", []))

    @staticmethod
    def _parseStatusResponse(reply: QNetworkReply) -> Optional[dict]:
        try:
            result = json.loads(bytes(reply.readAll()).decode("utf-8"))
            # TODO: use model or named tuple here.
            return result
        except json.decoder.JSONDecodeError:
            Logger.logException("w", "Unable to decode JSON from reply.")
            return None

    def _updatePrinters(self, remote_printers: List[Dict[str, any]]) -> None:
        # TODO: use model or tuple for remote_printers data
        for printer in remote_printers:
        
            # If the printer does not exist yet, create it.
            if not self._getPrinterByKey(printer["uuid"]):
                self._printers.append(PrinterOutputModel(
                        output_controller = CloudOutputController(self),
                        number_of_extruders = self._number_of_extruders
                ))
    
        # TODO: properly handle removed and updated printers
        self.printersChanged.emit()

    def _updatePrintJobs(self, remote_print_jobs: List[Dict[str, any]]) -> None:
        # TODO: use model or tuple for remote_print_jobs data
        pass

    def _addPrintJobToQueue(self):
        # TODO: implement this
        pass
