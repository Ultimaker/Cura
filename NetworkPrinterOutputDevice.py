import threading
import time
import requests

from UM.i18n import i18nCatalog
from UM.Application import Application
from UM.Logger import Logger

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
        self._thread = None

        self._json_printer_state = None

        self._num_extruders = 2

        self._api_version = "1"
        self._api_prefix = "/api/v" + self._api_version + "/"
        self.setName(key)
        self.setShortDescription(i18n_catalog.i18nc("@action:button", "Print with WIFI"))
        self.setDescription(i18n_catalog.i18nc("@info:tooltip", "Print with WIFI"))
        self.setIconName("print")

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
        pass

    def close(self):
        self._connection_state == ConnectionState.closed
        self._thread = None

    def requestWrite(self, node, file_name = None):
        self._file = getattr(Application.getInstance().getController().getScene(), "gcode_list")
        self.startPrint()

    def isConnected(self):
        return self._connection_state != ConnectionState.closed and self._connection_state != ConnectionState.error

    ##  Start the polling thread.
    def connect(self):
        if self._thread is None:
            self.setConnectionState(ConnectionState.connecting)
            self._thread = threading.Thread(target = self._update)
            self._thread.daemon = True
            self._thread.start()

    def getCameraImage(self):
        pass #Do Nothing

    def startPrint(self):
        try:
            result = self._httpPost("print_job", self._file)
        except Exception as e:
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