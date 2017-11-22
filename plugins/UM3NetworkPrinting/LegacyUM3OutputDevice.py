from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice, AuthState
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel
from cura.PrinterOutput.MaterialOutputModel import MaterialOutputModel

from UM.Logger import Logger
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Application import Application
from UM.i18n import i18nCatalog
from UM.Message import Message

from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtCore import QTimer

import json
import os  # To get the username

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
    def __init__(self, device_id, address: str, properties, parent = None):
        super().__init__(device_id = device_id, address = address, properties = properties, parent = parent)
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
        self._not_authenticated_message = None

    def _setupMessages(self):
        self._authentication_requested_message = Message(i18n_catalog.i18nc("@info:status",
                                                                            "Access to the printer requested. Please approve the request on the printer"),
                                                         lifetime=0, dismissable=False, progress=0,
                                                         title=i18n_catalog.i18nc("@info:title",
                                                                                  "Authentication status"))

        self._authentication_failed_message = Message(i18n_catalog.i18nc("@info:status", ""),
                                                      title=i18n_catalog.i18nc("@info:title", "Authentication Status"))
        self._authentication_failed_message.addAction("Retry", i18n_catalog.i18nc("@action:button", "Retry"), None,
                                                      i18n_catalog.i18nc("@info:tooltip", "Re-send the access request"))
        self._authentication_failed_message.actionTriggered.connect(self._requestAuthentication)
        self._authentication_succeeded_message = Message(
            i18n_catalog.i18nc("@info:status", "Access to the printer accepted"),
            title=i18n_catalog.i18nc("@info:title", "Authentication Status"))

        self._not_authenticated_message = Message(
            i18n_catalog.i18nc("@info:status", "No access to print with this printer. Unable to send print job."),
            title=i18n_catalog.i18nc("@info:title", "Authentication Status"))
        self._not_authenticated_message.addAction("Request", i18n_catalog.i18nc("@action:button", "Request Access"),
                                                  None, i18n_catalog.i18nc("@info:tooltip",
                                                                           "Send access request to the printer"))
        self._not_authenticated_message.actionTriggered.connect(self._requestAuthentication)

    def connect(self):
        super().connect()
        self._setupMessages()
        global_container = Application.getInstance().getGlobalContainerStack()
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

        self._authentication_timer.stop()

    ##  Send all material profiles to the printer.
    def sendMaterialProfiles(self):
        # TODO
        pass

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
        self._get("printer", onFinished=self._onGetPrinterDataFinished)
        self._get("print_job", onFinished=self._onGetPrintJobFinished)

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
            Logger.log("i", "Authentication timer ended. Setting authentication to denied for printer: %s" % self._key)
            self.setAuthenticationState(AuthState.AuthenticationDenied)
            self._resetAuthenticationRequestedMessage()
            self._authentication_failed_message.show()

    def _verifyAuthentication(self):
        Logger.log("d", "Attempting to verify authentication")
        # This will ensure that the "_onAuthenticationRequired" is triggered, which will setup the authenticator.
        self._get("auth/verify", onFinished=self._onVerifyAuthenticationCompleted)

    def _onVerifyAuthenticationCompleted(self, reply):
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code == 401:
            # Something went wrong; We somehow tried to verify authentication without having one.
            Logger.log("d", "Attempted to verify auth without having one.")
            self._authentication_id = None
            self._authentication_key = None
            self.setAuthenticationState(AuthState.NotAuthenticated)
        elif status_code == 403:
            Logger.log("d",
                       "While trying to verify the authentication state, we got a forbidden response. Our own auth state was %s",
                       self._authentication_state)
            self.setAuthenticationState(AuthState.AuthenticationDenied)
            self._authentication_failed_message.show()
        elif status_code == 200:
            self.setAuthenticationState(AuthState.Authenticated)
            # Now we know for sure that we are authenticated, send the material profiles to the machine.
            self.sendMaterialProfiles()

    def _checkAuthentication(self):
        Logger.log("d", "Checking if authentication is correct for id %s and key %s", self._authentication_id, self._getSafeAuthKey())
        self._get("auth/check/" + str(self._authentication_id), onFinished=self._onCheckAuthenticationFinished)

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

    def _saveAuthentication(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            if "network_authentication_key" in global_container_stack.getMetaData():
                global_container_stack.setMetaDataEntry("network_authentication_key", self._authentication_key)
            else:
                global_container_stack.addMetaDataEntry("network_authentication_key", self._authentication_key)

            if "network_authentication_id" in global_container_stack.getMetaData():
                global_container_stack.setMetaDataEntry("network_authentication_id", self._authentication_id)
            else:
                global_container_stack.addMetaDataEntry("network_authentication_id", self._authentication_id)

            # Force save so we are sure the data is not lost.
            Application.getInstance().saveStack(global_container_stack)
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

        self._post("auth/request",
                   json.dumps({"application":  "Cura-" + Application.getInstance().getVersion(),
                                               "user": self._getUserName()}).encode(),
                   onFinished=self._onRequestAuthenticationFinished)

        self.setAuthenticationState(AuthState.AuthenticationRequested)

    def _onAuthenticationRequired(self, reply, authenticator):
        if self._authentication_id is not None and self._authentication_key is not None:
            Logger.log("d",
                       "Authentication was required for printer: %s. Setting up authenticator with ID %s and key %s",
                       self._id, self._authentication_id, self._getSafeAuthKey())
            authenticator.setUser(self._authentication_id)
            authenticator.setPassword(self._authentication_key)
        else:
            Logger.log("d", "No authentication is available to use for %s, but we did got a request for it.", self._key)

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
                print_job = PrintJobOutputModel(output_controller=None)
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

    def _onGetPrinterDataFinished(self, reply):
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code == 200:
            try:
                result = json.loads(bytes(reply.readAll()).decode("utf-8"))
            except json.decoder.JSONDecodeError:
                Logger.log("w", "Received an invalid printer state message: Not valid JSON.")
                return

            if not self._printers:
                self._printers = [PrinterOutputModel(output_controller=None, number_of_extruders=self._number_of_extruders)]

            # LegacyUM3 always has a single printer.
            printer = self._printers[0]
            printer.updateBedTemperature(result["bed"]["temperature"]["current"])
            printer.updateTargetBedTemperature(result["bed"]["temperature"]["target"])
            printer.updatePrinterState(result["status"])

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
                    else:
                        # Unknown material.
                        color = "#00000000"
                        brand = "Unknown"
                        material_type = "Unknown"
                    material = MaterialOutputModel(guid=material_guid, type=material_type,
                                                   brand=brand, color=color)
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

    ##  Convenience function to get the username from the OS.
    #   The code was copied from the getpass module, as we try to use as little dependencies as possible.
    def _getUserName(self):
        for name in ("LOGNAME", "USER", "LNAME", "USERNAME"):
            user = os.environ.get(name)
            if user:
                return user
        return "Unknown User"  # Couldn't find out username.