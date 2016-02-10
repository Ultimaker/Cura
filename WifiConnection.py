from UM.OutputDevice.OutputDevice import OutputDevice
from UM.OutputDevice import OutputDeviceError
import threading
import http.client as httpclient
import urllib
import json
import time
import base64

from . import HttpUploadDataStream
from UM.i18n import i18nCatalog
from UM.Signal import Signal, SignalEmitter
from UM.Application import Application
from UM.Logger import Logger
i18n_catalog = i18nCatalog("cura")

class WifiConnection(OutputDevice, SignalEmitter):
    def __init__(self, address, info):
        super().__init__(address)
        self._address = address
        self._info = info
        self._http_lock = threading.Lock()
        self._http_connection = None
        self._file = None
        self._do_update = True
        self._thread = None
        self._state = None
        self._is_connected = False
        self.connect()
        self.setName(address)
        self.setShortDescription(i18n_catalog.i18nc("@action:button", "Print with WIFI"))
        self.setDescription(i18n_catalog.i18nc("@info:tooltip", "Print with WIFI"))
        self.setIconName("print")

    connectionStateChanged = Signal()

    def isConnected(self):
        return self._is_connected

    def setConnectionState(self, state):
        print("setting connection state: " , self._address, " " , state)
        if state != self._is_connected:
            self._is_connected = state
            self.connectionStateChanged.emit(self._address)
        else:
             self._is_connected = state

    def _update(self):
        while self._thread:
            state_reply = self._httpRequest('GET', '/api/v1/printer/state')
            if state_reply is not None:
                self._state = state_reply
                if not self._is_connected:
                    self.setConnectionState(True)
            else:
                self._state = {'state': 'CONNECTION_ERROR'}
                self.setConnectionState(False)
            time.sleep(1)

    def close(self):
        self._do_update = False
        self._is_connected = False

    def requestWrite(self, node):
        self._file = getattr( Application.getInstance().getController().getScene(), "gcode_list")
        self.startPrint()

    #Open the active connection to the printer so we can send commands
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
            result = self._httpRequest('POST', '/api/v1/printer/print_upload', {'print_name': 'Print from Cura', 'parameters':''}, {'file': ('file.gcode', self._file)})
            print(result.get('success',False))
            #result = self._httpRequest('POST', '/api/v1/printer/print_upload', {'print_name': 'Print from Cura'})
        except Exception as e:
            Logger.log('e' , 'An exception occured in wifi connection: ' , e)

    def _httpRequest(self, method, path, post_data = None, files = None):
        with self._http_lock:
            self._http_connection = httpclient.HTTPConnection(self._address, timeout = 30)
            try:
                if files is not None:
                    boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'
                    s = HttpUploadDataStream.HttpUploadDataStream()
                    for k, v in files.items():
                        filename = v[0]
                        file_contents = v[1]
                        s.write('--%s\r\n' % (boundary))
                        s.write('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (k, filename))
                        s.write('Content-Type: application/octet-stream\r\n')
                        s.write('Content-Transfer-Encoding: binary\r\n')
                        s.write('\r\n')

                        if file_contents is not None:
                            for line in file_contents:
                                s.write(str(line))

                        s.write('\r\n')

                    for k, v in post_data.items():
                        s.write('--%s\r\n' % (boundary))
                        s.write('Content-Disposition: form-data; name="%s"\r\n' % (k))
                        s.write('\r\n')
                        s.write(str(v))
                        s.write('\r\n')
                    s.write('--%s--\r\n' % (boundary))

                    self._http_connection.request(method, path, s, {"Content-type": "multipart/form-data; boundary=%s" % (boundary), "Content-Length": len(s)})
                elif post_data is not None:

                    self._http_connection.request(method, path, urllib.urlencode(post_data), {"Content-type": "application/x-www-form-urlencoded", "User-Agent": "Cura Doodle3D connection"})
                else:
                    self._http_connection.request(method, path, headers={"Content-type": "application/x-www-form-urlencoded", "User-Agent": "Cura Doodle3D connection"})
            except IOError:
                self._http_connection.close()
                return None
            except Exception as e:
                self._http_connection.close()
                return None

            try:
                response = self._http_connection.getresponse()
                response_text = response.read()
            except IOError:
                self._http_connection.close()
                return None
            try:
                response = json.loads(response_text.decode("utf-8"))
            except ValueError:
                self._http_connection.close()
                return None
            self._http_connection.close()
            return response
