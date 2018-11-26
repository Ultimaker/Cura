# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
from typing import List, Optional, Dict

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, QUrl
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest

from UM import i18nCatalog
from UM.FileHandler.FileHandler import FileHandler
from UM.Logger import Logger
from UM.Scene.SceneNode import SceneNode
from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice, AuthState
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel

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
        
        # Properties to populate later on with received cloud data.
        self._printers = []
        self._print_jobs = []
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
    def printJobs(self) -> List[UM3PrintJobOutputModel]:
        return self._print_jobs

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
