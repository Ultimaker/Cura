from UM.i18n import i18nCatalog
from UM.Application import Application
from UM.Logger import Logger
from UM.Signal import signalemitter

from UM.Message import Message

from cura.PrinterOutputDevice import PrinterOutputDevice, ConnectionState

from PyQt5.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkRequest, QNetworkAccessManager
from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtGui import QPixmap

import json

i18n_catalog = i18nCatalog("cura")


##  Network connected (wifi / lan) printer that uses the Ultimaker API
@signalemitter
class NetworkPrinterOutputDevice(PrinterOutputDevice):
    def __init__(self, key, address, info):
        super().__init__(key)
        self._address = address
        self._key = key
        self._info = info

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
        self.setDescription(i18n_catalog.i18nc("@info:tooltip", "Print with WIFI"))
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

        self._progress_message = None
        self._error_message = None

        self._update_timer = QTimer()
        self._update_timer.setInterval(5000)  # TODO; Add preference for update interval
        self._update_timer.setSingleShot(False)
        self._update_timer.timeout.connect(self._update)

        self._camera_image = QPixmap()

    ##  Get the unique key of this machine
    #   \return key String containing the key of the machine.
    def getKey(self):
        return self._key

    def _update(self):
        ## Request 'general' printer data
        url = QUrl("http://" + self._address + self._api_prefix + "printer")
        self._printer_request = QNetworkRequest(url)
        self._printer_reply = self._manager.get(self._printer_request)

        ## Request print_job data
        url = QUrl("http://" + self._address + self._api_prefix + "print_job")
        self._print_job_request = QNetworkRequest(url)
        self._print_job_reply = self._manager.get(self._print_job_request)

        ## Request new image
        url = QUrl("http://" + self._address +":8080/?action=snapshot")
        self._image_request = QNetworkRequest(url)
        self._image_reply = self._manager.get(self._image_request)

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
        self._update_timer.stop()

    def requestWrite(self, node, file_name = None, filter_by_machine = False):
        self._gcode = getattr(Application.getInstance().getController().getScene(), "gcode_list")
        self.startPrint()

    def isConnected(self):
        return self._connection_state != ConnectionState.closed and self._connection_state != ConnectionState.error

    ##  Start requesting data from printer
    def connect(self):
        self.setConnectionState(ConnectionState.connecting)
        self._update()  # Manually trigger the first update, as we don't want to wait a few secs before it starts.
        Logger.log("d", "Connection with printer %s with ip %s started", self._key, self._address)
        self._update_timer.start()

    def getCameraImage(self):
        return self._camera_image

    def startPrint(self):
        if self._progress != 0:
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Printer is still printing. Unable to start a new job."))
            self._error_message.show()
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
                    self.setProgress(progress)

                    self.setTimeElapsed(json_data["time_elapsed"])
                    self.setTimeTotal(json_data["time_total"])

                elif reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) == 404:
                    self.setProgress(0)  # No print job found, so there can't be progress!
            elif "snapshot" in reply.url().toString():  # Status update from image:
                if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) == 200:
                    self._camera_image.loadFromData(reply.readAll())
        elif reply.operation() == QNetworkAccessManager.PostOperation:
            reply.uploadProgress.disconnect(self._onUploadProgress)
            self._progress_message.hide()
        else:
            Logger.log("d", "NetworkPrinterOutputDevice got an unhandled operation %s", reply.operation())

    def _onUploadProgress(self, bytes_sent, bytes_total):
        if bytes_total > 0:
            self._progress_message.setProgress(bytes_sent / bytes_total * 100)
        else:
            self._progress_message.setProgress(0)