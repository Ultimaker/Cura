from UM.i18n import i18nCatalog
from UM.Application import Application
from UM.Logger import Logger
from UM.Signal import signalemitter

from UM.Message import Message

import UM.Settings

from cura.PrinterOutputDevice import PrinterOutputDevice, ConnectionState

from PyQt5.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkRequest, QNetworkAccessManager, QNetworkReply
from PyQt5.QtCore import QUrl, QTimer, pyqtSignal, pyqtProperty, pyqtSlot
from PyQt5.QtGui import QImage

import json
import os

from time import time

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
        self._print_finished = True # _print_finsihed == False means we're halfway in a print

        # This holds the full JSON file that was received from the last request.
        # The JSON looks like:
        # {'led': {'saturation': 0.0, 'brightness': 100.0, 'hue': 0.0},
        # 'beep': {}, 'network': {'wifi_networks': [],
        # 'ethernet': {'connected': True, 'enabled': True},
        # 'wifi': {'ssid': 'xxxx', 'connected': False, 'enabled': False}},
        # 'diagnostics': {},
        # 'bed': {'temperature': {'target': 60.0, 'current': 44.4}},
        # 'heads': [{'max_speed': {'z': 40.0, 'y': 300.0, 'x': 300.0},
        # 'position': {'z': 20.0, 'y': 6.0, 'x': 180.0},
        # 'fan': 0.0,
        # 'jerk': {'z': 0.4, 'y': 20.0, 'x': 20.0},
        # 'extruders': [
        # {'feeder': {'max_speed': 45.0, 'jerk': 5.0, 'acceleration': 3000.0},
        # 'active_material': {'GUID': 'xxxxxxx', 'length_remaining': -1.0},
        # 'hotend': {'temperature': {'target': 0.0, 'current': 22.8}, 'id': 'AA 0.4'}},
        # {'feeder': {'max_speed': 45.0, 'jerk': 5.0, 'acceleration': 3000.0},
        # 'active_material': {'GUID': 'xxxx', 'length_remaining': -1.0},
        # 'hotend': {'temperature': {'target': 0.0, 'current': 22.8}, 'id': 'BB 0.4'}}],
        # 'acceleration': 3000.0}],
        # 'status': 'printing'}
        self._json_printer_state = {}

        ##  Todo: Hardcoded value now; we should probably read this from the machine file.
        ##  It's okay to leave this for now, as this plugin is um3 only (and has 2 extruders by definition)
        self._num_extruders = 2

        # These are reinitialised here (from PrinterOutputDevice) to match the new _num_extruders
        self._hotend_temperatures = [0] * self._num_extruders
        self._target_hotend_temperatures = [0] * self._num_extruders

        self._material_ids = [""] * self._num_extruders
        self._hotend_ids = [""] * self._num_extruders

        self._api_version = "1"
        self._api_prefix = "/api/v" + self._api_version + "/"
        self.setPriority(2) # Make sure the output device gets selected above local file output
        self.setName(key)
        self.setShortDescription(i18n_catalog.i18nc("@action:button", "Print over network"))
        self.setDescription(i18n_catalog.i18nc("@properties:tooltip", "Print over network"))
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

        self._material_multi_part = None
        self._material_part = None

        self._progress_message = None
        self._error_message = None
        self._connection_message = None

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

        self._material_post_objects = {}
        self._connection_state_before_timeout = None

        self._last_response_time = time()
        self._response_timeout_time = 5
        self._not_authenticated_message = None

    def _onAuthenticationTimer(self):
        self._authentication_counter += 1
        self._authentication_requested_message.setProgress(self._authentication_counter / self._max_authentication_counter * 100)
        if self._authentication_counter > self._max_authentication_counter:
            self._authentication_timer.stop()
            Logger.log("i", "Authentication timer ended. Setting authentication to denied")
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
            self.setAcceptsCommands(False)
            self._authentication_requested_message.show()
            self._authentication_timer.start()  # Start timer so auth will fail after a while.
        elif auth_state == AuthState.Authenticated:
            self.setAcceptsCommands(True)
            self._authentication_requested_message.hide()
            authentication_succeeded_message = Message(i18n_catalog.i18nc("@info:status", "Printer was successfully paired with Cura"))
            authentication_succeeded_message.show()

            # Stop waiting for a response
            self._authentication_timer.stop()
            self._authentication_counter = 0

            # Once we are authenticated we need to send all material profiles.
            self.sendMaterialProfiles()
        elif auth_state == AuthState.AuthenticationDenied:
            self.setAcceptsCommands(False)
            self._authentication_requested_message.hide()
            authentication_failed_message = Message(i18n_catalog.i18nc("@info:status", "Pairing request failed. This can be either due to a timeout or the printer refused the request."))
            authentication_failed_message.show()

            # Stop waiting for a response
            self._authentication_timer.stop()
            self._authentication_counter = 0

        self._authentication_state = auth_state

    ##  Request data from the connected device.
    def _update(self):
        # Check that we aren't in a timeout state
        if self._last_response_time and not self._connection_state_before_timeout:
            if time() - self._last_response_time > self._response_timeout_time:
                # Go into timeout state.
                Logger.log("d", "We did not receive a response for %0.1f seconds, so it seems the printer is no longer accessible.", time() - self._last_response_time)
                self._connection_state_before_timeout = self._connection_state
                self._connection_message = Message(i18n_catalog.i18nc("@info:status", "The connection with the printer was lost. Check your network-connections."))
                self._connection_message.show()
                self.setConnectionState(ConnectionState.error)

        if self._authentication_state == AuthState.NotAuthenticated:
            self._verifyAuthentication()  # We don't know if we are authenticated; check if we have correct auth.
        elif self._authentication_state == AuthState.AuthenticationRequested:
            self._checkAuthentication()  # We requested authentication at some point. Check if we got permission.

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
            try:
                material_id = self._json_printer_state["heads"][0]["extruders"][index]["active_material"]["GUID"]
            except KeyError:
                material_id = ""
            self._setMaterialId(index, material_id)
            try:
                hotend_id = self._json_printer_state["heads"][0]["extruders"][index]["hotend"]["id"]
            except KeyError:
                hotend_id = ""
            self._setHotendId(index, hotend_id)

        bed_temperature = self._json_printer_state["bed"]["temperature"]["current"]
        self._setBedTemperature(bed_temperature)

        head_x = self._json_printer_state["heads"][0]["position"]["x"]
        head_y = self._json_printer_state["heads"][0]["position"]["y"]
        head_z = self._json_printer_state["heads"][0]["position"]["z"]
        self._updateHeadPosition(head_x, head_y, head_z)

    def close(self):
        self._updateJobState("")
        self.setConnectionState(ConnectionState.closed)
        if self._progress_message:
            self._progress_message.hide()

        # Reset authentication state
        self._authentication_requested_message.hide()
        self._authentication_state = AuthState.NotAuthenticated
        self._authentication_counter = 0
        self._authentication_timer.stop()

        if self._error_message:
            self._error_message.hide()

        # Reset timeout state
        self._connection_state_before_timeout = None
        self._last_response_time = time()

        # Stop update timers
        self._update_timer.stop()
        self._camera_timer.stop()

    def requestWrite(self, node, file_name = None, filter_by_machine = False):
        if self._progress != 0:
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Printer is still printing. Unable to start a new job."))
            self._error_message.show()
            return
        if self._json_printer_state["status"] != "idle":
            self._error_message = Message(
                i18n_catalog.i18nc("@info:status", "Unable to start a new print job, printer is not idle. Current printer status is %s.") % self._json_printer_state["status"])
            self._error_message.show()
            return
        elif self._authentication_state != AuthState.Authenticated:
            self._not_authenticated_message = Message(i18n_catalog.i18nc("@info:status",
                                                                         "Not authenticated to print with this machine. Unable to start a new job."))
            self._not_authenticated_message.show()
            return

        Application.getInstance().showPrintMonitor.emit(True)
        self._print_finished = True
        self._gcode = getattr(Application.getInstance().getController().getScene(), "gcode_list")

        # TODO: Implement all checks.
        # Check if cartridges are loaded at all (Error)
        #self._json_printer_state["heads"][0]["extruders"][0]["hotend"]["id"] != ""

        # Check if there is material loaded at all (Error)
        #self._json_printer_state["heads"][0]["extruders"][0]["active_material"]["GUID"] != ""

        # Check if there is enough material (Warning)
        #self._json_printer_state["heads"][0]["extruders"][0]["active_material"]["length_remaining"]

        #TODO: Check if the cartridge is the right ID (give warning otherwise)

        self.startPrint()

    def isConnected(self):
        return self._connection_state != ConnectionState.closed and self._connection_state != ConnectionState.error

    ##  Start requesting data from printer
    def connect(self):
        self.close()  # Ensure that previous connection (if any) is killed.
        self.setConnectionState(ConnectionState.connecting)
        self._update()  # Manually trigger the first update, as we don't want to wait a few secs before it starts.
        self._update_camera()
        Logger.log("d", "Connection with printer %s with ip %s started", self._key, self._address)

        ## Check if this machine was authenticated before.
        self._authentication_id = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("network_authentication_id", None)
        self._authentication_key = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("network_authentication_key", None)

        self._update_timer.start()
        self._camera_timer.start()

    ##  Stop requesting data from printer
    def disconnect(self):
        Logger.log("d", "Connection with printer %s with ip %s stopped", self._key, self._address)
        self.close()

    newImage = pyqtSignal()

    @pyqtProperty(QUrl, notify = newImage)
    def cameraImage(self):
        self._camera_image_id += 1
        # There is an image provider that is called "camera". In order to ensure that the image qml object, that
        # requires a QUrl to function, updates correctly we add an increasing number. This causes to see the QUrl
        # as new (instead of relying on cached version and thus forces an update.
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
        for name in ("LOGNAME", "USER", "LNAME", "USERNAME"):
            user = os.environ.get(name)
            if user:
                return user
        return "Unknown User"  # Couldn't find out username.

    ##  Attempt to start a new print.
    #   This function can fail to actually start a print due to not being authenticated or another print already
    #   being in progress.
    def startPrint(self):
        try:
            self._progress_message = Message(i18n_catalog.i18nc("@info:status", "Sending data to printer"), 0, False, -1)
            self._progress_message.show()

            ## Mash the data into single string
            single_string_file_data = ""
            for line in self._gcode:
                single_string_file_data += line

            file_name = "%s.gcode" % Application.getInstance().getPrintInformation().jobName

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

    ##  Send all material profiles to the printer.
    def sendMaterialProfiles(self):
        for container in UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(type = "material"):
            try:
                xml_data = container.serialize()
                if xml_data == "":
                    continue
                material_multi_part = QHttpMultiPart(QHttpMultiPart.FormDataType)

                material_part = QHttpPart()
                file_name = "none.xml"
                material_part.setHeader(QNetworkRequest.ContentDispositionHeader, "form-data; name=\"file\";filename=\"%s\"" % file_name)
                material_part.setBody(xml_data.encode())
                material_multi_part.append(material_part)
                url = QUrl("http://" + self._address + self._api_prefix + "materials")
                material_post_request = QNetworkRequest(url)
                reply = self._manager.post(material_post_request, material_multi_part)

                # Keep reference to material_part, material_multi_part and reply so the garbage collector won't touch them.
                self._material_post_objects[id(reply)] = (material_part, material_multi_part, reply)
            except NotImplementedError:
                # If the material container is not the most "generic" one it can't be serialized an will raise a
                # NotImplementedError. We can simply ignore these.
                pass

    ##  Handler for all requests that have finished.
    def _onFinished(self, reply):
        if reply.error() == QNetworkReply.TimeoutError:
            Logger.log("w", "Received a timeout on a request to the printer")
            self._connection_state_before_timeout = self._connection_state
            self.setConnectionState(ConnectionState.error)
            return

        if self._connection_state_before_timeout and reply.error() == QNetworkReply.NoError:  # There was a timeout, but we got a correct answer again.
            Logger.log("d", "We got a response from the server after %0.1f of silence", time() - self._last_response_time)
            self.setConnectionState(self._connection_state_before_timeout)
            self._connection_state_before_timeout = None

        if reply.error() == QNetworkReply.NoError:
            self._last_response_time = time()

        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if not status_code:
            # Received no or empty reply
            return
        reply_url = reply.url().toString()

        if reply.operation() == QNetworkAccessManager.GetOperation:
            if "printer" in reply_url:  # Status update from printer.
                if status_code == 200:
                    if self._connection_state == ConnectionState.connecting:
                        self.setConnectionState(ConnectionState.connected)
                    self._json_printer_state = json.loads(bytes(reply.readAll()).decode("utf-8"))
                    self._spliceJSONData()

                    # Hide connection error message if the connection was restored
                    if self._connection_message:
                        self._connection_message.hide()
                        self._connection_message = None
                else:
                    Logger.log("w", "We got an unexpected status (%s) while requesting printer state", status_code)
                    pass  # TODO: Handle errors
            elif "print_job" in reply_url:  # Status update from print_job:
                if status_code == 200:
                    json_data = json.loads(bytes(reply.readAll()).decode("utf-8"))
                    progress = json_data["progress"]
                    ## If progress is 0 add a bit so another print can't be sent.
                    if progress == 0:
                        progress += 0.001
                    elif progress == 1:
                        self._print_finished = True
                    else:
                        self._print_finished = False
                    self.setProgress(progress * 100)

                    state = json_data["state"]

                    # There is a short period after aborting or finishing a print where the printer
                    # reports a "none" state (but the printer is not ready to receive a print)
                    # If this happens before the print has reached progress == 1, the print has
                    # been aborted.
                    if state == "none" or state == "":
                        if self._print_finished:
                            state = "printing"
                        else:
                            self.setErrorText(i18n_catalog.i18nc("@label:MonitorStatus", "Aborting print..."))
                            state = "error"
                    if state == "wait_cleanup" and not self._print_finished:
                        # Keep showing the "aborted" error state until after the buildplate has been cleaned
                        self.setErrorText(i18n_catalog.i18nc("@label:MonitorStatus", "Print aborted. Please check the printer"))
                        state = "error"

                    self._updateJobState(state)
                    self.setTimeElapsed(json_data["time_elapsed"])
                    self.setTimeTotal(json_data["time_total"])
                    self.setJobName(json_data["name"])
                elif status_code == 404:
                    self.setProgress(0)  # No print job found, so there can't be progress or other data.
                    self._updateJobState("")
                    self.setErrorText("")
                    self.setTimeElapsed(0)
                    self.setTimeTotal(0)
                    self.setJobName("")
                else:
                    Logger.log("w", "We got an unexpected status (%s) while requesting print job state", status_code)
            elif "snapshot" in reply_url:  # Status update from image:
                if status_code == 200:
                    self._camera_image.loadFromData(reply.readAll())
                    self.newImage.emit()
            elif "auth/verify" in reply_url:  # Answer when requesting authentication
                if status_code == 401:
                    if self._authentication_state != AuthState.AuthenticationRequested:
                        # Only request a new authentication when we have not already done so.
                        Logger.log("i", "Not authenticated. Attempting to request authentication")
                        self._requestAuthentication()
                elif status_code == 403:
                    pass
                elif status_code == 200:
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
                else:  # Got a response that we didn't expect, so something went wrong.
                    Logger.log("w", "While trying to authenticate, we got an unexpected response: %s", reply.attribute(QNetworkRequest.HttpStatusCodeAttribute))
                    self.setAuthenticationState(AuthState.NotAuthenticated)

            elif "auth/check" in reply_url:  # Check if we are authenticated (user can refuse this!)
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
            if "/auth/request" in reply_url:
                # We got a response to requesting authentication.
                data = json.loads(bytes(reply.readAll()).decode("utf-8"))
                self._authentication_key = data["key"]
                self._authentication_id = data["id"]
                Logger.log("i", "Got a new authentication ID. Waiting for authorization: %s", self._authentication_id )

                # Check if the authentication is accepted.
                self._checkAuthentication()
            elif "materials" in reply_url:
                # Remove cached post request items.
                del self._material_post_objects[id(reply)]
            elif "print_job" in reply_url:
                reply.uploadProgress.disconnect(self._onUploadProgress)
                self._progress_message.hide()

        elif reply.operation() == QNetworkAccessManager.PutOperation:
            if status_code == 204:
                pass  # Request was successful!
            else:
                Logger.log("d", "Something went wrong when trying to update data of API (%s). Message: %s Statuscode: %s", reply_url, reply.readAll(), status_code)
        else:
            Logger.log("d", "NetworkPrinterOutputDevice got an unhandled operation %s", reply.operation())

    def _onUploadProgress(self, bytes_sent, bytes_total):
        if bytes_total > 0:
            new_progress = bytes_sent / bytes_total * 100
            if new_progress > self._progress_message.getProgress():
                self._progress_message.setProgress(bytes_sent / bytes_total * 100)
        else:
            self._progress_message.setProgress(0)
