from UM.i18n import i18nCatalog
from UM.Application import Application
from UM.Logger import Logger
from UM.Signal import signalemitter

from UM.Message import Message

from cura.PrinterOutputDevice import PrinterOutputDevice, ConnectionState

from PyQt5.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkRequest, QNetworkAccessManager
from PyQt5.QtCore import QUrl, QTimer, pyqtSignal, pyqtProperty, pyqtSlot
from PyQt5.QtGui import QImage

import json
import os

i18n_catalog = i18nCatalog("cura")

from enum import IntEnum

class AuthState(IntEnum):
    NotAuthenticated = 1
    AuthenticationRequested = 2
    Authenticated = 3
    AuthenticationDenied = 4

##  Network connected (wifi / lan) printer that uses the Ultimaker API
@signalemitter
class NetworkPrinterOutputDevice(PrinterOutputDevice):
    def __init__(self, key, address, properties):
        super().__init__(key)
        self._address = address
        self._key = key
        self._properties = properties  # Properties dict as provided by zero conf

        self._gcode = None

        #   This holds the full JSON file that was received from the last request.
        self._json_printer_state = None

        ##  Todo: Hardcoded value now; we should probably read this from the machine file.
        ##  It's okay to leave this for now, as this plugin is um3 only (and has 2 extruders by definition)
        self._num_extruders = 2

        self._hotend_temperatures = [0] * self._num_extruders
        self._target_hotend_temperatures = [0] * self._num_extruders

        self._api_version = "1"
        self._api_prefix = "/api/v" + self._api_version + "/"
        self.setName(key)
        self.setShortDescription(i18n_catalog.i18nc("@action:button", "Print with WIFI"))
        self.setDescription(i18n_catalog.i18nc("@properties:tooltip", "Print with WIFI"))
        self.setIconName("print")

        #   QNetwork manager needs to be created in advance. If we don't it can happen that it doesn't correctly
        #   hook itself into the event loop, which results in events never being fired / done.
        self._manager = QNetworkAccessManager()
        self._manager.finished.connect(self._onFinished)
        self._manager.authenticationRequired.connect(self._onAuthenticationRequired)

        self._post_request = None
        self._post_reply = None
        self._post_multi_part = None
        self._post_part = None

        self._progress_message = None
        self._error_message = None

        self._update_timer = QTimer()
        self._update_timer.setInterval(2000)  # TODO; Add preference for update interval
        self._update_timer.setSingleShot(False)
        self._update_timer.timeout.connect(self._update)

        self._camera_timer = QTimer()
        self._camera_timer.setInterval(2000)  # Todo: Add preference for camera update interval
        self._camera_timer.setSingleShot(False)
        self._camera_timer.timeout.connect(self._update_camera)

        self._camera_image_id = 0

        self._authentication_counter = 0
        self._max_authentication_counter = 5 * 60  # Number of attempts before authentication timed out (5 min)

        self._authentication_timer = QTimer()
        self._authentication_timer.setInterval(1000)  # TODO; Add preference for update interval
        self._authentication_timer.setSingleShot(False)
        self._authentication_timer.timeout.connect(self._onAuthenticationTimer)

        self._authentication_state = AuthState.NotAuthenticated
        self._authentication_id = None
        self._authentication_key = None

        self._authentication_requested_message = Message(i18n_catalog.i18nc("@info:status", "Requested access. Please aprove the request on the printer"), lifetime = 0, dismissable = False, progress = 0)
        self._camera_image = QImage()

    def _onAuthenticationTimer(self):
        self._authentication_counter += 1
        self._authentication_requested_message.setProgress(self._authentication_counter / self._max_authentication_counter * 100)
        if self._authentication_counter > self._max_authentication_counter:
            self._authentication_timer.stop()
            self.setAuthenticationState(AuthState.AuthenticationDenied)

    def _onAuthenticationRequired(self, reply, authenticator):
        if self._authentication_id is not None and self._authentication_key is not None:
            authenticator.setUser(self._authentication_id)
            authenticator.setPassword(self._authentication_key)

    def getProperties(self):
        return self._properties

    ##  Get the unique key of this machine
    #   \return key String containing the key of the machine.
    @pyqtSlot(result = str)
    def getKey(self):
        return self._key

    ##  Name of the printer (as returned from the zeroConf properties)
    @pyqtProperty(str, constant = True)
    def name(self):
        return self._properties.get(b"name", b"").decode("utf-8")

    ##  Firmware version (as returned from the zeroConf properties)
    @pyqtProperty(str, constant=True)
    def firmwareVersion(self):
        return self._properties.get(b"firmware_version", b"").decode("utf-8")

    ## IPadress of this printer
    @pyqtProperty(str, constant=True)
    def ipAddress(self):
        return self._address

    def _update_camera(self):
        ## Request new image
        url = QUrl("http://" + self._address + ":8080/?action=snapshot")
        image_request = QNetworkRequest(url)
        self._manager.get(image_request)

    ##  Set the authentication state.
    #   \param auth_state \type{AuthState} Enum value representing the new auth state
    def setAuthenticationState(self, auth_state):
        if auth_state == AuthState.AuthenticationRequested:
            self._authentication_requested_message.show()
            self._authentication_timer.start()  # Start timer so auth will fail after a while.
        elif auth_state == AuthState.Authenticated:
            self._authentication_requested_message.hide()
            authentication_succeeded_message = Message(i18n_catalog.i18nc("@info:status", "Printer was successfully paired with Cura"))
            authentication_succeeded_message.show()
        elif auth_state == AuthState.AuthenticationDenied:
            self._authentication_requested_message.hide()
            authentication_failed_message = Message(i18n_catalog.i18nc("@info:status", "Pairing request failed. This can be either due to a timeout or the printer refused the request."))
            authentication_failed_message.show()
        self._authentication_state = auth_state

    ##  Request data from the connected device.
    def _update(self):
        if self._authentication_state == AuthState.NotAuthenticated:
            self._verifyAuthentication() # We don't know if we are authenticated; check if we have correct auth.
        elif self._authentication_state == AuthState.AuthenticationRequested:
            self._checkAuthentication() # We requested authentication at some point. Check if we got permission.
        ## Request 'general' printer data
        url = QUrl("http://" + self._address + self._api_prefix + "printer")
        printer_request = QNetworkRequest(url)
        self._manager.get(printer_request)

        ## Request print_job data
        url = QUrl("http://" + self._address + self._api_prefix + "print_job")
        print_job_request = QNetworkRequest(url)
        self._manager.get(print_job_request)

    ##  Convenience function that gets information from the received json data and converts it to the right internal
    #   values / variables
    def _spliceJSONData(self):
        # Check for hotend temperatures
        for index in range(0, self._num_extruders):
            temperature = self._json_printer_state["heads"][0]["extruders"][index]["hotend"]["temperature"]["current"]
            self._setHotendTemperature(index, temperature)

        bed_temperature = self._json_printer_state["bed"]["temperature"]["current"]
        self._setBedTemperature(bed_temperature)

        head_x = self._json_printer_state["heads"][0]["position"]["x"]
        head_y = self._json_printer_state["heads"][0]["position"]["y"]
        head_z = self._json_printer_state["heads"][0]["position"]["z"]
        self._updateHeadPosition(head_x, head_y, head_z)

    def close(self):
        self.setConnectionState(ConnectionState.closed)
        self._progress_message.hide()
        self._authentication_requested_message.hide()
        self._error_message.hide()
        self._authentication_counter = 0
        self._authentication_timer.stop()
        self._update_timer.stop()
        self._camera_timer.stop()

    def requestWrite(self, node, file_name = None, filter_by_machine = False):
        self._gcode = getattr(Application.getInstance().getController().getScene(), "gcode_list")

        # TODO: Implement all checks.
        # Check if cartridges are loaded at all (Error)
        #self._json_printer_state["heads"][0]["extruders"][0]["hotend"]["id"] != ""

        # Check if there is material loaded at all (Error)self.authentication_requested_message.setProgress(self._authentication_counter / self._max_authentication_counter)
        #self._json_printer_state["heads"][0]["extruders"][0]["active_material"]["GUID"] != ""

        # Check if there is enough material (Warning)
        #self._json_printer_state["heads"][0]["extruders"][0]["active_material"]["length_remaining"]

        #TODO: Check if the cartridge is the right ID (give warning otherwise)

        self.startPrint()

    def isConnected(self):
        return self._connection_state != ConnectionState.closed and self._connection_state != ConnectionState.error

    ##  Start requesting data from printer
    def connect(self):
        self.setConnectionState(ConnectionState.connecting)
        self._update()  # Manually trigger the first update, as we don't want to wait a few secs before it starts.
        self._update_camera()
        Logger.log("d", "Connection with printer %s with ip %s started", self._key, self._address)

        ## Check if this machine was authenticated before.
        self._authentication_id = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("network_authentication_id", None)
        self._authentication_key = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("network_authentication_key", None)

        self._update_timer.start()
        self._camera_timer.start()

    newImage = pyqtSignal()

    @pyqtProperty(QUrl, notify = newImage)
    def cameraImage(self):
        self._camera_image_id += 1
        temp = "image://camera/" + str(self._camera_image_id)
        return QUrl(temp, QUrl.TolerantMode)

    def getCameraImage(self):
        return self._camera_image

    def _setJobState(self, job_state):
        url = QUrl("http://" + self._address + self._api_prefix + "print_job/state")
        put_request = QNetworkRequest(url)
        put_request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        data = "{\"target\": \"%s\"}" % job_state
        self._manager.put(put_request, data.encode())

    ##  Convenience function to get the username from the OS.
    #   The code was copied from the getpass module, as we try to use as little dependencies as possible.
    def _getUserName(self):
        for name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):
            user = os.environ.get(name)
            if user:
                return user
        return "Unknown User"  # Couldn't find out username.

    ##  Attempt to start a new print.
    #   This function can fail to actually start a print due to not being authenticated or another print already
    #   being in progress.
    def startPrint(self):
        if self._progress != 0:
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Printer is still printing. Unable to start a new job."))
            self._error_message.show()
            return
        elif self._authentication_state != AuthState.Authenticated:
            self._not_authenticated_message = Message(i18n_catalog.i18nc("@info:status",
                                                                         "Not authenticated to print with this machine. Unable to start a new job."))
            self._not_authenticated_message.show()
            return
        try:
            self._progress_message = Message(i18n_catalog.i18nc("@info:status", "Sending data to printer"), 0, False, -1)
            self._progress_message.show()

            ## Mash the data into single string
            single_string_file_data = ""
            for line in self._gcode:
                single_string_file_data += line

            ##  TODO: Use correct file name (we use placeholder now)
            file_name = "test.gcode"

            ##  Create multi_part request
            self._post_multi_part = QHttpMultiPart(QHttpMultiPart.FormDataType)

            ##  Create part (to be placed inside multipart)
            self._post_part = QHttpPart()
            self._post_part.setHeader(QNetworkRequest.ContentDispositionHeader,
                           "form-data; name=\"file\"; filename=\"%s\"" % file_name)
            self._post_part.setBody(single_string_file_data.encode())
            self._post_multi_part.append(self._post_part)

            url = QUrl("http://" + self._address + self._api_prefix + "print_job")

            ##  Create the QT request
            self._post_request = QNetworkRequest(url)

            ##  Post request + data
            self._post_reply = self._manager.post(self._post_request, self._post_multi_part)
            self._post_reply.uploadProgress.connect(self._onUploadProgress)

        except IOError:
            self._progress_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Unable to send data to printer. Is another job still active?"))
            self._error_message.show()
        except Exception as e:
            self._progress_message.hide()
            Logger.log("e", "An exception occurred in network connection: %s" % str(e))

    ##  Verify if we are authenticated to make requests.
    def _verifyAuthentication(self):
        url = QUrl("http://" + self._address + self._api_prefix + "auth/verify")
        request = QNetworkRequest(url)
        self._manager.get(request)

    ##  Check if the authentication request was allowed by the printer.
    def _checkAuthentication(self):
        self._manager.get(QNetworkRequest(QUrl("http://" + self._address + self._api_prefix + "auth/check/" + str(self._authentication_id))))

    ##  Request a authentication key from the printer so we can be authenticated
    def _requestAuthentication(self):
        url = QUrl("http://" + self._address + self._api_prefix + "auth/request")
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        self.setAuthenticationState(AuthState.AuthenticationRequested)
        self._manager.post(request, json.dumps({"application": "Cura-" + Application.getInstance().getVersion(), "user": self._getUserName()}).encode())

    ##  Handler for all requests that have finished.
    def _onFinished(self, reply):
        if reply.operation() == QNetworkAccessManager.GetOperation:
            if "printer" in reply.url().toString():  # Status update from printer.
                if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) == 200:
                    if self._connection_state == ConnectionState.connecting:
                        self.setConnectionState(ConnectionState.connected)
                    self._json_printer_state = json.loads(bytes(reply.readAll()).decode("utf-8"))

                    self._spliceJSONData()
                else:
                    pass  # TODO: Handle errors
            elif "print_job" in reply.url().toString():  # Status update from print_job:
                if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) == 200:
                    json_data = json.loads(bytes(reply.readAll()).decode("utf-8"))
                    progress = json_data["progress"]
                    ## If progress is 0 add a bit so another print can't be sent.
                    if progress == 0:
                        progress += 0.001
                    self.setProgress(progress * 100)
                    self._updateJobState(json_data["state"])
                    self.setTimeElapsed(json_data["time_elapsed"])
                    self.setTimeTotal(json_data["time_total"])
                    self.setJobName(json_data["name"])
                elif reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) == 404:
                    self.setProgress(0)  # No print job found, so there can't be progress!
                    self._updateJobState("")
            elif "snapshot" in reply.url().toString():  # Status update from image:
                if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) == 200:
                    self._camera_image.loadFromData(reply.readAll())
                    self.newImage.emit()
            elif "auth/verify" in reply.url().toString():  # Answer when requesting authentication
                if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) == 401:
                    if self._authentication_state != AuthState.AuthenticationRequested:
                        # Only request a new authentication when we have not already done so.
                        Logger.log("i", "Not authenticated. Attempting to request authentication")
                        self._requestAuthentication()
                elif reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) == 403:
                    pass
                else:
                    self.setAuthenticationState(AuthState.Authenticated)
                    global_container_stack = Application.getInstance().getGlobalContainerStack()
                    ## Save authentication details.
                    if global_container_stack:
                        if "network_authentication_key" in global_container_stack.getMetaData():
                            global_container_stack.setMetaDataEntry("network_authentication_key", self._authentication_key)
                        else:
                            global_container_stack.addMetaDataEntry("network_authentication_key", self._authentication_key)
                        if "network_authentication_id" in global_container_stack.getMetaData():
                            global_container_stack.setMetaDataEntry("network_authentication_id", self._authentication_id)
                        else:
                            global_container_stack.addMetaDataEntry("network_authentication_id", self._authentication_id)
                    Logger.log("i", "Authentication succeeded")
            elif "auth/check" in reply.url().toString():  # Check if we are authenticated (user can refuse this!)
                data = json.loads(bytes(reply.readAll()).decode("utf-8"))
                if data.get("message", "") == "authorized":
                    Logger.log("i", "Authentication was approved")
                    self._verifyAuthentication()  # Ensure that the verification is really used and correct.
                elif data.get("message", "") == "unauthorized":
                    Logger.log("i", "Authentication was denied.")
                    self.setAuthenticationState(AuthState.AuthenticationDenied)
                else:
                    pass

        elif reply.operation() == QNetworkAccessManager.PostOperation:
            if "/auth/request" in reply.url().toString():
                # We got a response to requesting authentication.
                data = json.loads(bytes(reply.readAll()).decode("utf-8"))
                self._authentication_key = data["key"]
                self._authentication_id = data["id"]
                Logger.log("i", "Got a new authentication ID. Waiting for authorization: %s", self._authentication_id )

                # Check if the authentication is accepted.
                self._checkAuthentication()
            else:
                reply.uploadProgress.disconnect(self._onUploadProgress)
                self._progress_message.hide()
        elif reply.operation() == QNetworkAccessManager.PutOperation:
            if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) == 204:
                pass  # Request was sucesfull!
            else:
                Logger.log("d", "Something went wrong when trying to update data of API (%s). Message: %s Statuscode: %s", reply.url().toString(), reply.readAll(), reply.attribute(QNetworkRequest.HttpStatusCodeAttribute))
        else:
            Logger.log("d", "NetworkPrinterOutputDevice got an unhandled operation %s", reply.operation())

    def _onUploadProgress(self, bytes_sent, bytes_total):
        if bytes_total > 0:
            self._progress_message.setProgress(bytes_sent / bytes_total * 100)
        else:
            self._progress_message.setProgress(0)