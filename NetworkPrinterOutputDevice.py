import threading
import time
import requests

from UM.i18n import i18nCatalog
from UM.Application import Application
from UM.Logger import Logger

from UM.Message import Message

from cura.PrinterOutputDevice import PrinterOutputDevice, ConnectionState

from PyQt5.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkRequest, QNetworkAccessManager
from PyQt5.QtCore import QUrl

i18n_catalog = i18nCatalog("cura")


##  Network connected (wifi / lan) printer that uses the Ultimaker API
class NetworkPrinterOutputDevice(PrinterOutputDevice):
    def __init__(self, key, address, info):
        super().__init__(key)
        self._address = address
        self._key = key
        self._info = info
        self._http_lock = threading.Lock()
        self._http_connection = None
        self._file = None
        self._update_thread = None

        self._json_printer_state = None

        self._num_extruders = 2

        self._api_version = "1"
        self._api_prefix = "/api/v" + self._api_version + "/"
        self.setName(key)
        self.setShortDescription(i18n_catalog.i18nc("@action:button", "Print with WIFI"))
        self.setDescription(i18n_catalog.i18nc("@info:tooltip", "Print with WIFI"))
        self.setIconName("print")

        self._manager = QNetworkAccessManager()
        self._manager.finished.connect(self._onFinished)

        ##  Hack to ensure that the qt networking stuff isn't garbage collected (unless we want it to)
        self._qt_request = None
        self._qt_reply = None
        self._qt_multi_part = None
        self._qt_part = None

        self._progress_message = None
        self._error_message = None

    def getKey(self):
        return self._key

    def _update(self):
        Logger.log("d", "Update thread of printer with key %s and ip %s started", self._key, self._address)
        while self.isConnected():
            try:
                printer_reply = self._httpGet("printer")
                if printer_reply.status_code == 200:
                    self._json_printer_state = printer_reply.json()
                    try:
                        self._spliceJSONData()
                    except:
                        # issues with json parsing should not break by definition TODO: Check in what cases it should fail.
                        pass
                    if self._connection_state == ConnectionState.connecting:
                        # First successful response, so we are now "connected"
                        self.setConnectionState(ConnectionState.connected)
                else:
                    Logger.log("w", "Got http status code %s while trying to request data.", printer_reply.status_code)
                    self.setConnectionState(ConnectionState.error)

                print_job_reply = self._httpGet("print_job")
                if print_job_reply.status_code != 404:
                    self.setProgress(print_job_reply.json()["progress"])
                else:
                    self.setProgress(0)
                
            except Exception as e:
                self.setConnectionState(ConnectionState.error)
                Logger.log("w", "Exception occured while connecting; %s", str(e))
            time.sleep(2)  # Poll every second for printer state.
        Logger.log("d", "Update thread of printer with key %s and ip %s stopped with state: %s", self._key, self._address, self._connection_state)

    ##  Convenience function that gets information from the recieved json data and converts it to the right internal
    #   values / variables
    def _spliceJSONData(self):
        # Check for hotend temperatures
        for index in range(0, self._num_extruders - 1):
            temperature = self._json_printer_state["heads"][0]["extruders"][index]["hotend"]["temperature"]["current"]
            self._setHotendTemperature(index, temperature)

        bed_temperature = self._json_printer_state["bed"]["temperature"]
        self._setBedTemperature(bed_temperature)

        head_x = self._json_printer_state["heads"][0]["position"]["x"]
        head_y = self._json_printer_state["heads"][0]["position"]["y"]
        head_z = self._json_printer_state["heads"][0]["position"]["z"]
        self._updateHeadPosition(head_x, head_y, head_z)

    def close(self):
        self._connection_state == ConnectionState.closed
        if self._update_thread != None:
            self._update_thread.join()
            self._update_thread = None

    def requestWrite(self, node, file_name = None, filter_by_machine = False):
        self._file = getattr(Application.getInstance().getController().getScene(), "gcode_list")
        self.startPrint()

    def isConnected(self):
        return self._connection_state != ConnectionState.closed and self._connection_state != ConnectionState.error

    ##  Start the polling thread.
    def connect(self):
        if self._update_thread is None:
            self.setConnectionState(ConnectionState.connecting)
            self._update_thread = threading.Thread(target = self._update)
            self._update_thread.daemon = True
            self._update_thread.start()

    def getCameraImage(self):
        pass  # TODO: This still needs to be implemented (we don't have a place to show it now anyway)

    def startPrint(self):
        if self._progress != 0:
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Printer is still printing. Unable to start a new job."))
            self._error_message.show()
            return
        try:
            self._progress_message = Message(i18n_catalog.i18nc("@info:status", "Sending data to printer"), 0, False, -1)
            self._progress_message.show()

            single_string_file_data = ""
            for line in self._file:
                single_string_file_data += line

            ##  TODO: Use correct file name (we use placeholder now)
            file_name = "test.gcode"

            ##  Create multi_part request
            self._qt_multi_part = QHttpMultiPart(QHttpMultiPart.FormDataType)

            ##  Create part (to be placed inside multipart)
            self._qt_part = QHttpPart()
            self._qt_part.setHeader(QNetworkRequest.ContentDispositionHeader,
                           "form-data; name=\"file\"; filename=\"%s\"" % file_name)
            self._qt_part.setBody(single_string_file_data)
            self._qt_multi_part.append(self._qt_part)

            url =  "http://" + self._address + self._api_prefix + "print_job"

            url_2 = "http://10.180.0.53/api/v1/print_job"
            ##  Create the QT request
            self._qt_request = QNetworkRequest(QUrl("http://10.180.0.53/api/v1/print_job"))

            ##  Post request + data
            self._qt_reply = self._manager.post(self._qt_request, self._qt_multi_part)
            self._qt_reply.uploadProgress.connect(self._onUploadProgress)

        except IOError:
            self._progress_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Unable to send data to printer. Is another job still active?"))
            self._error_message.show()
        except Exception as e:
            self._progress_message.hide()
            Logger.log("e" , "An exception occured in network connection: %s" % str(e))

    def _onFinished(self, reply):
        reply.uploadProgress.disconnect(self._onUploadProgress)
        self._progress_message.hide()

    def _onUploadProgress(self, bytes_sent, bytes_total):
        self._progress_message.setProgress(bytes_sent / bytes_total * 100)

    def _httpGet(self, path):
        return requests.get("http://" + self._address + self._api_prefix + path)