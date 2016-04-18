import threading
import time
import requests

from UM.i18n import i18nCatalog
from UM.Signal import Signal
from UM.Application import Application
from UM.Logger import Logger

from cura.PrinterOutputDevice import PrinterOutputDevice, ConnectionState

i18n_catalog = i18nCatalog("cura")


class NetworkPrinterOutputDevice(PrinterOutputDevice):
    def __init__(self, key, address, info):
        super().__init__(key)
        self._address = address
        self._key = key
        self._info = info
        self._http_lock = threading.Lock()
        self._http_connection = None
        self._file = None
        self._do_update = True
        self._thread = None

        self._json_printer_state = None

        self._api_version = "1"
        self._api_prefix = "/api/v" + self._api_version + "/"
        self.setName(key)
        self.setShortDescription(i18n_catalog.i18nc("@action:button", "Print with WIFI"))
        self.setDescription(i18n_catalog.i18nc("@info:tooltip", "Print with WIFI"))
        self.setIconName("print")

    def getKey(self):
        return self._key

    def _update(self):
        while self._connection_state == ConnectionState.connected or self._connection_state == ConnectionState.busy:
            try:
                reply = self._httpGet("printer")
                if reply.status_code == 200:
                    self._json_printer_state = reply.json()
                else:
                    self.setConnectionState(ConnectionState.error)
            except:
                self.setConnectionState(ConnectionState.error)
            time.sleep(1)  # Poll every second for printer state.

    def close(self):
        self._do_update = False
        self._is_connected = False

    def requestWrite(self, node, file_name = None):
        self._file = getattr( Application.getInstance().getController().getScene(), "gcode_list")
        self.startPrint()

    ##  Start the polling thread.
    def connect(self):
        if self._thread is None:
            self._do_update = True
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
            if isinstance(file_data, list): # in case a list with strings is sent
                single_string_file_data = ""
                for line in file_data:
                    single_string_file_data += line
                files_dict = {"file":("test.gcode", single_string_file_data)}
            else:
                files_dict = {"file":("test.gcode", file_data)}

            return requests.post("http://" + self._address + self._api_prefix + path, files = files_dict)