# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.i18n import i18nCatalog
from UM.Application import Application
from UM.Logger import Logger
from UM.Signal import signalemitter

from UM.Message import Message

import UM.Settings.ContainerRegistry
import UM.Version #To compare firmware version numbers.

from cura.PrinterOutputDevice import PrinterOutputDevice, ConnectionState
from cura.Settings.ContainerManager import ContainerManager
import cura.Settings.ExtruderManager

from PyQt5.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkRequest, QNetworkAccessManager, QNetworkReply
from PyQt5.QtCore import QUrl, QTimer, pyqtSignal, pyqtProperty, pyqtSlot, QCoreApplication
from PyQt5.QtGui import QImage, QColor
from PyQt5.QtWidgets import QMessageBox

import json
import os
import gzip

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
    def __init__(self, key, address, properties, api_prefix):
        super().__init__(key)
        self._address = address
        self._key = key
        self._properties = properties  # Properties dict as provided by zero conf
        self._api_prefix = api_prefix

        self._gcode = None
        self._print_finished = True  # _print_finished == False means we're halfway in a print
        self._write_finished = True  # _write_finished == False means we're currently sending a G-code file

        self._use_gzip = True  # Should we use g-zip compression before sending the data?

        # This holds the full JSON file that was received from the last request.
        # The JSON looks like:
        #{
        #    "led": {"saturation": 0.0, "brightness": 100.0, "hue": 0.0},
        #    "beep": {},
        #    "network": {
        #        "wifi_networks": [],
        #        "ethernet": {"connected": true, "enabled": true},
        #        "wifi": {"ssid": "xxxx", "connected": False, "enabled": False}
        #    },
        #    "diagnostics": {},
        #    "bed": {"temperature": {"target": 60.0, "current": 44.4}},
        #    "heads": [{
        #        "max_speed": {"z": 40.0, "y": 300.0, "x": 300.0},
        #        "position": {"z": 20.0, "y": 6.0, "x": 180.0},
        #        "fan": 0.0,
        #        "jerk": {"z": 0.4, "y": 20.0, "x": 20.0},
        #        "extruders": [
        #            {
        #                "feeder": {"max_speed": 45.0, "jerk": 5.0, "acceleration": 3000.0},
        #                "active_material": {"guid": "xxxxxxx", "length_remaining": -1.0},
        #                "hotend": {"temperature": {"target": 0.0, "current": 22.8}, "id": "AA 0.4"}
        #            },
        #            {
        #                "feeder": {"max_speed": 45.0, "jerk": 5.0, "acceleration": 3000.0},
        #                "active_material": {"guid": "xxxx", "length_remaining": -1.0},
        #                "hotend": {"temperature": {"target": 0.0, "current": 22.8}, "id": "BB 0.4"}
        #            }
        #        ],
        #        "acceleration": 3000.0
        #    }],
        #    "status": "printing"
        #}

        self._json_printer_state = {}

        ##  Todo: Hardcoded value now; we should probably read this from the machine file.
        ##  It's okay to leave this for now, as this plugin is um3 only (and has 2 extruders by definition)
        self._num_extruders = 2

        # These are reinitialised here (from PrinterOutputDevice) to match the new _num_extruders
        self._hotend_temperatures = [0] * self._num_extruders
        self._target_hotend_temperatures = [0] * self._num_extruders

        self._material_ids = [""] * self._num_extruders
        self._hotend_ids = [""] * self._num_extruders
        self._target_bed_temperature = 0
        self._processing_preheat_requests = True

        self.setPriority(3) # Make sure the output device gets selected above local file output
        self.setName(key)
        self.setShortDescription(i18n_catalog.i18nc("@action:button Preceded by 'Ready to'.", "Print over network"))
        self.setDescription(i18n_catalog.i18nc("@properties:tooltip", "Print over network"))
        self.setIconName("print")

        self._manager = None

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
        self._camera_timer.setInterval(500)  # Todo: Add preference for camera update interval
        self._camera_timer.setSingleShot(False)
        self._camera_timer.timeout.connect(self._updateCamera)

        self._image_request = None
        self._image_reply = None

        self._use_stream = True
        self._stream_buffer = b""
        self._stream_buffer_start_index = -1

        self._camera_image_id = 0

        self._authentication_counter = 0
        self._max_authentication_counter = 5 * 60  # Number of attempts before authentication timed out (5 min)

        self._authentication_timer = QTimer()
        self._authentication_timer.setInterval(1000)  # TODO; Add preference for update interval
        self._authentication_timer.setSingleShot(False)
        self._authentication_timer.timeout.connect(self._onAuthenticationTimer)
        self._authentication_request_active = False

        self._authentication_state = AuthState.NotAuthenticated
        self._authentication_id = None
        self._authentication_key = None

        self._authentication_requested_message = Message(i18n_catalog.i18nc("@info:status", "Access to the printer requested. Please approve the request on the printer"), lifetime = 0, dismissable = False, progress = 0, title = i18n_catalog.i18nc("@info:title", "Connection status"))
        self._authentication_failed_message = Message(i18n_catalog.i18nc("@info:status", ""), title = i18n_catalog.i18nc("@info:title", "Connection Status"))
        self._authentication_failed_message.addAction("Retry", i18n_catalog.i18nc("@action:button", "Retry"), None, i18n_catalog.i18nc("@info:tooltip", "Re-send the access request"))
        self._authentication_failed_message.actionTriggered.connect(self.requestAuthentication)
        self._authentication_succeeded_message = Message(i18n_catalog.i18nc("@info:status", "Access to the printer accepted"), title = i18n_catalog.i18nc("@info:title", "Connection Status"))
        self._not_authenticated_message = Message(i18n_catalog.i18nc("@info:status", "No access to print with this printer. Unable to send print job."), title = i18n_catalog.i18nc("@info:title", "Connection Status"))
        self._not_authenticated_message.addAction("Request", i18n_catalog.i18nc("@action:button", "Request Access"), None, i18n_catalog.i18nc("@info:tooltip", "Send access request to the printer"))
        self._not_authenticated_message.actionTriggered.connect(self.requestAuthentication)

        self._camera_image = QImage()

        self._material_post_objects = {}
        self._connection_state_before_timeout = None

        self._last_response_time = time()
        self._last_request_time = None
        self._response_timeout_time = 10
        self._recreate_network_manager_time = 30 # If we have no connection, re-create network manager every 30 sec.
        self._recreate_network_manager_count = 1

        self._send_gcode_start = time()  # Time when the sending of the g-code started.

        self._last_command = ""

        self._compressing_print = False
        self._monitor_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MonitorItem.qml")
        printer_type = self._properties.get(b"machine", b"").decode("utf-8")
        if printer_type.startswith("9511"):
            self._updatePrinterType("ultimaker3_extended")
        elif printer_type.startswith("9066"):
            self._updatePrinterType("ultimaker3")
        else:
            self._updatePrinterType("unknown")

        Application.getInstance().getOutputDeviceManager().outputDevicesChanged.connect(self._onOutputDevicesChanged)

    def _onNetworkAccesibleChanged(self, accessible):
        Logger.log("d", "Network accessible state changed to: %s", accessible)

    ##  Triggered when the output device manager changes devices.
    #
    #   This is how we can detect that our device is no longer active now.
    def _onOutputDevicesChanged(self):
        if self.getId() not in Application.getInstance().getOutputDeviceManager().getOutputDeviceIds():
            self.stopCamera()

    def _onAuthenticationTimer(self):
        self._authentication_counter += 1
        self._authentication_requested_message.setProgress(self._authentication_counter / self._max_authentication_counter * 100)
        if self._authentication_counter > self._max_authentication_counter:
            self._authentication_timer.stop()
            Logger.log("i", "Authentication timer ended. Setting authentication to denied for printer: %s" % self._key)
            self.setAuthenticationState(AuthState.AuthenticationDenied)

    def _onAuthenticationRequired(self, reply, authenticator):
        if self._authentication_id is not None and self._authentication_key is not None:
            Logger.log("d", "Authentication was required for printer: %s. Setting up authenticator with ID %s and key %s", self._key, self._authentication_id, self._getSafeAuthKey())
            authenticator.setUser(self._authentication_id)
            authenticator.setPassword(self._authentication_key)
        else:
            Logger.log("d", "No authentication is available to use for %s, but we did got a request for it.", self._key)

    def getProperties(self):
        return self._properties

    @pyqtSlot(str, result = str)
    def getProperty(self, key):
        key = key.encode("utf-8")
        if key in self._properties:
            return self._properties.get(key, b"").decode("utf-8")
        else:
            return ""

    ##  Get the unique key of this machine
    #   \return key String containing the key of the machine.
    @pyqtSlot(result = str)
    def getKey(self):
        return self._key

    ##  The IP address of the printer.
    @pyqtProperty(str, constant = True)
    def address(self):
        return self._properties.get(b"address", b"").decode("utf-8")

    ##  Name of the printer (as returned from the ZeroConf properties)
    @pyqtProperty(str, constant = True)
    def name(self):
        return self._properties.get(b"name", b"").decode("utf-8")

    ##  Firmware version (as returned from the ZeroConf properties)
    @pyqtProperty(str, constant=True)
    def firmwareVersion(self):
        return self._properties.get(b"firmware_version", b"").decode("utf-8")

    ## IPadress of this printer
    @pyqtProperty(str, constant=True)
    def ipAddress(self):
        return self._address

    ##  Pre-heats the heated bed of the printer.
    #
    #   \param temperature The temperature to heat the bed to, in degrees
    #   Celsius.
    #   \param duration How long the bed should stay warm, in seconds.
    @pyqtSlot(float, float)
    def preheatBed(self, temperature, duration):
        temperature = round(temperature) #The API doesn't allow floating point.
        duration = round(duration)
        if UM.Version.Version(self.firmwareVersion) < UM.Version.Version("3.5.92"): #Real bed pre-heating support is implemented from 3.5.92 and up.
            self.setTargetBedTemperature(temperature = temperature) #No firmware-side duration support then.
            return
        url = QUrl("http://" + self._address + self._api_prefix + "printer/bed/pre_heat")
        if duration > 0:
            data = """{"temperature": "%i", "timeout": "%i"}""" % (temperature, duration)
        else:
            data = """{"temperature": "%i"}""" % temperature
        Logger.log("i", "Pre-heating bed to %i degrees.", temperature)
        put_request = QNetworkRequest(url)
        put_request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        self._processing_preheat_requests = False
        self._manager.put(put_request, data.encode())
        self._preheat_bed_timer.start(self._preheat_bed_timeout * 1000) #Times 1000 because it needs to be provided as milliseconds.
        self.preheatBedRemainingTimeChanged.emit()

    ##  Cancels pre-heating the heated bed of the printer.
    #
    #   If the bed is not pre-heated, nothing happens.
    @pyqtSlot()
    def cancelPreheatBed(self):
        Logger.log("i", "Cancelling pre-heating of the bed.")
        self.preheatBed(temperature = 0, duration = 0)
        self._preheat_bed_timer.stop()
        self._preheat_bed_timer.setInterval(0)
        self.preheatBedRemainingTimeChanged.emit()

    ##  Changes the target bed temperature on the printer.
    #
    #   /param temperature The new target temperature of the bed.
    def _setTargetBedTemperature(self, temperature):
        if not self._updateTargetBedTemperature(temperature):
            return

        url = QUrl("http://" + self._address + self._api_prefix + "printer/bed/temperature/target")
        data = str(temperature)
        put_request = QNetworkRequest(url)
        put_request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        self._manager.put(put_request, data.encode())

    ##  Updates the target bed temperature from the printer, and emit a signal if it was changed.
    #
    #   /param temperature The new target temperature of the bed.
    #   /return boolean, True if the temperature was changed, false if the new temperature has the same value as the already stored temperature
    def _updateTargetBedTemperature(self, temperature):
        if self._target_bed_temperature == temperature:
            return False
        self._target_bed_temperature = temperature
        self.targetBedTemperatureChanged.emit()
        return True

    ##  Updates the target hotend temperature from the printer, and emit a signal if it was changed.
    #
    #   /param index The index of the hotend.
    #   /param temperature The new target temperature of the hotend.
    #   /return boolean, True if the temperature was changed, false if the new temperature has the same value as the already stored temperature
    def _updateTargetHotendTemperature(self, index, temperature):
        if self._target_hotend_temperatures[index] == temperature:
            return False
        self._target_hotend_temperatures[index] = temperature
        self.targetHotendTemperaturesChanged.emit()
        return True

    def _stopCamera(self):
        self._stream_buffer = b""
        self._stream_buffer_start_index = -1

        if self._camera_timer.isActive():
            self._camera_timer.stop()

        if self._image_reply:
            try:
                # disconnect the signal
                try:
                    self._image_reply.downloadProgress.disconnect(self._onStreamDownloadProgress)
                except Exception:
                    pass
                # abort the request if it's not finished
                if not self._image_reply.isFinished():
                    self._image_reply.close()
            except Exception as e: #RuntimeError
                pass  # It can happen that the wrapped c++ object is already deleted.
            self._image_reply = None
            self._image_request = None

    def _startCamera(self):
        if self._use_stream:
            self._startCameraStream()
        else:
            self._camera_timer.start()

    def _startCameraStream(self):
        ## Request new image
        url = QUrl("http://" + self._address + ":8080/?action=stream")
        self._image_request = QNetworkRequest(url)
        self._image_reply = self._manager.get(self._image_request)
        self._image_reply.downloadProgress.connect(self._onStreamDownloadProgress)

    def _updateCamera(self):
        if not self._manager.networkAccessible():
            return
        ## Request new image
        url = QUrl("http://" + self._address + ":8080/?action=snapshot")
        image_request = QNetworkRequest(url)
        self._manager.get(image_request)
        self._last_request_time = time()

    ##  Set the authentication state.
    #   \param auth_state \type{AuthState} Enum value representing the new auth state
    def setAuthenticationState(self, auth_state):
        if auth_state == self._authentication_state:
            return  # Nothing to do here.

        Logger.log("d", "Attempting to update auth state from %s to %s for printer %s" % (self._authentication_state, auth_state, self._key))

        if auth_state == AuthState.AuthenticationRequested:
            Logger.log("d", "Authentication state changed to authentication requested.")
            self.setAcceptsCommands(False)
            self.setConnectionText(i18n_catalog.i18nc("@info:status", "Connected over the network. Please approve the access request on the printer."))
            self._authentication_requested_message.show()
            self._authentication_request_active = True
            self._authentication_timer.start()  # Start timer so auth will fail after a while.
        elif auth_state == AuthState.Authenticated:
            Logger.log("d", "Authentication state changed to authenticated")
            self.setAcceptsCommands(True)
            self.setConnectionText(i18n_catalog.i18nc("@info:status", "Connected over the network."))
            self._authentication_requested_message.hide()
            if self._authentication_request_active:
                self._authentication_succeeded_message.show()

            # Stop waiting for a response
            self._authentication_timer.stop()
            self._authentication_counter = 0

            # Once we are authenticated we need to send all material profiles.
            self.sendMaterialProfiles()
        elif auth_state == AuthState.AuthenticationDenied:
            self.setAcceptsCommands(False)
            self.setConnectionText(i18n_catalog.i18nc("@info:status", "Connected over the network. No access to control the printer."))
            self._authentication_requested_message.hide()
            if self._authentication_request_active:
                if self._authentication_timer.remainingTime() > 0:
                    Logger.log("d", "Authentication state changed to authentication denied before the request timeout.")
                    self._authentication_failed_message.setText(i18n_catalog.i18nc("@info:status", "Access request was denied on the printer."))
                else:
                    Logger.log("d", "Authentication state changed to authentication denied due to a timeout")
                    self._authentication_failed_message.setText(i18n_catalog.i18nc("@info:status", "Access request failed due to a timeout."))

                self._authentication_failed_message.show()
            self._authentication_request_active = False

            # Stop waiting for a response
            self._authentication_timer.stop()
            self._authentication_counter = 0

        self._authentication_state = auth_state
        self.authenticationStateChanged.emit()

    authenticationStateChanged = pyqtSignal()

    @pyqtProperty(int, notify = authenticationStateChanged)
    def authenticationState(self):
        return self._authentication_state

    @pyqtSlot()
    def requestAuthentication(self, message_id = None, action_id = "Retry"):
        if action_id == "Request" or action_id == "Retry":
            Logger.log("d", "Requestion authentication for %s due to action %s" % (self._key, action_id))
            self._authentication_failed_message.hide()
            self._not_authenticated_message.hide()
            self.setAuthenticationState(AuthState.NotAuthenticated)
            self._authentication_counter = 0
            self._authentication_requested_message.setProgress(0)
            self._authentication_id = None
            self._authentication_key = None
            self._createNetworkManager() # Re-create network manager to force re-authentication.

    ##  Request data from the connected device.
    def _update(self):
        if self._last_response_time:
            time_since_last_response = time() - self._last_response_time
        else:
            time_since_last_response = 0
        if self._last_request_time:
            time_since_last_request = time() - self._last_request_time
        else:
            time_since_last_request = float("inf") # An irrelevantly large number of seconds

        # Connection is in timeout, check if we need to re-start the connection.
        # Sometimes the qNetwork manager incorrectly reports the network status on Mac & Windows.
        # Re-creating the QNetworkManager seems to fix this issue.
        if self._last_response_time and self._connection_state_before_timeout:
            if time_since_last_response > self._recreate_network_manager_time * self._recreate_network_manager_count:
                self._recreate_network_manager_count += 1
                counter = 0  # Counter to prevent possible indefinite while loop.
                # It can happen that we had a very long timeout (multiple times the recreate time).
                # In that case we should jump through the point that the next update won't be right away.
                while time_since_last_response - self._recreate_network_manager_time * self._recreate_network_manager_count > self._recreate_network_manager_time and counter < 10:
                    counter += 1
                    self._recreate_network_manager_count += 1
                Logger.log("d", "Timeout lasted over %.0f seconds (%.1fs), re-checking connection.", self._recreate_network_manager_time, time_since_last_response)
                self._createNetworkManager()
                return

        # Check if we have an connection in the first place.
        if not self._manager.networkAccessible():
            if not self._connection_state_before_timeout:
                Logger.log("d", "The network connection seems to be disabled. Going into timeout mode")
                self._connection_state_before_timeout = self._connection_state
                self.setConnectionState(ConnectionState.error)
                self._connection_message = Message(i18n_catalog.i18nc("@info:status",
                                                                      "The connection with the network was lost."),
                                                   title = i18n_catalog.i18nc("@info:title", "Connection Status"))
                self._connection_message.show()

                if self._progress_message:
                    self._progress_message.hide()

                # Check if we were uploading something. Abort if this is the case.
                # Some operating systems handle this themselves, others give weird issues.
                if self._post_reply:
                    Logger.log("d", "Stopping post upload because the connection was lost.")
                    self._finalizePostReply()
            return
        else:
            if not self._connection_state_before_timeout:
                self._recreate_network_manager_count = 1

        # Check that we aren't in a timeout state
        if self._last_response_time and self._last_request_time and not self._connection_state_before_timeout:
            if time_since_last_response > self._response_timeout_time and time_since_last_request <= self._response_timeout_time:
                # Go into timeout state.
                Logger.log("d", "We did not receive a response for %0.1f seconds, so it seems the printer is no longer accessible.", time_since_last_response)
                self._connection_state_before_timeout = self._connection_state
                self._connection_message = Message(i18n_catalog.i18nc("@info:status", "The connection with the printer was lost. Check your printer to see if it is connected."),
                                                   title = i18n_catalog.i18nc("@info:title", "Connection Status"))
                self._connection_message.show()

                if self._progress_message:
                    self._progress_message.hide()

                # Check if we were uploading something. Abort if this is the case.
                # Some operating systems handle this themselves, others give weird issues.
                if self._post_reply:
                    Logger.log("d", "Stopping post upload because the connection was lost.")
                    self._finalizePostReply()
                self.setConnectionState(ConnectionState.error)
                return

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

        self._last_request_time = time()

    def _finalizePostReply(self):
        # Indicate uploading was finished (so another file can be send)
        self._write_finished = True

        if self._post_reply is None:
            return

        try:
            try:
                self._post_reply.uploadProgress.disconnect(self._onUploadProgress)
            except TypeError:
                pass  # The disconnection can fail on mac in some cases. Ignore that.

            try:
                self._post_reply.finished.disconnect(self._onUploadFinished)
            except TypeError:
                pass  # The disconnection can fail on mac in some cases. Ignore that.

            self._post_reply.abort()
            self._post_reply = None
        except RuntimeError:
            self._post_reply = None  # It can happen that the wrapped c++ object is already deleted.

    def _createNetworkManager(self):
        if self._manager:
            self._manager.finished.disconnect(self._onFinished)
            self._manager.networkAccessibleChanged.disconnect(self._onNetworkAccesibleChanged)
            self._manager.authenticationRequired.disconnect(self._onAuthenticationRequired)

        self._manager = QNetworkAccessManager()
        self._manager.finished.connect(self._onFinished)
        self._manager.authenticationRequired.connect(self._onAuthenticationRequired)
        self._manager.networkAccessibleChanged.connect(self._onNetworkAccesibleChanged)  # for debug purposes

    ##  Convenience function that gets information from the received json data and converts it to the right internal
    #   values / variables
    def _spliceJSONData(self):
        # Check for hotend temperatures
        for index in range(0, self._num_extruders):
            temperatures = self._json_printer_state["heads"][0]["extruders"][index]["hotend"]["temperature"]
            self._setHotendTemperature(index, temperatures["current"])
            self._updateTargetHotendTemperature(index, temperatures["target"])
            try:
                material_id = self._json_printer_state["heads"][0]["extruders"][index]["active_material"]["guid"]
            except KeyError:
                material_id = ""
            self._setMaterialId(index, material_id)
            try:
                hotend_id = self._json_printer_state["heads"][0]["extruders"][index]["hotend"]["id"]
            except KeyError:
                hotend_id = ""
            self._setHotendId(index, hotend_id)

        bed_temperatures = self._json_printer_state["bed"]["temperature"]
        self._setBedTemperature(bed_temperatures["current"])
        self._updateTargetBedTemperature(bed_temperatures["target"])

        head_x = self._json_printer_state["heads"][0]["position"]["x"]
        head_y = self._json_printer_state["heads"][0]["position"]["y"]
        head_z = self._json_printer_state["heads"][0]["position"]["z"]
        self._updateHeadPosition(head_x, head_y, head_z)
        self._updatePrinterState(self._json_printer_state["status"])

        if self._processing_preheat_requests:
            try:
                is_preheating = self._json_printer_state["bed"]["pre_heat"]["active"]
            except KeyError: #Old firmware doesn't support that.
                pass #Don't update the pre-heat remaining time.
            else:
                if is_preheating:
                    try:
                        remaining_preheat_time = self._json_printer_state["bed"]["pre_heat"]["remaining"]
                    except KeyError: #Error in firmware. If "active" is supported, "remaining" should also be supported.
                        pass #Anyway, don't update.
                    else:
                        #Only update if time estimate is significantly off (>5000ms).
                        #Otherwise we get issues with latency causing the timer to count inconsistently.
                        if abs(self._preheat_bed_timer.remainingTime() - remaining_preheat_time * 1000) > 5000:
                            self._preheat_bed_timer.setInterval(remaining_preheat_time * 1000)
                            self._preheat_bed_timer.start()
                            self.preheatBedRemainingTimeChanged.emit()
                else: #Not pre-heating. Must've cancelled.
                    if self._preheat_bed_timer.isActive():
                        self._preheat_bed_timer.setInterval(0)
                        self._preheat_bed_timer.stop()
                        self.preheatBedRemainingTimeChanged.emit()

    def close(self):
        Logger.log("d", "Closing connection of printer %s with ip %s", self._key, self._address)
        self._updateJobState("")
        self.setConnectionState(ConnectionState.closed)
        if self._progress_message:
            self._progress_message.hide()

        # Reset authentication state
        self._authentication_requested_message.hide()
        self.setAuthenticationState(AuthState.NotAuthenticated)
        self._authentication_counter = 0
        self._authentication_timer.stop()

        self._authentication_requested_message.hide()
        self._authentication_failed_message.hide()
        self._authentication_succeeded_message.hide()

        # Reset stored material & hotend data.
        self._material_ids = [""] * self._num_extruders
        self._hotend_ids = [""] * self._num_extruders

        if self._error_message:
            self._error_message.hide()

        # Reset timeout state
        self._connection_state_before_timeout = None
        self._last_response_time = time()
        self._last_request_time = None

        # Stop update timers
        self._update_timer.stop()

        self.stopCamera()

    ##  Request the current scene to be sent to a network-connected printer.
    #
    #   \param nodes A collection of scene nodes to send. This is ignored.
    #   \param file_name \type{string} A suggestion for a file name to write.
    #   This is ignored.
    #   \param filter_by_machine Whether to filter MIME types by machine. This
    #   is ignored.
    #   \param kwargs Keyword arguments.
    def requestWrite(self, nodes, file_name=None, filter_by_machine=False, file_handler=None, **kwargs):

        if self._printer_state not in ["idle", ""]:
            self._error_message = Message(
                i18n_catalog.i18nc("@info:status", "Unable to start a new print job, printer is busy. Current printer status is %s.") % self._printer_state,
                title = i18n_catalog.i18nc("@info:title", "Printer Status"))
            self._error_message.show()
            return
        elif self._authentication_state != AuthState.Authenticated:
            self._not_authenticated_message.show()
            Logger.log("d", "Attempting to perform an action without authentication for printer %s. Auth state is %s", self._key, self._authentication_state)
            return

        Application.getInstance().showPrintMonitor.emit(True)
        self._print_finished = True
        self.writeStarted.emit(self)
        self._gcode = getattr(Application.getInstance().getController().getScene(), "gcode_list")

        print_information = Application.getInstance().getPrintInformation()
        warnings = []  # There might be multiple things wrong. Keep a list of all the stuff we need to warn about.

        # Only check for mistakes if there is material length information.
        if print_information.materialLengths:
            # Check if PrintCores / materials are loaded at all. Any failure in these results in an Error.
            for index in range(0, self._num_extruders):
                if index < len(print_information.materialLengths) and print_information.materialLengths[index] != 0:
                    if self._json_printer_state["heads"][0]["extruders"][index]["hotend"]["id"] == "":
                        Logger.log("e", "No cartridge loaded in slot %s, unable to start print", index + 1)
                        self._error_message = Message(
                            i18n_catalog.i18nc("@info:status", "Unable to start a new print job. No Printcore loaded in slot {0}".format(index + 1)),
                            title = i18n_catalog.i18nc("@info:title", "Error"))
                        self._error_message.show()
                        return
                    if self._json_printer_state["heads"][0]["extruders"][index]["active_material"]["guid"] == "":
                        Logger.log("e", "No material loaded in slot %s, unable to start print", index + 1)
                        self._error_message = Message(
                            i18n_catalog.i18nc("@info:status",
                                               "Unable to start a new print job. No material loaded in slot {0}".format(index + 1)),
                            title = i18n_catalog.i18nc("@info:title", "Error"))
                        self._error_message.show()
                        return

            for index in range(0, self._num_extruders):
                # Check if there is enough material. Any failure in these results in a warning.
                material_length = self._json_printer_state["heads"][0]["extruders"][index]["active_material"]["length_remaining"]
                if material_length != -1 and index < len(print_information.materialLengths) and print_information.materialLengths[index] > material_length:
                    Logger.log("w", "Printer reports that there is not enough material left for extruder %s. We need %s and the printer has %s", index + 1, print_information.materialLengths[index], material_length)
                    warnings.append(i18n_catalog.i18nc("@label", "Not enough material for spool {0}.").format(index+1))

                # Check if the right cartridges are loaded. Any failure in these results in a warning.
                extruder_manager = cura.Settings.ExtruderManager.ExtruderManager.getInstance()
                if index < len(print_information.materialLengths) and print_information.materialLengths[index] != 0:
                    variant = extruder_manager.getExtruderStack(index).findContainer({"type": "variant"})
                    core_name = self._json_printer_state["heads"][0]["extruders"][index]["hotend"]["id"]
                    if variant:
                        if variant.getName() != core_name:
                            Logger.log("w", "Extruder %s has a different Cartridge (%s) as Cura (%s)", index + 1, core_name, variant.getName())
                            warnings.append(i18n_catalog.i18nc("@label", "Different PrintCore (Cura: {0}, Printer: {1}) selected for extruder {2}".format(variant.getName(), core_name, index + 1)))

                    material = extruder_manager.getExtruderStack(index).findContainer({"type": "material"})
                    if material:
                        remote_material_guid = self._json_printer_state["heads"][0]["extruders"][index]["active_material"]["guid"]
                        if material.getMetaDataEntry("GUID") != remote_material_guid:
                            Logger.log("w", "Extruder %s has a different material (%s) as Cura (%s)", index + 1,
                                       remote_material_guid,
                                       material.getMetaDataEntry("GUID"))

                            remote_materials = UM.Settings.ContainerRegistry.ContainerRegistry.getInstance().findInstanceContainers(type = "material", GUID = remote_material_guid, read_only = True)
                            remote_material_name = "Unknown"
                            if remote_materials:
                                remote_material_name = remote_materials[0].getName()
                            warnings.append(i18n_catalog.i18nc("@label", "Different material (Cura: {0}, Printer: {1}) selected for extruder {2}").format(material.getName(), remote_material_name, index + 1))

                    try:
                        is_offset_calibrated = self._json_printer_state["heads"][0]["extruders"][index]["hotend"]["offset"]["state"] == "valid"
                    except KeyError:  # Older versions of the API don't expose the offset property, so we must asume that all is well.
                        is_offset_calibrated = True

                    if not is_offset_calibrated:
                        warnings.append(i18n_catalog.i18nc("@label", "PrintCore {0} is not properly calibrated. XY calibration needs to be performed on the printer.").format(index + 1))
        else:
            Logger.log("w", "There was no material usage found. No check to match used material with machine is done.")

        if warnings:
            text = i18n_catalog.i18nc("@label", "Are you sure you wish to print with the selected configuration?")
            informative_text = i18n_catalog.i18nc("@label", "There is a mismatch between the configuration or calibration of the printer and Cura. "
                                                "For the best result, always slice for the PrintCores and materials that are inserted in your printer.")
            detailed_text = ""
            for warning in warnings:
                detailed_text += warning + "\n"

            Application.getInstance().messageBox(i18n_catalog.i18nc("@window:title", "Mismatched configuration"),
                                                 text,
                                                 informative_text,
                                                 detailed_text,
                                                 buttons=QMessageBox.Yes + QMessageBox.No,
                                                 icon=QMessageBox.Question,
                                                 callback=self._configurationMismatchMessageCallback
                                                 )
            return

        self.startPrint()

    def _configurationMismatchMessageCallback(self, button):
        def delayedCallback():
            if button == QMessageBox.Yes:
                self.startPrint()
            else:
                Application.getInstance().showPrintMonitor.emit(False)
        # For some unknown reason Cura on OSX will hang if we do the call back code
        # immediately without first returning and leaving QML's event system.
        QTimer.singleShot(100, delayedCallback)

    def isConnected(self):
        return self._connection_state != ConnectionState.closed and self._connection_state != ConnectionState.error

    ##  Start requesting data from printer
    def connect(self):
        if self.isConnected():
            self.close()  # Close previous connection

        self._createNetworkManager()

        self._last_response_time = time()  # Ensure we reset the time when trying to connect (again)

        self.setConnectionState(ConnectionState.connecting)
        self._update()  # Manually trigger the first update, as we don't want to wait a few secs before it starts.
        if not self._use_stream:
            self._updateCamera()
        Logger.log("d", "Connection with printer %s with ip %s started", self._key, self._address)

        ## Check if this machine was authenticated before.
        self._authentication_id = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("network_authentication_id", None)
        self._authentication_key = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("network_authentication_key", None)

        if self._authentication_id is None and self._authentication_key is None:
            Logger.log("d", "No authentication found in metadata.")
        else:
            Logger.log("d", "Loaded authentication id %s and key %s from the metadata entry for printer %s", self._authentication_id, self._getSafeAuthKey(), self._key)

        self._update_timer.start()

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
        self._last_command = job_state
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

    def _progressMessageActionTrigger(self, message_id = None, action_id = None):
        if action_id == "Abort":
            Logger.log("d", "User aborted sending print to remote.")
            self._progress_message.hide()
            self._compressing_print = False
            self._write_finished = True  # post_reply does not always exist, so make sure we unblock writing
            if self._post_reply:
                self._finalizePostReply()
            Application.getInstance().showPrintMonitor.emit(False)

    ##  Attempt to start a new print.
    #   This function can fail to actually start a print due to not being authenticated or another print already
    #   being in progress.
    def startPrint(self):

        # Check if we're already writing
        if not self._write_finished:
            self._error_message = Message(
                i18n_catalog.i18nc("@info:status",
                                   "Sending new jobs (temporarily) blocked, still sending the previous print job."))
            self._error_message.show()
            return

        # Indicate we're starting a new write action, is set back to True at the end of this method
        self._write_finished = False

        try:
            self._send_gcode_start = time()
            self._progress_message = Message(i18n_catalog.i18nc("@info:status", "Sending data to printer"), 0, False, -1, i18n_catalog.i18nc("@info:title", "Sending Data"))
            self._progress_message.addAction("Abort", i18n_catalog.i18nc("@action:button", "Cancel"), None, "")
            self._progress_message.actionTriggered.connect(self._progressMessageActionTrigger)
            self._progress_message.show()
            Logger.log("d", "Started sending g-code to remote printer.")
            self._compressing_print = True
            ## Mash the data into single string

            max_chars_per_line = 1024 * 1024 / 4  # 1 / 4  MB

            byte_array_file_data = b""
            batched_line = ""

            def _compress_data_and_notify_qt(data_to_append):
                compressed_data = gzip.compress(data_to_append.encode("utf-8"))
                self._progress_message.setProgress(-1) # Tickle the message so that it's clear that it's still being used.
                QCoreApplication.processEvents()  # Ensure that the GUI does not freeze.
                # Pretend that this is a response, as zipping might take a bit of time.
                self._last_response_time = time()
                return compressed_data

            for line in self._gcode:
                if not self._compressing_print:
                    self._progress_message.hide()
                    return  # Stop trying to zip, abort was called.

                if self._use_gzip:
                    batched_line += line
                    # if the gcode was read from a gcode file, self._gcode will be a list of all lines in that file.
                    # Compressing line by line in this case is extremely slow, so we need to batch them.
                    if len(batched_line) < max_chars_per_line:
                        continue

                    byte_array_file_data += _compress_data_and_notify_qt(batched_line)
                    batched_line = ""
                else:
                    byte_array_file_data += line.encode("utf-8")

            # don't miss the last batch if it's there
            if self._use_gzip:
                if batched_line:
                    byte_array_file_data += _compress_data_and_notify_qt(batched_line)

            if self._use_gzip:
                file_name = "%s.gcode.gz" % Application.getInstance().getPrintInformation().jobName
            else:
                file_name = "%s.gcode" % Application.getInstance().getPrintInformation().jobName

            self._compressing_print = False
            ##  Create multi_part request
            self._post_multi_part = QHttpMultiPart(QHttpMultiPart.FormDataType)

            ##  Create part (to be placed inside multipart)
            self._post_part = QHttpPart()
            self._post_part.setHeader(QNetworkRequest.ContentDispositionHeader,
                           "form-data; name=\"file\"; filename=\"%s\"" % file_name)
            self._post_part.setBody(byte_array_file_data)
            self._post_multi_part.append(self._post_part)

            url = QUrl("http://" + self._address + self._api_prefix + "print_job")

            ##  Create the QT request
            self._post_request = QNetworkRequest(url)

            ##  Post request + data
            self._post_reply = self._manager.post(self._post_request, self._post_multi_part)
            self._post_reply.uploadProgress.connect(self._onUploadProgress)
            self._post_reply.finished.connect(self._onUploadFinished)  # used to unblock new write actions

        except IOError:
            self._progress_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Unable to send data to printer. Is another job still active?"),
                                          title = i18n_catalog.i18nc("@info:title", "Warning"))
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
        Logger.log("d", "Checking if authentication is correct for id %s and key %s", self._authentication_id, self._getSafeAuthKey())
        self._manager.get(QNetworkRequest(QUrl("http://" + self._address + self._api_prefix + "auth/check/" + str(self._authentication_id))))

    ##  Request a authentication key from the printer so we can be authenticated
    def _requestAuthentication(self):
        url = QUrl("http://" + self._address + self._api_prefix + "auth/request")
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        self._authentication_key = None
        self._authentication_id = None
        self._manager.post(request, json.dumps({"application": "Cura-" + Application.getInstance().getVersion(), "user": self._getUserName()}).encode())
        self.setAuthenticationState(AuthState.AuthenticationRequested)

    ##  Send all material profiles to the printer.
    def sendMaterialProfiles(self):
        for container in UM.Settings.ContainerRegistry.ContainerRegistry.getInstance().findInstanceContainers(type = "material"):
            try:
                xml_data = container.serialize()
                if xml_data == "" or xml_data is None:
                    continue

                names = ContainerManager.getInstance().getLinkedMaterials(container.getId())
                if names:
                    # There are other materials that share this GUID.
                    if not container.isReadOnly():
                        continue  # If it's not readonly, it's created by user, so skip it.

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
            # Check if we were uploading something. Abort if this is the case.
            # Some operating systems handle this themselves, others give weird issues.
            if self._post_reply:
                self._finalizePostReply()
                Logger.log("d", "Uploading of print failed after %s", time() - self._send_gcode_start)
                self._progress_message.hide()

            self.setConnectionState(ConnectionState.error)
            return

        if self._connection_state_before_timeout and reply.error() == QNetworkReply.NoError:  # There was a timeout, but we got a correct answer again.
            Logger.log("d", "We got a response (%s) from the server after %0.1f of silence. Going back to previous state %s", reply.url().toString(), time() - self._last_response_time, self._connection_state_before_timeout)

            # Camera was active before timeout. Start it again
            if self._camera_active:
                self._startCamera()

            self.setConnectionState(self._connection_state_before_timeout)
            self._connection_state_before_timeout = None

        if reply.error() == QNetworkReply.NoError:
            self._last_response_time = time()

        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if not status_code:
            if self._connection_state != ConnectionState.error:
                Logger.log("d", "A reply from %s did not have status code.", reply.url().toString())
            # Received no or empty reply
            return
        reply_url = reply.url().toString()

        if reply.operation() == QNetworkAccessManager.GetOperation:
            # "printer" is also in "printers", therefore _api_prefix is added.
            if self._api_prefix + "printer" in reply_url:  # Status update from printer.
                if status_code == 200:
                    if self._connection_state == ConnectionState.connecting:
                        self.setConnectionState(ConnectionState.connected)
                    try:
                        self._json_printer_state = json.loads(bytes(reply.readAll()).decode("utf-8"))
                    except json.decoder.JSONDecodeError:
                        Logger.log("w", "Received an invalid printer state message: Not valid JSON.")
                        return
                    self._spliceJSONData()

                    # Hide connection error message if the connection was restored
                    if self._connection_message:
                        self._connection_message.hide()
                        self._connection_message = None
                else:
                    Logger.log("w", "We got an unexpected status (%s) while requesting printer state", status_code)
                    pass  # TODO: Handle errors
            elif self._api_prefix + "print_job" in reply_url:  # Status update from print_job:
                if status_code == 200:
                    try:
                        json_data = json.loads(bytes(reply.readAll()).decode("utf-8"))
                    except json.decoder.JSONDecodeError:
                        Logger.log("w", "Received an invalid print job state message: Not valid JSON.")
                        return
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
                        if self._last_command == "abort":
                            self.setErrorText(i18n_catalog.i18nc("@label:MonitorStatus", "Aborting print..."))
                            state = "error"
                        else:
                            state = "printing"
                    if state == "wait_cleanup" and self._last_command == "abort":
                        # Keep showing the "aborted" error state until after the buildplate has been cleaned
                        self.setErrorText(i18n_catalog.i18nc("@label:MonitorStatus", "Print aborted. Please check the printer"))
                        state = "error"

                    # NB/TODO: the following two states are intentionally added for future proofing the i18n strings
                    #          but are currently non-functional
                    if state == "!pausing":
                        self.setErrorText(i18n_catalog.i18nc("@label:MonitorStatus", "Pausing print..."))
                    if state == "!resuming":
                        self.setErrorText(i18n_catalog.i18nc("@label:MonitorStatus", "Resuming print..."))

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
                        Logger.log("i", "Not authenticated (Current auth state is %s). Attempting to request authentication for printer %s",  self._authentication_state, self._key )
                        self._requestAuthentication()
                elif status_code == 403:
                    # If we already had an auth (eg; didn't request one), we only need a single 403 to see it as denied.
                    if self._authentication_state != AuthState.AuthenticationRequested:
                        Logger.log("d", "While trying to verify the authentication state, we got a forbidden response. Our own auth state was %s", self._authentication_state)
                        self.setAuthenticationState(AuthState.AuthenticationDenied)
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
                        Logger.log("i", "Authentication succeeded for id %s and key %s", self._authentication_id, self._getSafeAuthKey())
                        Application.getInstance().saveStack(global_container_stack)  # Force save so we are sure the data is not lost.
                    else:
                        Logger.log("w", "Unable to save authentication for id %s and key %s", self._authentication_id, self._getSafeAuthKey())

                else:  # Got a response that we didn't expect, so something went wrong.
                    Logger.log("e", "While trying to authenticate, we got an unexpected response: %s", reply.attribute(QNetworkRequest.HttpStatusCodeAttribute))
                    self.setAuthenticationState(AuthState.NotAuthenticated)

            elif "auth/check" in reply_url:  # Check if we are authenticated (user can refuse this!)
                try:
                    data = json.loads(bytes(reply.readAll()).decode("utf-8"))
                except json.decoder.JSONDecodeError:
                    Logger.log("w", "Received an invalid authentication check from printer: Not valid JSON.")
                    return
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
                try:
                    data = json.loads(bytes(reply.readAll()).decode("utf-8"))
                except json.decoder.JSONDecodeError:
                    Logger.log("w", "Received an invalid authentication request reply from printer: Not valid JSON.")
                    return
                global_container_stack = Application.getInstance().getGlobalContainerStack()
                if global_container_stack:  # Remove any old data.
                    Logger.log("d", "Removing old network authentication data for %s as a new one was requested.", self._key)
                    global_container_stack.removeMetaDataEntry("network_authentication_key")
                    global_container_stack.removeMetaDataEntry("network_authentication_id")
                    Application.getInstance().saveStack(global_container_stack)  # Force saving so we don't keep wrong auth data.

                self._authentication_key = data["key"]
                self._authentication_id = data["id"]
                Logger.log("i", "Got a new authentication ID (%s) and KEY (%s). Waiting for authorization.", self._authentication_id, self._getSafeAuthKey())

                # Check if the authentication is accepted.
                self._checkAuthentication()
            elif "materials" in reply_url:
                # Remove cached post request items.
                del self._material_post_objects[id(reply)]
            elif "print_job" in reply_url:
                self._onUploadFinished()  # Make sure the upload flag is reset as reply.finished is not always triggered
                try:
                    reply.uploadProgress.disconnect(self._onUploadProgress)
                except:
                    pass
                try:
                    reply.finished.disconnect(self._onUploadFinished)
                except:
                    pass
                Logger.log("d", "Uploading of print succeeded after %s", time() - self._send_gcode_start)
                # Only reset the _post_reply if it was the same one.
                if reply == self._post_reply:
                    self._post_reply = None
                self._progress_message.hide()

        elif reply.operation() == QNetworkAccessManager.PutOperation:
            if "printer/bed/pre_heat" in reply_url: #Pre-heat command has completed. Re-enable syncing pre-heating.
                self._processing_preheat_requests = True
            if status_code in [200, 201, 202, 204]:
                pass  # Request was successful!
            else:
                Logger.log("d", "Something went wrong when trying to update data of API (%s). Message: %s Statuscode: %s", reply_url, reply.readAll(), status_code)
        else:
            Logger.log("d", "NetworkPrinterOutputDevice got an unhandled operation %s", reply.operation())

    def _onStreamDownloadProgress(self, bytes_received, bytes_total):
        # An MJPG stream is (for our purpose) a stream of concatenated JPG images.
        # JPG images start with the marker 0xFFD8, and end with 0xFFD9
        if self._image_reply is None:
            return
        self._stream_buffer += self._image_reply.readAll()

        if len(self._stream_buffer) > 2000000: # No single camera frame should be 2 Mb or larger
            Logger.log("w", "MJPEG buffer exceeds reasonable size. Restarting stream...")
            self._stopCamera() # resets stream buffer and start index
            self._startCamera()
            return

        if self._stream_buffer_start_index == -1:
            self._stream_buffer_start_index = self._stream_buffer.indexOf(b'\xff\xd8')
        stream_buffer_end_index = self._stream_buffer.lastIndexOf(b'\xff\xd9')
        # If this happens to be more than a single frame, then so be it; the JPG decoder will
        # ignore the extra data. We do it like this in order not to get a buildup of frames

        if self._stream_buffer_start_index != -1 and stream_buffer_end_index != -1:
            jpg_data = self._stream_buffer[self._stream_buffer_start_index:stream_buffer_end_index + 2]
            self._stream_buffer = self._stream_buffer[stream_buffer_end_index + 2:]
            self._stream_buffer_start_index = -1

            self._camera_image.loadFromData(jpg_data)
            self.newImage.emit()

    def _onUploadProgress(self, bytes_sent, bytes_total):
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

    ## Allow new write actions (uploads) again when uploading is finished.
    def _onUploadFinished(self):
        self._write_finished = True

    ##  Let the user decide if the hotends and/or material should be synced with the printer
    def materialHotendChangedMessage(self, callback):
        Application.getInstance().messageBox(i18n_catalog.i18nc("@window:title", "Sync with your printer"),
            i18n_catalog.i18nc("@label",
                "Would you like to use your current printer configuration in Cura?"),
            i18n_catalog.i18nc("@label",
                "The PrintCores and/or materials on your printer differ from those within your current project. For the best result, always slice for the PrintCores and materials that are inserted in your printer."),
            buttons=QMessageBox.Yes + QMessageBox.No,
            icon=QMessageBox.Question,
            callback=callback
        )

    ##  Convenience function to "blur" out all but the last 5 characters of the auth key.
    #   This can be used to debug print the key, without it compromising the security.
    def _getSafeAuthKey(self):
        if self._authentication_key is not None:
            result = self._authentication_key[-5:]
            result = "********" + result
            return result
        return self._authentication_key
