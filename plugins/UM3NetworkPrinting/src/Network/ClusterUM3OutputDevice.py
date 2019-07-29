# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional, Dict, List, Any

from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import pyqtSlot, QUrl, pyqtSignal, pyqtProperty

from UM.FileHandler.FileHandler import FileHandler
from UM.Logger import Logger
from UM.i18n import i18nCatalog
from UM.Scene.SceneNode import SceneNode
from cura.PrinterOutput.NetworkedPrinterOutputDevice import AuthState
from cura.PrinterOutput.PrinterOutputDevice import ConnectionType

from .ClusterApiClient import ClusterApiClient
from ..SendMaterialJob import SendMaterialJob
from ..UltimakerNetworkedPrinterOutputDevice import UltimakerNetworkedPrinterOutputDevice


I18N_CATALOG = i18nCatalog("cura")


class ClusterUM3OutputDevice(UltimakerNetworkedPrinterOutputDevice):

    activeCameraUrlChanged = pyqtSignal()

    def __init__(self, device_id: str, address: str, properties: Dict[bytes, bytes], parent=None) -> None:

        super().__init__(
            device_id=device_id,
            address=address,
            properties=properties,
            connection_type=ConnectionType.NetworkConnection,
            parent=parent
        )

        # API client for making requests to the print cluster.
        self._cluster_api = ClusterApiClient(address, on_error=self._onNetworkError)
        # We don't have authentication over local networking, so we're always authenticated.
        self.setAuthenticationState(AuthState.Authenticated)

        self._setInterfaceElements()

        self._active_camera_url = QUrl()  # type: QUrl

        # self._number_of_extruders = 2
        # self._dummy_lambdas = (
        #     "", {}, io.BytesIO()
        # )  # type: Tuple[Optional[str], Dict[str, Union[str, int, bool]], Union[io.StringIO, io.BytesIO]]
        # self._error_message = None  # type: Optional[Message]
        # self._write_job_progress_message = None  # type: Optional[Message]
        # self._progress_message = None  # type: Optional[Message]
        # self._printer_selection_dialog = None  # type: QObject
        # self._printer_uuid_to_unique_name_mapping = {}  # type: Dict[str, str]
        # self._finished_jobs = []  # type: List[UM3PrintJobOutputModel]
        # self._sending_job = None

    ##  Set all the interface elements and texts for this output device.
    def _setInterfaceElements(self) -> None:
        self.setPriority(3)  # Make sure the output device gets selected above local file output
        self.setName(self._id)
        self.setShortDescription(I18N_CATALOG.i18nc("@action:button Preceded by 'Ready to'.", "Print over network"))
        self.setDescription(I18N_CATALOG.i18nc("@properties:tooltip", "Print over network"))
        self.setConnectionText(I18N_CATALOG.i18nc("@info:status", "Connected over the network"))

    ## Called when the connection to the cluster changes.
    def connect(self) -> None:
        super().connect()
        self.sendMaterialProfiles()

    @pyqtProperty(QUrl, notify=activeCameraUrlChanged)
    def activeCameraUrl(self) -> QUrl:
        return self._active_camera_url

    @pyqtSlot(QUrl, name="setActiveCameraUrl")
    def setActiveCameraUrl(self, camera_url: QUrl) -> None:
        if self._active_camera_url != camera_url:
            self._active_camera_url = camera_url
            self.activeCameraUrlChanged.emit()

    @pyqtSlot(name="openPrintJobControlPanel")
    def openPrintJobControlPanel(self) -> None:
        QDesktopServices.openUrl(QUrl("http://" + self._address + "/print_jobs"))

    @pyqtSlot(name="openPrinterControlPanel")
    def openPrinterControlPanel(self) -> None:
        QDesktopServices.openUrl(QUrl("http://" + self._address + "/printers"))

    @pyqtSlot(str, name="sendJobToTop")
    def sendJobToTop(self, print_job_uuid: str) -> None:
        self._cluster_api.doPrintJobAction(print_job_uuid, "move", {"to_position": 0, "list": "queued"})

    @pyqtSlot(str, name="deleteJobFromQueue")
    def deleteJobFromQueue(self, print_job_uuid: str) -> None:
        self._cluster_api.doPrintJobAction(print_job_uuid, "delete")

    @pyqtSlot(str, name="forceSendJob")
    def forceSendJob(self, print_job_uuid: str) -> None:
        self._cluster_api.doPrintJobAction(print_job_uuid, "force")

    ## Set the remote print job state.
    #  \param print_job_uuid: The UUID of the print job to set the state for.
    #  \param action: The action to undertake ('pause', 'resume', 'abort').
    def setJobState(self, print_job_uuid: str, action: str) -> None:
        self._cluster_api.doPrintJobAction(print_job_uuid, action)

    ## Handle network errors.
    @staticmethod
    def _onNetworkError(errors: Dict[str, Any]):
        Logger.log("w", str(errors))

    def _update(self) -> None:
        super()._update()
        self._cluster_api.getPrinters(self._updatePrinters)
        self._cluster_api.getPrintJobs(self._updatePrintJobs)
        # for print_job in self._print_jobs:
        #     if print_job.getPreviewImage() is None:
        #         self.get("print_jobs/{uuid}/preview_image".format(uuid=print_job.key), on_finished=self._onGetPreviewImageFinished)

    ##  Sync the material profiles in Cura with the printer.
    #   This gets called when connecting to a printer as well as when sending a print.
    def sendMaterialProfiles(self) -> None:
        job = SendMaterialJob(device=self)
        job.run()



    # TODO FROM HERE



    def requestWrite(self, nodes: List["SceneNode"], file_name: Optional[str] = None, limit_mimetypes: bool = False,
                     file_handler: Optional["FileHandler"] = None, filter_by_machine: bool = False, **kwargs) -> None:
        pass
        # self.writeStarted.emit(self)
        #
        # self.sendMaterialProfiles()
        #
        # mesh_format = MeshFormatHandler(file_handler, self.firmwareVersion)
        #
        # # This function pauses with the yield, waiting on instructions on which printer it needs to print with.
        # if not mesh_format.is_valid:
        #     Logger.log("e", "Missing file or mesh writer!")
        #     return
        # self._sending_job = self._sendPrintJob(mesh_format, nodes)
        # if self._sending_job is not None:
        #     self._sending_job.send(None)  # Start the generator.
        #
        #     if len(self._printers) > 1:  # We need to ask the user.
        #         self._spawnPrinterSelectionDialog()
        #     else:  # Just immediately continue.
        #         self._sending_job.send("")  # No specifically selected printer.
        #         self._sending_job.send(None)
    #
    # def _spawnPrinterSelectionDialog(self):
    #     if self._printer_selection_dialog is None:
    #         if PluginRegistry.getInstance() is not None:
    #             path = os.path.join(
    #                 PluginRegistry.getInstance().getPluginPath("UM3NetworkPrinting"),
    #                 "resources", "qml", "PrintWindow.qml"
    #             )
    #             self._printer_selection_dialog = self._application.createQmlComponent(path, {"OutputDevice": self})
    #     if self._printer_selection_dialog is not None:
    #         self._printer_selection_dialog.show()

    # ##  Allows the user to choose a printer to print with from the printer
    # #   selection dialogue.
    # #   \param target_printer The name of the printer to target.
    # @pyqtSlot(str)
    # def selectPrinter(self, target_printer: str = "") -> None:
    #     if self._sending_job is not None:
    #         self._sending_job.send(target_printer)

    # @pyqtSlot()
    # def cancelPrintSelection(self) -> None:
    #     self._sending_gcode = False

    # ##  Greenlet to send a job to the printer over the network.
    # #
    # #   This greenlet gets called asynchronously in requestWrite. It is a
    # #   greenlet in order to optionally wait for selectPrinter() to select a
    # #   printer.
    # #   The greenlet yields exactly three times: First time None,
    # #   \param mesh_format Object responsible for choosing the right kind of format to write with.
    # def _sendPrintJob(self, mesh_format: MeshFormatHandler, nodes: List[SceneNode]):
    #     Logger.log("i", "Sending print job to printer.")
    #     if self._sending_gcode:
    #         self._error_message = Message(
    #             I18N_CATALOG.i18nc("@info:status",
    #                                "Sending new jobs (temporarily) blocked, still sending the previous print job."))
    #         self._error_message.show()
    #         yield #Wait on the user to select a target printer.
    #         yield #Wait for the write job to be finished.
    #         yield False #Return whether this was a success or not.
    #         yield #Prevent StopIteration.
    #
    #     self._sending_gcode = True
    #
    #     # Potentially wait on the user to select a target printer.
    #     target_printer = yield  # type: Optional[str]
    #
    #     # Using buffering greatly reduces the write time for many lines of gcode
    #
    #     stream = mesh_format.createStream()
    #
    #     job = WriteFileJob(mesh_format.writer, stream, nodes, mesh_format.file_mode)
    #
    #     self._write_job_progress_message = Message(I18N_CATALOG.i18nc("@info:status", "Sending data to printer"),
    #                                                lifetime = 0, dismissable = False, progress = -1,
    #                                                title = I18N_CATALOG.i18nc("@info:title", "Sending Data"),
    #                                                use_inactivity_timer = False)
    #     self._write_job_progress_message.show()
    #
    #     if mesh_format.preferred_format is not None:
    #         self._dummy_lambdas = (target_printer, mesh_format.preferred_format, stream)
    #         job.finished.connect(self._sendPrintJobWaitOnWriteJobFinished)
    #         job.start()
    #         yield True  # Return that we had success!
    #         yield  # To prevent having to catch the StopIteration exception.

    # def _sendPrintJobWaitOnWriteJobFinished(self, job: WriteFileJob) -> None:
    #     if self._write_job_progress_message:
    #         self._write_job_progress_message.hide()
    #
    #     self._progress_message = Message(I18N_CATALOG.i18nc("@info:status", "Sending data to printer"), lifetime = 0,
    #                                      dismissable = False, progress = -1,
    #                                      title = I18N_CATALOG.i18nc("@info:title", "Sending Data"))
    #     self._progress_message.addAction("Abort", I18N_CATALOG.i18nc("@action:button", "Cancel"), icon = "",
    #                                      description = "")
    #     self._progress_message.actionTriggered.connect(self._progressMessageActionTriggered)
    #     self._progress_message.show()
    #     parts = []
    #
    #     target_printer, preferred_format, stream = self._dummy_lambdas
    #
    #     # If a specific printer was selected, it should be printed with that machine.
    #     if target_printer:
    #         target_printer = self._printer_uuid_to_unique_name_mapping[target_printer]
    #         parts.append(self._createFormPart("name=require_printer_name", bytes(target_printer, "utf-8"), "text/plain"))
    #
    #     # Add user name to the print_job
    #     parts.append(self._createFormPart("name=owner", bytes(self._getUserName(), "utf-8"), "text/plain"))
    #
    #     file_name = self._application.getPrintInformation().jobName + "." + preferred_format["extension"]
    #
    #     output = stream.getvalue()  # Either str or bytes depending on the output mode.
    #     if isinstance(stream, io.StringIO):
    #         output = cast(str, output).encode("utf-8")
    #     output = cast(bytes, output)
    #
    #     parts.append(self._createFormPart("name=\"file\"; filename=\"%s\"" % file_name, output))
    #
    #     self._latest_reply_handler = self.postFormWithParts("print_jobs/", parts,
    #                                                         on_finished = self._onPostPrintJobFinished,
    #                                                         on_progress = self._onUploadPrintJobProgress)

    # def _onPostPrintJobFinished(self, reply: QNetworkReply) -> None:
    #     if self._progress_message:
    #         self._progress_message.hide()
    #     self._compressing_gcode = False
    #     self._sending_gcode = False

    # def _onUploadPrintJobProgress(self, bytes_sent: int, bytes_total: int) -> None:
    #     if bytes_total > 0:
    #         new_progress = bytes_sent / bytes_total * 100
    #         # Treat upload progress as response. Uploading can take more than 10 seconds, so if we don't, we can get
    #         # timeout responses if this happens.
    #         self._last_response_time = time()
    #         if self._progress_message is not None and new_progress != self._progress_message.getProgress():
    #             self._progress_message.show()  # Ensure that the message is visible.
    #             self._progress_message.setProgress(bytes_sent / bytes_total * 100)
    #
    #         # If successfully sent:
    #         if bytes_sent == bytes_total:
    #             # Show a confirmation to the user so they know the job was sucessful and provide the option to switch to
    #             # the monitor tab.
    #             self._success_message = Message(
    #                 I18N_CATALOG.i18nc("@info:status", "Print job was successfully sent to the printer."),
    #                 lifetime=5, dismissable=True,
    #                 title=I18N_CATALOG.i18nc("@info:title", "Data Sent"))
    #             self._success_message.addAction("View", I18N_CATALOG.i18nc("@action:button", "View in Monitor"), icon = "",
    #                                             description="")
    #             self._success_message.actionTriggered.connect(self._successMessageActionTriggered)
    #             self._success_message.show()
    #     else:
    #         if self._progress_message is not None:
    #             self._progress_message.setProgress(0)
    #             self._progress_message.hide()

    # def _progressMessageActionTriggered(self, message_id: Optional[str] = None, action_id: Optional[str] = None) -> None:
    #     if action_id == "Abort":
    #         Logger.log("d", "User aborted sending print to remote.")
    #         if self._progress_message is not None:
    #             self._progress_message.hide()
    #         self._compressing_gcode = False
    #         self._sending_gcode = False
    #         self._application.getController().setActiveStage("PrepareStage")
    #
    #         # After compressing the sliced model Cura sends data to printer, to stop receiving updates from the request
    #         # the "reply" should be disconnected
    #         if self._latest_reply_handler:
    #             self._latest_reply_handler.disconnect()
    #             self._latest_reply_handler = None

    # def _successMessageActionTriggered(self, message_id: Optional[str] = None, action_id: Optional[str] = None) -> None:
    #     if action_id == "View":
    #         self._application.getController().setActiveStage("MonitorStage")

    # def _onGetPreviewImageFinished(self, reply: QNetworkReply) -> None:
    #     reply_url = reply.url().toString()
    #
    #     uuid = reply_url[reply_url.find("print_jobs/")+len("print_jobs/"):reply_url.rfind("/preview_image")]
    #
    #     print_job = findByKey(self._print_jobs, uuid)
    #     if print_job:
    #         image = QImage()
    #         image.loadFromData(reply.readAll())
    #         print_job.updatePreviewImage(image)

    # def _createMaterialOutputModel(self, material_data: Dict[str, Any]) -> "MaterialOutputModel":
    #     material_manager = self._application.getMaterialManager()
    #     material_group_list = None
    #
    #     # Avoid crashing if there is no "guid" field in the metadata
    #     material_guid = material_data.get("guid")
    #     if material_guid:
    #         material_group_list = material_manager.getMaterialGroupListByGUID(material_guid)
    #
    #     # This can happen if the connected machine has no material in one or more extruders (if GUID is empty), or the
    #     # material is unknown to Cura, so we should return an "empty" or "unknown" material model.
    #     if material_group_list is None:
    #         material_name = I18N_CATALOG.i18nc("@label:material", "Empty") if len(material_data.get("guid", "")) == 0 \
    #                     else I18N_CATALOG.i18nc("@label:material", "Unknown")
    #
    #         return MaterialOutputModel(guid = material_data.get("guid", ""),
    #                                     type = material_data.get("material", ""),
    #                                     color = material_data.get("color", ""),
    #                                     brand = material_data.get("brand", ""),
    #                                     name = material_data.get("name", material_name)
    #                                     )
    #
    #     # Sort the material groups by "is_read_only = True" first, and then the name alphabetically.
    #     read_only_material_group_list = list(filter(lambda x: x.is_read_only, material_group_list))
    #     non_read_only_material_group_list = list(filter(lambda x: not x.is_read_only, material_group_list))
    #     material_group = None
    #     if read_only_material_group_list:
    #         read_only_material_group_list = sorted(read_only_material_group_list, key = lambda x: x.name)
    #         material_group = read_only_material_group_list[0]
    #     elif non_read_only_material_group_list:
    #         non_read_only_material_group_list = sorted(non_read_only_material_group_list, key = lambda x: x.name)
    #         material_group = non_read_only_material_group_list[0]
    #
    #     if material_group:
    #         container = material_group.root_material_node.getContainer()
    #         color = container.getMetaDataEntry("color_code")
    #         brand = container.getMetaDataEntry("brand")
    #         material_type = container.getMetaDataEntry("material")
    #         name = container.getName()
    #     else:
    #         Logger.log("w",
    #                    "Unable to find material with guid {guid}. Using data as provided by cluster".format(
    #                        guid=material_data["guid"]))
    #         color = material_data["color"]
    #         brand = material_data["brand"]
    #         material_type = material_data["material"]
    #         name = I18N_CATALOG.i18nc("@label:material", "Empty") if material_data["material"] == "empty" \
    #             else I18N_CATALOG.i18nc("@label:material", "Unknown")
    #     return MaterialOutputModel(guid = material_data["guid"], type = material_type,
    #                                brand = brand, color = color, name = name)
