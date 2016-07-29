from UM.i18n import i18nCatalog
from UM.Application import Application
from UM.Logger import Logger
from UM.Signal import signalemitter

from UM.Message import Message

from cura.PrinterOutputDevice import PrinterOutputDevice, ConnectionState

from PyQt5.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkRequest, QNetworkAccessManager
from PyQt5.QtCore import QUrl, QTimer, pyqtSignal, pyqtProperty, pyqtSlot
from PyQt5.QtGui import QImage, QDesktopServices

import json

i18n_catalog = i18nCatalog("cura")


##  OctoPrint connected (wifi / lan) printer using the OctoPrint API
@signalemitter
class OctoPrintOutputDevice(PrinterOutputDevice):
    def __init__(self, key, address, properties):
        super().__init__(key)
        self._address = address
        self._key = key
        self._properties = properties  # Properties dict as provided by zero conf

        self._gcode = None

        ##  Todo: Hardcoded value now; we should probably read this from the machine definition and octoprint.
        self._num_extruders = 1

        self._hotend_temperatures = [0] * self._num_extruders
        self._target_hotend_temperatures = [0] * self._num_extruders

        self._api_version = "1"
        self._api_prefix = "/api/"
        self._api_header = "X-Api-Key"
        self._api_key = None

        self.setName(key)
        self.setShortDescription(i18n_catalog.i18nc("@action:button", "Print with OctoPrint"))
        self.setDescription(i18n_catalog.i18nc("@properties:tooltip", "Print with OctoPrint"))
        self.setIconName("print")

        #   QNetwork manager needs to be created in advance. If we don't it can happen that it doesn't correctly
        #   hook itself into the event loop, which results in events never being fired / done.
        self._manager = QNetworkAccessManager()
        self._manager.finished.connect(self._onFinished)

        ##  Hack to ensure that the qt networking stuff isn't garbage collected (unless we want it to)
        self._printer_request = None
        self._printer_reply = None

        self._print_job_request = None
        self._print_job_reply = None

        self._image_request = None
        self._image_reply = None

        self._post_request = None
        self._post_reply = None
        self._post_multi_part = None
        self._post_part = None

        self._job_request = None
        self._job_reply = None

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
        self._camera_timer.timeout.connect(self._update_camera)

        self._camera_image_id = 0

        self._camera_image = QImage()

        self._connection_state_before_timeout = None

        self._last_response_time = time()
        self._response_timeout_time = 5

    def getProperties(self):
        return self._properties

    ##  Get the unique key of this machine
    #   \return key String containing the key of the machine.
    @pyqtSlot(result = str)
    def getKey(self):
        return self._key

    ##  Set the API key of this OctoPrint instance
    def setApiKey(self, api_key):
        self._api_key = api_key

    ##  Name of the printer (as returned from the zeroConf properties)
    @pyqtProperty(str, constant = True)
    def name(self):
        return self._key

    ##  Version (as returned from the zeroConf properties)
    @pyqtProperty(str, constant=True)
    def octoprintVersion(self):
        return self._properties.get(b"version", b"").decode("utf-8")

    ## IPadress of this printer
    @pyqtProperty(str, constant=True)
    def ipAddress(self):
        return self._address

    def _update_camera(self):
        ## Request new image
        url = QUrl("http://" + self._address + ":8080/?action=snapshot")
        self._image_request = QNetworkRequest(url)
        self._image_reply = self._manager.get(self._image_request)

    def _update(self):
        # Check that we aren't in a timeout state
        if self._last_response_time and not self._connection_state_before_timeout:
            if time() - self._last_response_time > self._response_timeout_time:
                # Go into timeout state.
                Logger.log("d", "We did not receive a response for %s seconds, so it seems the printer is no longer accesible.", time() - self._last_response_time)
                self._connection_state_before_timeout = self._connection_state
                self._connection_message = Message(i18n_catalog.i18nc("@info:status", "The connection with the printer was lost.Check your network-connections."))
                self._connection_message.show()
                self.setConnectionState(ConnectionState.error)

        ## Request 'general' printer data
        url = QUrl("http://" + self._address + self._api_prefix + "printer")
        self._printer_request = QNetworkRequest(url)
        self._printer_request.setRawHeader(self._api_header.encode(), self._api_key.encode())
        self._printer_reply = self._manager.get(self._printer_request)

        ## Request print_job data
        url = QUrl("http://" + self._address + self._api_prefix + "job")
        self._job_request = QNetworkRequest(url)
        self._job_request.setRawHeader(self._api_header.encode(), self._api_key.encode())
        self._job_reply = self._manager.get(self._job_request)

    def close(self):
        self._updateJobState("")
        self.setConnectionState(ConnectionState.closed)
        if self._progress_message:
            self._progress_message.hide()
        if self._error_message:
            self._error_message.hide()
        self._update_timer.stop()
        self._camera_timer.stop()
        self._camera_image = QImage()
        self.newImage.emit()

    def requestWrite(self, node, file_name = None, filter_by_machine = False):
        Application.getInstance().showPrintMonitor.emit(True)
        self._gcode = getattr(Application.getInstance().getController().getScene(), "gcode_list")

        self.startPrint()

    def isConnected(self):
        return self._connection_state != ConnectionState.closed and self._connection_state != ConnectionState.error

    ##  Start requesting data from printer
    def connect(self):
        self.setConnectionState(ConnectionState.connecting)
        self._update()  # Manually trigger the first update, as we don't want to wait a few secs before it starts.
        self._update_camera()
        Logger.log("d", "Connection with printer %s with ip %s started", self._key, self._address)
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
        temp = "image://camera/" + str(self._camera_image_id)
        return QUrl(temp, QUrl.TolerantMode)

    def getCameraImage(self):
        return self._camera_image

    def _setJobState(self, job_state):
        url = QUrl("http://" + self._address + self._api_prefix + "job")
        self._job_request = QNetworkRequest(url)
        self._job_request.setRawHeader(self._api_header.encode(), self._api_key.encode())
        self._job_request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        if job_state == "abort":
            command = "cancel"
        elif job_state == "print":
            if self.jobState == "paused":
                command = "pause"
            else:
                command = "start"
        elif job_state == "pause":
            command = "pause"
        data = "{\"command\": \"%s\"}" % command
        self._job_reply = self._manager.post(self._job_request, data.encode())
        Logger.log("d", "Sent command to OctoPrint instance: %s", data)

    def startPrint(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if not global_container_stack:
            return

        if self.jobState != "ready" and self.jobState != "":
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Printer is printing. Unable to start a new job."))
            self._error_message.show()
            return
        try:
            self._progress_message = Message(i18n_catalog.i18nc("@info:status", "Sending data to OctoPrint"), 0, False, -1)
            self._progress_message.show()

            ## Mash the data into single string
            single_string_file_data = ""
            for line in self._gcode:
                single_string_file_data += line

            file_name = "%s.gcode" % Application.getInstance().getPrintInformation().jobName

            ##  Create multi_part request
            self._post_multi_part = QHttpMultiPart(QHttpMultiPart.FormDataType)

            ##  Create parts (to be placed inside multipart)
            self._post_part = QHttpPart()
            self._post_part.setHeader(QNetworkRequest.ContentDispositionHeader, "form-data; name=\"select\"")
            self._post_part.setBody(b"true")
            self._post_multi_part.append(self._post_part)

            if global_container_stack.getMetaDataEntry("octoprint_auto_print", True):
                self._post_part = QHttpPart()
                self._post_part.setHeader(QNetworkRequest.ContentDispositionHeader, "form-data; name=\"print\"")
                self._post_part.setBody(b"true")
                self._post_multi_part.append(self._post_part)

                self._post_part = QHttpPart()
                self._post_part.setHeader(QNetworkRequest.ContentDispositionHeader, "form-data; name=\"file\"; filename=\"%s\"" % file_name)
                self._post_part.setBody(single_string_file_data.encode())
                self._post_multi_part.append(self._post_part)

            url = QUrl("http://" + self._address + self._api_prefix + "files/local")

            ##  Create the QT request
            self._post_request = QNetworkRequest(url)
            self._post_request.setRawHeader(self._api_header.encode(), self._api_key.encode())

            ##  Post request + data
            self._post_reply = self._manager.post(self._post_request, self._post_multi_part)
            self._post_reply.uploadProgress.connect(self._onUploadProgress)

            self._gcode = None

        except IOError:
            self._progress_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Unable to send data to printer. Is another job still active?"))
            self._error_message.show()
        except Exception as e:
            self._progress_message.hide()
            Logger.log("e", "An exception occurred in network connection: %s" % str(e))

    ##  Handler for all requests that have finished.
    def _onFinished(self, reply):
        if reply.error() == QNetworkReply.TimeoutError:
            Logger.log("w", "Received a timeout on a request to the printer")
            self._connection_state_before_timeout = self._connection_state
            self.setConnectionState(ConnectionState.error)
            return

        if self._connection_state_before_timeout and reply.error() == QNetworkReply.NoError:  #  There was a timeout, but we got a correct answer again.
            Logger.log("d", "We got a response from the server after %s of silence", time() - self._last_response_time )
            self.setConnectionState(self._connection_state_before_timeout)
            self._connection_state_before_timeout = None

        if reply.error() == QNetworkReply.NoError:
            self._last_response_time = time()

        http_status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if not http_status_code:
            # Received no or empty reply
            return

        if reply.operation() == QNetworkAccessManager.GetOperation:
            if "printer" in reply.url().toString():  # Status update from /printer.
                if http_status_code == 200:
                    if self._connection_state == ConnectionState.connecting:
                        self.setConnectionState(ConnectionState.connected)
                    json_data = json.loads(bytes(reply.readAll()).decode("utf-8"))

                    # Check for hotend temperatures
                    for index in range(0, self._num_extruders):
                        temperature = json_data["temperature"]["tool%d" % index]["actual"]
                        self._setHotendTemperature(index, temperature)

                    bed_temperature = json_data["temperature"]["bed"]["actual"]
                    self._setBedTemperature(bed_temperature)

                    printer_state = "offline"
                    if json_data["state"]["flags"]["error"]:
                        printer_state = "error"
                    elif json_data["state"]["flags"]["paused"]:
                        printer_state = "paused"
                    elif json_data["state"]["flags"]["printing"]:
                        printer_state = "printing"
                    elif json_data["state"]["flags"]["ready"]:
                        printer_state = "ready"
                    self._updateJobState(printer_state)
                else:
                    pass  # TODO: Handle errors

            elif "job" in reply.url().toString():  # Status update from /job:
                if http_status_code == 200:
                    json_data = json.loads(bytes(reply.readAll()).decode("utf-8"))

                    progress = json_data["progress"]["completion"]
                    if progress:
                        self.setProgress(progress)

                    if json_data["progress"]["printTime"]:
                        self.setTimeElapsed(json_data["progress"]["printTime"])
                        if json_data["progress"]["printTimeLeft"]:
                            self.setTimeTotal(json_data["progress"]["printTime"] + json_data["progress"]["printTimeLeft"])
                        elif json_data["job"]["estimatedPrintTime"]:
                            self.setTimeTotal(max(json_data["job"]["estimatedPrintTime"], json_data["progress"]["printTime"]))
                        elif progress > 0:
                            self.setTimeTotal(json_data["progress"]["printTime"] / (progress / 100))
                        else:
                            self.setTimeTotal(0)
                    else:
                        self.setTimeElapsed(0)
                        self.setTimeTotal(0)
                    self.setJobName(json_data["job"]["file"]["name"])
                else:
                    pass  # TODO: Handle errors

            elif "snapshot" in reply.url().toString():  # Update from camera:
                if http_status_code == 200:
                    self._camera_image.loadFromData(reply.readAll())
                    self.newImage.emit()
                else:
                    pass  # TODO: Handle errors

        elif reply.operation() == QNetworkAccessManager.PostOperation:
            if "files" in reply.url().toString():  # Result from /files command:
                if http_status_code == 201:
                    Logger.log("d", "Resource created on OctoPrint instance: %s", reply.header(QNetworkRequest.LocationHeader).toString())
                else:
                    pass  # TODO: Handle errors

                reply.uploadProgress.disconnect(self._onUploadProgress)
                self._progress_message.hide()
                global_container_stack = Application.getInstance().getGlobalContainerStack()
                if global_container_stack and not global_container_stack.getMetaDataEntry("octoprint_auto_print", True):
                    message = Message(catalog.i18nc("@info:status", "Saved to OctoPrint as {1}").format(reply.header(QNetworkRequest.LocationHeader).toString()))
                    message.addAction("open_browser", catalog.i18nc("@action:button", "Open Browser"), "globe", catalog.i18nc("@info:tooltip", "Open browser to OctoPrint."))
                    message.actionTriggered.connect(self._onMessageActionTriggered)
                    message.show()

            elif "job" in reply.url().toString():  # Result from /job command:
                if http_status_code == 204:
                    Logger.log("d", "Octoprint command accepted")
                else:
                    pass  # TODO: Handle errors

        else:
            Logger.log("d", "OctoPrintOutputDevice got an unhandled operation %s", reply.operation())

    def _onUploadProgress(self, bytes_sent, bytes_total):
        if bytes_total > 0:
            progress = bytes_sent / bytes_total * 100
            if progress < 100:
                self._progress_message.setProgress(progress)
            else:
                self._progress_message.hide()
                self._progress_message = Message(i18n_catalog.i18nc("@info:status", "Storing data on OctoPrint"), 0, False, -1)
                self._progress_message.show()
        else:
            self._progress_message.setProgress(0)

    def _onMessageActionTriggered(self, message, action):
        if action == "open_browser":
            QDesktopServices.openUrl(QUrl("http://" + self._address))