import threading
import time
import requests

from UM.i18n import i18nCatalog
from UM.Application import Application
from UM.Logger import Logger

from UM.Message import Message

from cura.PrinterOutputDevice import PrinterOutputDevice, ConnectionState

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

        self._progress_message = None
        self._error_message = None

    def getKey(self):
        return self._key

    def _update(self):
        Logger.log("d", "Update thread of printer with key %s and ip %s started", self._key, self._address)
        while self.isConnected():
            try:
                reply = self._httpGet("printer")
                if reply.status_code == 200:
                    self._json_printer_state = reply.json()
                    try:
                        self._spliceJSONData()
                    except:
                        # issues with json parsing should not break by definition TODO: Check in what cases it should fail.
                        pass
                    if self._connection_state == ConnectionState.connecting:
                        # First successful response, so we are now "connected"
                        self.setConnectionState(ConnectionState.connected)
                else:
                    Logger.log("w", "Got http status code %s while trying to request data.", reply.status_code)
                    self.setConnectionState(ConnectionState.error)
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

    def close(self):
        self._connection_state == ConnectionState.closed
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
        pass #Do Nothing

    def startPrint(self):
        try:
            self._progress_message = Message(i18n_catalog.i18nc("@info:status", "Sending data to printer"), 0, False, -1)
            self._progress_message.show()
            #TODO: Create a job that handles this! (As it currently locks up UI)
            result = self._httpPost("print_job", self._file)
            self._progress_message.hide()
            if result.status_code == 200:
                pass
        except IOError:
            self._progress_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Unable to send data printer. Is another job still active?"))
            self._error_message.show()
        except Exception as e:
            self._progress_message.hide()
            Logger.log("e" , "An exception occured in wifi connection: %s" % str(e))

    def _httpGet(self, path):
        return requests.get("http://" + self._address + self._api_prefix + path)

    def _httpPost(self, path, file_data):
        with self._http_lock:
            files_dict = {}
            if isinstance(file_data, list):  # in case a list with strings is sent
                single_string_file_data = ""
                for line in file_data:
                    single_string_file_data += line
                files_dict = {"file":("test.gcode", single_string_file_data)}
            else:
                files_dict = {"file":("test.gcode", file_data)}

            return requests.post("http://" + self._address + self._api_prefix + path, files = files_dict)