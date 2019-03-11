from typing import List, Optional

from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice, AuthState
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel
from cura.PrinterOutput.MaterialOutputModel import MaterialOutputModel
from cura.PrinterOutputDevice import ConnectionType

from cura.Settings.ContainerManager import ContainerManager
from cura.Settings.ExtruderManager import ExtruderManager

from UM.FileHandler.FileHandler import FileHandler
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Message import Message
from UM.PluginRegistry import PluginRegistry
from UM.Scene.SceneNode import SceneNode
from UM.Settings.ContainerRegistry import ContainerRegistry

from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtCore import QTimer, QUrl
from PyQt5.QtWidgets import QMessageBox

from .LegacyUM3PrinterOutputController import LegacyUM3PrinterOutputController

from time import time

import json
import os


i18n_catalog = i18nCatalog("cura")


##  This is the output device for the "Legacy" API of the UM3. All firmware before 4.0.1 uses this API.
#   Everything after that firmware uses the ClusterUM3Output.
#   The Legacy output device can only have one printer (whereas the cluster can have 0 to n).
#
#   Authentication is done in a number of steps;
#   1. Request an id / key pair by sending the application & user name. (state = authRequested)
#   2. Machine sends this back and will display an approve / deny message on screen. (state = AuthReceived)
#   3. OutputDevice will poll if the button was pressed.
#   4. At this point the machine either has the state Authenticated or AuthenticationDenied.
#   5. As a final step, we verify the authentication, as this forces the QT manager to setup the authenticator.
class LegacyUM3OutputDevice(NetworkedPrinterOutputDevice):
    def __init__(self, device_id, address: str, properties, parent = None) -> None:
        super().__init__(device_id = device_id, address = address, properties = properties, connection_type =  ConnectionType.NetworkConnection, parent = parent)
        self._api_prefix = "/api/v1/"
        self._number_of_extruders = 2

        self._authentication_id = None
        self._authentication_key = None

        self._authentication_counter = 0
        self._max_authentication_counter = 5 * 60  # Number of attempts before authentication timed out (5 min)

        self._authentication_timer = QTimer()
        self._authentication_timer.setInterval(1000)  # TODO; Add preference for update interval
        self._authentication_timer.setSingleShot(False)

        self._authentication_timer.timeout.connect(self._onAuthenticationTimer)

        # The messages are created when connect is called the first time.
        # This ensures that the messages are only created for devices that actually want to connect.
        self._authentication_requested_message = None
        self._authentication_failed_message = None
        self._authentication_succeeded_message = None
        self._not_authenticated_message = None

        self.authenticationStateChanged.connect(self._onAuthenticationStateChanged)

        self.setPriority(3)  # Make sure the output device gets selected above local file output
        self.setName(self._id)
        self.setShortDescription(i18n_catalog.i18nc("@action:button Preceded by 'Ready to'.", "Print over network"))
        self.setDescription(i18n_catalog.i18nc("@properties:tooltip", "Print over network"))

        self.setIconName("print")

        if PluginRegistry.getInstance() is not None:
            self._monitor_view_qml_path = os.path.join(
                PluginRegistry.getInstance().getPluginPath("UM3NetworkPrinting"),
                "resources", "qml", "MonitorStage.qml"
            )

        self._output_controller = LegacyUM3PrinterOutputController(self)

    def _onAuthenticationStateChanged(self):
        # We only accept commands if we are authenticated.
        self._setAcceptsCommands(self._authentication_state == AuthState.Authenticated)

        if self._authentication_state == AuthState.Authenticated:
            self.setConnectionText(i18n_catalog.i18nc("@info:status", "Connected over the network."))
        elif self._authentication_state == AuthState.AuthenticationRequested:
            self.setConnectionText(i18n_catalog.i18nc("@info:status",
                                                      "Connected over the network. Please approve the access request on the printer."))
        elif self._authentication_state == AuthState.AuthenticationDenied:
            self.setConnectionText(i18n_catalog.i18nc("@info:status", "Connected over the network. No access to control the printer."))


    def _setupMessages(self):
        self._authentication_requested_message = Message(i18n_catalog.i18nc("@info:status",
                                                                            "Access to the printer requested. Please approve the request on the printer"),
                                                         lifetime=0, dismissable=False, progress=0,
                                                         title=i18n_catalog.i18nc("@info:title",
                                                                                  "Authentication status"))

        self._authentication_failed_message = Message("", title=i18n_catalog.i18nc("@info:title", "Authentication Status"))
        self._authentication_failed_message.addAction("Retry", i18n_catalog.i18nc("@action:button", "Retry"), None,
                                                      i18n_catalog.i18nc("@info:tooltip", "Re-send the access request"))
        self._authentication_failed_message.actionTriggered.connect(self._messageCallback)
        self._authentication_succeeded_message = Message(
            i18n_catalog.i18nc("@info:status", "Access to the printer accepted"),
            title=i18n_catalog.i18nc("@info:title", "Authentication Status"))

        self._not_authenticated_message = Message(
            i18n_catalog.i18nc("@info:status", "No access to print with this printer. Unable to send print job."),
            title=i18n_catalog.i18nc("@info:title", "Authentication Status"))
        self._not_authenticated_message.addAction("Request", i18n_catalog.i18nc("@action:button", "Request Access"),
                                                  None, i18n_catalog.i18nc("@info:tooltip",
                                                                           "Send access request to the printer"))
        self._not_authenticated_message.actionTriggered.connect(self._messageCallback)

    def _messageCallback(self, message_id=None, action_id="Retry"):
        if action_id == "Request" or action_id == "Retry":
            if self._authentication_failed_message:
                self._authentication_failed_message.hide()
            if self._not_authenticated_message:
                self._not_authenticated_message.hide()

            self._requestAuthentication()

    def connect(self):
        super().connect()
        self._setupMessages()
        global_container = CuraApplication.getInstance().getGlobalContainerStack()
        if global_container:
            self._authentication_id = global_container.getMetaDataEntry("network_authentication_id", None)
            self._authentication_key = global_container.getMetaDataEntry("network_authentication_key", None)

    def close(self):
        super().close()
        if self._authentication_requested_message:
            self._authentication_requested_message.hide()
        if self._authentication_failed_message:
            self._authentication_failed_message.hide()
        if self._authentication_succeeded_message:
            self._authentication_succeeded_message.hide()
        self._sending_gcode = False
        self._compressing_gcode = False
        self._authentication_timer.stop()

    ##  Send all material profiles to the printer.
    def _sendMaterialProfiles(self):
        Logger.log("i", "Sending material profiles to printer")

        # TODO: Might want to move this to a job...
        for container in ContainerRegistry.getInstance().findInstanceContainers(type="material"):
            try:
                xml_data = container.serialize()
                if xml_data == "" or xml_data is None:
                    continue

                names = ContainerManager.getInstance().getLinkedMaterials(container.getId())
                if names:
                    # There are other materials that share this GUID.
                    if not container.isReadOnly():
                        continue  # If it's not readonly, it's created by user, so skip it.

                file_name = "none.xml"

                self.postForm("materials", "form-data; name=\"file\";filename=\"%s\"" % file_name, xml_data.encode(), on_finished=None)

            except NotImplementedError:
                # If the material container is not the most "generic" one it can't be serialized an will raise a
                # NotImplementedError. We can simply ignore these.
                pass

    def requestWrite(self, nodes: List[SceneNode], file_name: Optional[str] = None, limit_mimetypes: bool = False, file_handler: Optional[FileHandler] = None, **kwargs: str) -> None:
        if not self.activePrinter:
            # No active printer. Unable to write
            return

        if self.activePrinter.state not in ["idle", ""]:
            # Printer is not able to accept commands.
            return

        if self._authentication_state != AuthState.Authenticated:
            # Not authenticated, so unable to send job.
            return

        self.writeStarted.emit(self)

        gcode_dict = getattr(CuraApplication.getInstance().getController().getScene(), "gcode_dict", [])
        active_build_plate_id = CuraApplication.getInstance().getMultiBuildPlateModel().activeBuildPlate
        gcode_list = gcode_dict[active_build_plate_id]

        if not gcode_list:
            # Unable to find g-code. Nothing to send
            return

        self._gcode = gcode_list

        errors = self._checkForErrors()
        if errors:
            text = i18n_catalog.i18nc("@label", "Unable to start a new print job.")
            informative_text = i18n_catalog.i18nc("@label",
                                                  "There is an issue with the configuration of your Ultimaker, which makes it impossible to start the print. "
                                                  "Please resolve this issues before continuing.")
            detailed_text = ""
            for error in errors:
                detailed_text += error + "\n"

            CuraApplication.getInstance().messageBox(i18n_catalog.i18nc("@window:title", "Mismatched configuration"),
                                                 text,
                                                 informative_text,
                                                 detailed_text,
                                                 buttons=QMessageBox.Ok,
                                                 icon=QMessageBox.Critical,
                                                callback = self._messageBoxCallback
                                                 )
            return  # Don't continue; Errors must block sending the job to the printer.

        # There might be multiple things wrong with the configuration. Check these before starting.
        warnings = self._checkForWarnings()

        if warnings:
            text = i18n_catalog.i18nc("@label", "Are you sure you wish to print with the selected configuration?")
            informative_text = i18n_catalog.i18nc("@label",
                                                  "There is a mismatch between the configuration or calibration of the printer and Cura. "
                                                  "For the best result, always slice for the PrintCores and materials that are inserted in your printer.")
            detailed_text = ""
            for warning in warnings:
                detailed_text += warning + "\n"

            CuraApplication.getInstance().messageBox(i18n_catalog.i18nc("@window:title", "Mismatched configuration"),
                                                 text,
                                                 informative_text,
                                                 detailed_text,
                                                 buttons=QMessageBox.Yes + QMessageBox.No,
                                                 icon=QMessageBox.Question,
                                                 callback=self._messageBoxCallback
                                                 )
            return

        # No warnings or errors, so we're good to go.
        self._startPrint()

        # Notify the UI that a switch to the print monitor should happen
        CuraApplication.getInstance().getController().setActiveStage("MonitorStage")

    def _startPrint(self):
        Logger.log("i", "Sending print job to printer.")
        if self._sending_gcode:
            self._error_message = Message(
                i18n_catalog.i18nc("@info:status",
                                   "Sending new jobs (temporarily) blocked, still sending the previous print job."))
            self._error_message.show()
            return

        self._sending_gcode = True

        self._send_gcode_start = time()
        self._progress_message = Message(i18n_catalog.i18nc("@info:status", "Sending data to printer"), 0, False, -1,
                                         i18n_catalog.i18nc("@info:title", "Sending Data"))
        self._progress_message.addAction("Abort", i18n_catalog.i18nc("@action:button", "Cancel"), None, "")
        self._progress_message.actionTriggered.connect(self._progressMessageActionTriggered)
        self._progress_message.show()
        
        compressed_gcode = self._compressGCode()
        if compressed_gcode is None:
            # Abort was called.
            return

        file_name = "%s.gcode.gz" % CuraApplication.getInstance().getPrintInformation().jobName
        self.postForm("print_job", "form-data; name=\"file\";filename=\"%s\"" % file_name, compressed_gcode,
                      on_finished=self._onPostPrintJobFinished)

        return

    def _progressMessageActionTriggered(self, message_id=None, action_id=None):
        if action_id == "Abort":
            Logger.log("d", "User aborted sending print to remote.")
            self._progress_message.hide()
            self._compressing_gcode = False
            self._sending_gcode = False
            CuraApplication.getInstance().getController().setActiveStage("PrepareStage")

    def _onPostPrintJobFinished(self, reply):
        self._progress_message.hide()
        self._sending_gcode = False

    def _onUploadPrintJobProgress(self, bytes_sent, bytes_total):
        if bytes_total > 0:
            new_progress = bytes_sent / bytes_total * 100
            # Treat upload progress as response. Uploading can take more than 10 seconds, so if we don't, we can get
            # timeout responses if this happens.
            self._last_response_time = time()
            if new_progress > self._progress_message.getProgress():
                self._progress_message.show()  # Ensure that the message is visible.
                self._progress_message.setProgress(bytes_sent / bytes_total * 100)
        else:
            self._progress_message.setProgress(0)

            self._progress_message.hide()

    def _messageBoxCallback(self, button):
        def delayedCallback():
            if button == QMessageBox.Yes:
                self._startPrint()
            else:
                CuraApplication.getInstance().getController().setActiveStage("PrepareStage")
                # For some unknown reason Cura on OSX will hang if we do the call back code
                # immediately without first returning and leaving QML's event system.

        QTimer.singleShot(100, delayedCallback)

    def _checkForErrors(self):
        errors = []
        print_information = CuraApplication.getInstance().getPrintInformation()
        if not print_information.materialLengths:
            Logger.log("w", "There is no material length information. Unable to check for errors.")
            return errors

        for index, extruder in enumerate(self.activePrinter.extruders):
            # Due to airflow issues, both slots must be loaded, regardless if they are actually used or not.
            if extruder.hotendID == "":
                # No Printcore loaded.
                errors.append(i18n_catalog.i18nc("@info:status", "No Printcore loaded in slot {slot_number}".format(slot_number=index + 1)))

            if index < len(print_information.materialLengths) and print_information.materialLengths[index] != 0:
                # The extruder is by this print.
                if extruder.activeMaterial is None:
                    # No active material
                    errors.append(i18n_catalog.i18nc("@info:status", "No material loaded in slot {slot_number}".format(slot_number=index + 1)))
        return errors

    def _checkForWarnings(self):
        warnings = []
        print_information = CuraApplication.getInstance().getPrintInformation()

        if not print_information.materialLengths:
            Logger.log("w", "There is no material length information. Unable to check for warnings.")
            return warnings

        extruder_manager = ExtruderManager.getInstance()

        for index, extruder in enumerate(self.activePrinter.extruders):
            if index < len(print_information.materialLengths) and print_information.materialLengths[index] != 0:
                # The extruder is by this print.

                # TODO: material length check

                # Check if the right Printcore is active.
                variant = extruder_manager.getExtruderStack(index).findContainer({"type": "variant"})
                if variant:
                    if variant.getName() != extruder.hotendID:
                        warnings.append(i18n_catalog.i18nc("@label", "Different PrintCore (Cura: {cura_printcore_name}, Printer: {remote_printcore_name}) selected for extruder {extruder_id}".format(cura_printcore_name = variant.getName(), remote_printcore_name = extruder.hotendID, extruder_id = index + 1)))
                else:
                    Logger.log("w", "Unable to find variant.")

                # Check if the right material is loaded.
                local_material = extruder_manager.getExtruderStack(index).findContainer({"type": "material"})
                if local_material:
                    if extruder.activeMaterial.guid != local_material.getMetaDataEntry("GUID"):
                        Logger.log("w", "Extruder %s has a different material (%s) as Cura (%s)", index + 1, extruder.activeMaterial.guid, local_material.getMetaDataEntry("GUID"))
                        warnings.append(i18n_catalog.i18nc("@label", "Different material (Cura: {0}, Printer: {1}) selected for extruder {2}").format(local_material.getName(), extruder.activeMaterial.name, index + 1))
                else:
                    Logger.log("w", "Unable to find material.")

        return warnings

    def _update(self):
        if not super()._update():
            return
        if self._authentication_state == AuthState.NotAuthenticated:
            if self._authentication_id is None and self._authentication_key is None:
                # This machine doesn't have any authentication, so request it.
                self._requestAuthentication()
            elif self._authentication_id is not None and self._authentication_key is not None:
                # We have authentication info, but we haven't checked it out yet. Do so now.
                self._verifyAuthentication()
        elif self._authentication_state == AuthState.AuthenticationReceived:
            # We have an authentication, but it's not confirmed yet.
            self._checkAuthentication()

        # We don't need authentication for requesting info, so we can go right ahead with requesting this.
        self.get("printer", on_finished=self._onGetPrinterDataFinished)
        self.get("print_job", on_finished=self._onGetPrintJobFinished)

    def _resetAuthenticationRequestedMessage(self):
        if self._authentication_requested_message:
            self._authentication_requested_message.hide()
        self._authentication_timer.stop()
        self._authentication_counter = 0

    def _onAuthenticationTimer(self):
        self._authentication_counter += 1
        self._authentication_requested_message.setProgress(
            self._authentication_counter / self._max_authentication_counter * 100)
        if self._authentication_counter > self._max_authentication_counter:
            self._authentication_timer.stop()
            Logger.log("i", "Authentication timer ended. Setting authentication to denied for printer: %s" % self._id)
            self.setAuthenticationState(AuthState.AuthenticationDenied)
            self._resetAuthenticationRequestedMessage()
            self._authentication_failed_message.show()

    def _verifyAuthentication(self):
        Logger.log("d", "Attempting to verify authentication")
        # This will ensure that the "_onAuthenticationRequired" is triggered, which will setup the authenticator.
        self.get("auth/verify", on_finished=self._onVerifyAuthenticationCompleted)

    def _onVerifyAuthenticationCompleted(self, reply):
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code == 401:
            # Something went wrong; We somehow tried to verify authentication without having one.
            Logger.log("d", "Attempted to verify auth without having one.")
            self._authentication_id = None
            self._authentication_key = None
            self.setAuthenticationState(AuthState.NotAuthenticated)
        elif status_code == 403 and self._authentication_state != AuthState.Authenticated:
            # If we were already authenticated, we probably got an older message back all of the sudden. Drop that.
            Logger.log("d",
                       "While trying to verify the authentication state, we got a forbidden response. Our own auth state was %s. ",
                       self._authentication_state)
            self.setAuthenticationState(AuthState.AuthenticationDenied)
            self._authentication_failed_message.show()
        elif status_code == 200:
            self.setAuthenticationState(AuthState.Authenticated)

    def _checkAuthentication(self):
        Logger.log("d", "Checking if authentication is correct for id %s and key %s", self._authentication_id, self._getSafeAuthKey())
        self.get("auth/check/" + str(self._authentication_id), on_finished=self._onCheckAuthenticationFinished)

    def _onCheckAuthenticationFinished(self, reply):
        if str(self._authentication_id) not in reply.url().toString():
            Logger.log("w", "Got an old id response.")
            # Got response for old authentication ID.
            return
        try:
            data = json.loads(bytes(reply.readAll()).decode("utf-8"))
        except json.decoder.JSONDecodeError:
            Logger.log("w", "Received an invalid authentication check from printer: Not valid JSON.")
            return

        if data.get("message", "") == "authorized":
            Logger.log("i", "Authentication was approved")
            self.setAuthenticationState(AuthState.Authenticated)
            self._saveAuthentication()

            # Double check that everything went well.
            self._verifyAuthentication()

            # Notify the user.
            self._resetAuthenticationRequestedMessage()
            self._authentication_succeeded_message.show()
        elif data.get("message", "") == "unauthorized":
            Logger.log("i", "Authentication was denied.")
            self.setAuthenticationState(AuthState.AuthenticationDenied)
            self._authentication_failed_message.show()

    def _saveAuthentication(self) -> None:
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        if self._authentication_key is None:
            Logger.log("e", "Authentication key is None, nothing to save.")
            return
        if self._authentication_id is None:
            Logger.log("e", "Authentication id is None, nothing to save.")
            return
        if global_container_stack:
            global_container_stack.setMetaDataEntry("network_authentication_key", self._authentication_key)

            global_container_stack.setMetaDataEntry("network_authentication_id", self._authentication_id)

            # Force save so we are sure the data is not lost.
            CuraApplication.getInstance().saveStack(global_container_stack)
            Logger.log("i", "Authentication succeeded for id %s and key %s", self._authentication_id,
                       self._getSafeAuthKey())
        else:
            Logger.log("e", "Unable to save authentication for id %s and key %s", self._authentication_id,
                       self._getSafeAuthKey())

    def _onRequestAuthenticationFinished(self, reply):
        try:
            data = json.loads(bytes(reply.readAll()).decode("utf-8"))
        except json.decoder.JSONDecodeError:
            Logger.log("w", "Received an invalid authentication request reply from printer: Not valid JSON.")
            self.setAuthenticationState(AuthState.NotAuthenticated)
            return

        self.setAuthenticationState(AuthState.AuthenticationReceived)
        self._authentication_id = data["id"]
        self._authentication_key = data["key"]
        Logger.log("i", "Got a new authentication ID (%s) and KEY (%s). Waiting for authorization.",
                   self._authentication_id, self._getSafeAuthKey())

    def _requestAuthentication(self):
        self._authentication_requested_message.show()
        self._authentication_timer.start()

        # Reset any previous authentication info. If this isn't done, the "Retry" action on the failed message might
        # give issues.
        self._authentication_key = None
        self._authentication_id = None

        self.post("auth/request",
                  json.dumps({"application": "Cura-" + CuraApplication.getInstance().getVersion(),
                              "user": self._getUserName()}),
                  on_finished=self._onRequestAuthenticationFinished)

        self.setAuthenticationState(AuthState.AuthenticationRequested)

    def _onAuthenticationRequired(self, reply, authenticator):
        if self._authentication_id is not None and self._authentication_key is not None:
            Logger.log("d",
                       "Authentication was required for printer: %s. Setting up authenticator with ID %s and key %s",
                       self._id, self._authentication_id, self._getSafeAuthKey())
            authenticator.setUser(self._authentication_id)
            authenticator.setPassword(self._authentication_key)
        else:
            Logger.log("d", "No authentication is available to use for %s, but we did got a request for it.", self._id)

    def _onGetPrintJobFinished(self, reply):
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)

        if not self._printers:
            return  # Ignore the data for now, we don't have info about a printer yet.
        printer = self._printers[0]

        if status_code == 200:
            try:
                result = json.loads(bytes(reply.readAll()).decode("utf-8"))
            except json.decoder.JSONDecodeError:
                Logger.log("w", "Received an invalid print job state message: Not valid JSON.")
                return
            if printer.activePrintJob is None:
                print_job = PrintJobOutputModel(output_controller=self._output_controller)
                printer.updateActivePrintJob(print_job)
            else:
                print_job = printer.activePrintJob
            print_job.updateState(result["state"])
            print_job.updateTimeElapsed(result["time_elapsed"])
            print_job.updateTimeTotal(result["time_total"])
            print_job.updateName(result["name"])
        elif status_code == 404:
            # No job found, so delete the active print job (if any!)
            printer.updateActivePrintJob(None)
        else:
            Logger.log("w",
                       "Got status code {status_code} while trying to get printer data".format(status_code=status_code))

    def materialHotendChangedMessage(self, callback):
        CuraApplication.getInstance().messageBox(i18n_catalog.i18nc("@window:title", "Sync with your printer"),
                                             i18n_catalog.i18nc("@label",
                                                                "Would you like to use your current printer configuration in Cura?"),
                                             i18n_catalog.i18nc("@label",
                                                                "The PrintCores and/or materials on your printer differ from those within your current project. For the best result, always slice for the PrintCores and materials that are inserted in your printer."),
                                             buttons=QMessageBox.Yes + QMessageBox.No,
                                             icon=QMessageBox.Question,
                                             callback=callback
                                             )

    def _onGetPrinterDataFinished(self, reply):
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code == 200:
            try:
                result = json.loads(bytes(reply.readAll()).decode("utf-8"))
            except json.decoder.JSONDecodeError:
                Logger.log("w", "Received an invalid printer state message: Not valid JSON.")
                return

            if not self._printers:
                # Quickest way to get the firmware version is to grab it from the zeroconf.
                firmware_version = self._properties.get(b"firmware_version", b"").decode("utf-8")
                self._printers = [PrinterOutputModel(output_controller=self._output_controller, number_of_extruders=self._number_of_extruders, firmware_version=firmware_version)]
                self._printers[0].setCameraUrl(QUrl("http://" + self._address + ":8080/?action=stream"))
                for extruder in self._printers[0].extruders:
                    extruder.activeMaterialChanged.connect(self.materialIdChanged)
                    extruder.hotendIDChanged.connect(self.hotendIdChanged)
                self.printersChanged.emit()

            # LegacyUM3 always has a single printer.
            printer = self._printers[0]
            printer.updateBedTemperature(result["bed"]["temperature"]["current"])
            printer.updateTargetBedTemperature(result["bed"]["temperature"]["target"])
            printer.updateState(result["status"])

            try:
                # If we're still handling the request, we should ignore remote for a bit.
                if not printer.getController().isPreheatRequestInProgress():
                    printer.updateIsPreheating(result["bed"]["pre_heat"]["active"])
            except KeyError:
                # Older firmwares don't support preheating, so we need to fake it.
                pass

            head_position = result["heads"][0]["position"]
            printer.updateHeadPosition(head_position["x"], head_position["y"], head_position["z"])

            for index in range(0, self._number_of_extruders):
                temperatures = result["heads"][0]["extruders"][index]["hotend"]["temperature"]
                extruder = printer.extruders[index]
                extruder.updateTargetHotendTemperature(temperatures["target"])
                extruder.updateHotendTemperature(temperatures["current"])

                material_guid = result["heads"][0]["extruders"][index]["active_material"]["guid"]

                if extruder.activeMaterial is None or extruder.activeMaterial.guid != material_guid:
                    # Find matching material (as we need to set brand, type & color)
                    containers = ContainerRegistry.getInstance().findInstanceContainers(type="material",
                                                                                        GUID=material_guid)
                    if containers:
                        color = containers[0].getMetaDataEntry("color_code")
                        brand = containers[0].getMetaDataEntry("brand")
                        material_type = containers[0].getMetaDataEntry("material")
                        name = containers[0].getName()
                    else:
                        # Unknown material.
                        color = "#00000000"
                        brand = "Unknown"
                        material_type = "Unknown"
                        name = "Unknown"
                    material = MaterialOutputModel(guid=material_guid, type=material_type,
                                                   brand=brand, color=color, name = name)
                    extruder.updateActiveMaterial(material)

                try:
                    hotend_id = result["heads"][0]["extruders"][index]["hotend"]["id"]
                except KeyError:
                    hotend_id = ""
                printer.extruders[index].updateHotendID(hotend_id)

        else:
            Logger.log("w",
                       "Got status code {status_code} while trying to get printer data".format(status_code = status_code))

    ##  Convenience function to "blur" out all but the last 5 characters of the auth key.
    #   This can be used to debug print the key, without it compromising the security.
    def _getSafeAuthKey(self):
        if self._authentication_key is not None:
            result = self._authentication_key[-5:]
            result = "********" + result
            return result

        return self._authentication_key
