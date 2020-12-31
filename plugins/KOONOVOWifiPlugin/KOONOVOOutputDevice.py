# coding=utf-8
from UM.i18n import i18nCatalog
from UM.Application import Application
from UM.Logger import Logger
from UM.Signal import signalemitter
from UM.Message import Message
from cura.PrinterOutputDevice import PrinterOutputDevice, ConnectionState
from cura.CuraApplication import CuraApplication

from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice, AuthState
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel
from UM.PluginRegistry import PluginRegistry
from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.Models.SettingDefinitionsModel import SettingDefinitionsModel

from PyQt5.QtQuick import QQuickView
from PyQt5.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton

from cura.PrinterOutput.GenericOutputController import GenericOutputController

from PyQt5.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkRequest, QNetworkAccessManager, QNetworkReply, QTcpSocket
from PyQt5.QtCore import QUrl, QTimer, pyqtSignal, pyqtProperty, pyqtSlot, QCoreApplication, Qt, QObject
from queue import Queue

from . import utils

import UM

import json
import os.path
import time
import base64
import sys
from enum import IntEnum
from UM.Preferences import Preferences

from typing import cast, Any, Callable, Dict, List, Optional, Union, TYPE_CHECKING
if TYPE_CHECKING:
    from UM.Scene.SceneNode import SceneNode #For typing.
    from UM.FileHandler.FileHandler import FileHandler #For typing.

i18n_catalog = i18nCatalog("cura")

class UnifiedConnectionState(IntEnum):
    try:
        Closed = ConnectionState.Closed
        Connecting = ConnectionState.Connecting
        Connected = ConnectionState.Connected
        Busy = ConnectionState.Busy
        Error = ConnectionState.Error
    except AttributeError:
        Closed = ConnectionState.closed          # type: ignore
        Connecting = ConnectionState.connecting  # type: ignore
        Connected = ConnectionState.connected    # type: ignore
        Busy = ConnectionState.busy              # type: ignore
        Error = ConnectionState.error            # type: ignore

@signalemitter
class KOONOVOOutputDevice(NetworkedPrinterOutputDevice):
    def __init__(self, instance_id: str, address: str, properties: dict, **kwargs) -> None:
        super().__init__(device_id = instance_id, address = address, properties = properties, **kwargs)
        self._address = address
        self._port = 8080
        self._key = instance_id
        self._properties = properties

        self._target_bed_temperature = 0
        self._num_extruders = 1
        self._hotend_temperatures = [0] * self._num_extruders
        self._target_hotend_temperatures = [0] * self._num_extruders      

        self._application = CuraApplication.getInstance()
        if self._application.getVersion().split(".")[0] == "4":
            self._monitor_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MonitorItem4x.qml")
        else:
            self._monitor_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MonitorItem.qml")

        self.setPriority(3)  # Make sure the output device gets selected above local file output and Octoprint XD
        self._active_machine = CuraApplication.getInstance().getMachineManager().activeMachine
        self.setName(instance_id)
        self.setShortDescription(i18n_catalog.i18nc("@action:button", "Print over TFT"))
        self.setDescription(i18n_catalog.i18nc("@properties:tooltip", "Print over TFT"))
        self.setIconName("print")
        self.setConnectionText(i18n_catalog.i18nc("@info:status", "Connected to TFT on {0}").format(self._key))
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerChanged)

        self._socket = None
        self._gl = None
        self._command_queue = Queue()
        self._isPrinting = False
        self._isPause = False
        self._isSending = False
        self._gcode = None
        self._isConnect = False
        self._printing_filename = ""
        self._printing_progress = 0
        self._printing_time = 0
        self._start_time = 0
        self._pause_time = 0
        self.last_update_time = 0
        self.angle = 10
        self._connection_state_before_timeout = None
        self._sdFileList = False
        self.sdFiles = []
        self._mdialog = None
        self._mfilename = None
        self._uploadpath = ''

        self._settings_reply = None
        self._printer_reply = None
        self._job_reply = None
        self._command_reply = None
        self._screenShot = None

        self._image_reply = None
        self._stream_buffer = b""
        self._stream_buffer_start_index = -1

        self._post_reply = None
        self._post_multi_part = None
        self._post_part = None
        self._last_file_name = None
        self._last_file_path = None

        self._progress_message = None
        self._error_message = None
        self._connection_message = None
        self.__additional_components_view = None

        self._ischanging = False

        self._update_timer = QTimer()
        self._update_timer.setInterval(2000)  # TODO; Add preference for update interval
        self._update_timer.setSingleShot(False)
        self._update_timer.timeout.connect(self._update)

        self._manager = QNetworkAccessManager()
        self._manager.finished.connect(self._onRequestFinished)

        self._preheat_timer = QTimer()
        self._preheat_timer.setSingleShot(True)
        self._preheat_timer.timeout.connect(self.cancelPreheatBed)
        self._exception_message = None
        self._output_controller = GenericOutputController(self)
        self._number_of_extruders = 1
        self._camera_url = ""
        # Application.getInstance().getOutputDeviceManager().outputDevicesChanged.connect(self._onOutputDevicesChanged)
        CuraApplication.getInstance().getCuraSceneController().activeBuildPlateChanged.connect(self.CreateKOONOVOController)


    def _onOutputDevicesChanged(self):
        Logger.log("d", "KOONOVO _onOutputDevicesChanged")

    def connect(self):
        if self._socket is not None:
            self._socket.close()
            self._socket.abort()
            self._socket = None
        self._socket = QTcpSocket()
        # Logger.log("d","self._socket.connectToHost %s" % self._address)
        # Logger.log("d","self._socket.connectToHost %s" % self._port)
        self._socket.connectToHost(self._address, self._port)
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        name1 = "Print over " + global_container_stack.getName()
        if CuraApplication.getInstance().getPreferences().getValue("general/language") == "zh_CN":
            name1 = "WIFI传输打印"
        else:
            name1 = "Print over " + global_container_stack.getName()
        self.setShortDescription(i18n_catalog.i18nc("@action:button", name1))
        self.setDescription(i18n_catalog.i18nc("@properties:tooltip", name1))
        Logger.log("d", "KOONOVO socket connecting ")
        self._socket.waitForConnected(2000)
        # Logger.log("d","self._socket.connectToHost self._socket.state() %s" % self._socket.state())
        # if self._socket.state() == 0 or self._socket.state() == 1:
        #     self.connect()
        # else:
        self.setConnectionState(cast(ConnectionState, UnifiedConnectionState.Connecting))
        self._setAcceptsCommands(True)
        self._socket.readyRead.connect(self.on_read)
        preferences = Application.getInstance().getPreferences()
        preferences.addPreference("KOONOVOwifi/stopupdate", "False")
        self._update_timer.start()

    def getProperties(self):
        return self._properties

    @pyqtSlot(str, result=str)
    def getProperty(self, key):
        key = key.encode("utf-8")
        if key in self._properties:
            return self._properties.get(key, b"").decode("utf-8")
        else:
            return ""

    @pyqtSlot(result=str)
    def getKey(self):
        return self._key

    @pyqtProperty(str, constant=True)
    def address(self):
        return self._properties.get(b"address", b"").decode("utf-8")

    @pyqtProperty(str, constant=True)
    def name(self):
        return self._properties.get(b"name", b"").decode("utf-8")

    @pyqtProperty(str, constant=True)
    def firmwareVersion(self):
        return self._properties.get(b"firmware_version", b"").decode("utf-8")

    @pyqtProperty(str, constant=True)
    def ipAddress(self):
        return self._address

    @pyqtSlot(float, float)
    def preheatBed(self, temperature, duration):
        self._setTargetBedTemperature(temperature)
        if duration > 0:
            self._preheat_timer.setInterval(duration * 1000)
            self._preheat_timer.start()
        else:
            self._preheat_timer.stop()

    @pyqtSlot()
    def cancelPreheatBed(self):
        self._setTargetBedTemperature(0)
        self._preheat_timer.stop()

    @pyqtSlot()
    def printtest(self):
        self.sendCommand("M104 S0\r\n M140 S0\r\n M106 S255")

    @pyqtSlot()
    def openfan(self):
        self.sendCommand("M106 S255")

    @pyqtSlot()
    def closefan(self):
        self.sendCommand("M106 S0")

    @pyqtSlot()
    def unlockmotor(self):
        self.sendCommand("M84")

    @pyqtSlot()
    def e0down(self):
        if not self._isPrinting:
            self.sendCommand("T0\r\n G91\r\n G1 E10 F1000\r\n G90")
        else:
            if self._error_message is not None:
                self._error_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Error: printing can not send"))
            self._error_message.show()

    @pyqtSlot()
    def e0up(self):
        if not self._isPrinting:
            self.sendCommand("T0\r\n G91\r\n G1 E-10 F1000\r\n G90")
        else:
            if self._error_message is not None:
                self._error_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Error: printing can not send"))
            self._error_message.show()

    @pyqtSlot()
    def e1down(self):
        if not self._isPrinting:
            self.sendCommand("T1\r\n G91\r\n G1 E10 F1000\r\n G90")
        else:
            if self._error_message is not None:
                self._error_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Error: printing can not send"))
            self._error_message.show()

    @pyqtSlot()
    def e1up(self):
        if not self._isPrinting:
            self.sendCommand("T1\r\n G91\r\n G1 E-10 F1000\r\n G90")
        else:
            if self._error_message is not None:
                self._error_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Error: printing can not send"))
            self._error_message.show()

    @pyqtSlot()
    def printer_E_num(self):
        return self._number_of_extruders

    @pyqtSlot()
    def printer_state(self):
        if len(self._printers) <= 0:
            return "offline"
        return self.printers[0].state

    @pyqtSlot()
    def isprinterprinting(self):
        if self._isPrinting:
            return "true"
        return "false"

    @pyqtSlot()
    def selectfile(self):
        if self._last_file_name:
            return True
        else:
            return False

    @pyqtSlot(str)
    def deleteSDFiles(self, filename):
        # filename = "几何图.gcode"
        self._sendCommand("M30 1:/" + filename)
        if filename in self.sdFiles:
            self.sdFiles.remove(filename)
        self._sendCommand("M20")

    @pyqtSlot(str)
    def printSDFiles(self, filename):
        self._sendCommand("M23 "+filename)
        self._sendCommand("M24")

    @pyqtSlot()
    def selectFileToUplload(self):
        preferences = Application.getInstance().getPreferences()
        preferences.addPreference("KOONOVOwifi/autoprint", "True")
        preferences.addPreference("KOONOVOwifi/savepath", "")
        # if preferences.getValue("KOONOVOwifi/uploadingfile"):
        if self._progress_message:
            if self._error_message is not None:
                self._error_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Error: Another file is uploading, please try later."))
            self._error_message.show()
        else:
            filename,_ = QFileDialog.getOpenFileName(None, "choose file", preferences.getValue("KOONOVOwifi/savepath"), "Gcode(*.gcode;*.g;*.goc)")
            preferences.setValue("KOONOVOwifi/savepath", filename)
            self._uploadpath = filename
            if ".g" in filename.lower():
                Logger.log("d", "selectfile:"+filename)
                if filename[filename.rfind("/")+1:] in self.sdFiles:
                    if self._mdialog:
                        self._mdialog.close()
                    self._mdialog = QDialog()
                    self._mdialog.setWindowTitle("The "+filename[filename.rfind("/")+1:]+" file already exists.")
                    dialogvbox = QVBoxLayout()
                    dialoghbox = QHBoxLayout()
                    yesbtn = QPushButton("yes")
                    nobtn = QPushButton("no")
                    yesbtn.clicked.connect(lambda : self.uploadfunc(filename))
                    nobtn.clicked.connect(self.closeMDialog)
                    content = QLabel("The "+filename[filename.rfind("/")+1:]+" file already exists. Do you want to upload it?")
                    self._mfilename = QLineEdit()
                    self._mfilename.setText(filename[filename.rfind("/")+1:])
                    dialoghbox.addWidget(yesbtn)
                    dialoghbox.addWidget(nobtn)
                    dialogvbox.addWidget(content)
                    dialogvbox.addWidget(self._mfilename)
                    dialogvbox.addLayout(dialoghbox)
                    self._mdialog.setLayout(dialogvbox)
                    self._mdialog.exec_()
                    return
                if len(filename[filename.rfind("/")+1:]) >= 30:
                    if self._mdialog:
                        self._mdialog.close()
                    self._mdialog = QDialog()
                    self._mdialog.setWindowTitle("File name is too long to upload, please rename it.")
                    dialogvbox = QVBoxLayout()
                    dialoghbox = QHBoxLayout()
                    yesbtn = QPushButton("yes")
                    nobtn = QPushButton("no")
                    yesbtn.clicked.connect(lambda : self.renameupload(filename))
                    nobtn.clicked.connect(self.closeMDialog)
                    content = QLabel("File name is too long to upload, please rename it.")
                    self._mfilename = QLineEdit()
                    self._mfilename.setText(filename[filename.rfind("/")+1:])
                    dialoghbox.addWidget(yesbtn)
                    dialoghbox.addWidget(nobtn)
                    dialogvbox.addWidget(content)
                    dialogvbox.addWidget(self._mfilename)
                    dialogvbox.addLayout(dialoghbox)
                    self._mdialog.setLayout(dialogvbox)
                    self._mdialog.exec_()
                    return
                if self.is_contains_chinese(filename[filename.rfind("/")+1:]):
                    if self._mdialog:
                        self._mdialog.close()
                    self._mdialog = QDialog()
                    self._mdialog.setWindowTitle("File name can not include chinese, please rename it.")
                    dialogvbox = QVBoxLayout()
                    dialoghbox = QHBoxLayout()
                    yesbtn = QPushButton("yes")
                    nobtn = QPushButton("no")
                    yesbtn.clicked.connect(lambda : self.renameupload(filename))
                    nobtn.clicked.connect(self.closeMDialog)
                    content = QLabel("File name can not include chinese, please rename it.")
                    self._mfilename = QLineEdit()
                    self._mfilename.setText(filename[filename.rfind("/")+1:])
                    dialoghbox.addWidget(yesbtn)
                    dialoghbox.addWidget(nobtn)
                    dialogvbox.addWidget(content)
                    dialogvbox.addWidget(self._mfilename)
                    dialogvbox.addLayout(dialoghbox)
                    self._mdialog.setLayout(dialogvbox)
                    self._mdialog.exec_()
                    return
                if self.isBusy():
                    if self._exception_message:
                        self._exception_message.hide()
                    self._exception_message = Message(i18n_catalog.i18nc("@info:status", "File cannot be transferred during printing."))
                    self._exception_message.show()
                    return
                self.uploadfunc(filename)
    
    def is_contains_chinese(self,strs):
        #检验是否含有中文字符
        # Logger.log("d", "is_contains_chinese---filename==: %s" % str(strs))
        # for _char in strs:
        #     if '\u4e00' <= _char <= '\u9fa5':
        #         return True
        return False

    def closeMDialog(self):
        if self._mdialog:
            self._mdialog.close()
    
    def renameupload(self, filename):
        if self._mfilename and ".g" in self._mfilename.text().lower():
            filename = filename[:filename.rfind("/")]+"/"+self._mfilename.text()
            # Logger.log("d", "renameupload---filename==: %s" % str(filename))
            if self._mfilename.text() in self.sdFiles:
                if self._mdialog:
                    self._mdialog.close()
                self._mdialog = QDialog()
                self._mdialog.setWindowTitle("The "+filename[filename.rfind("/")+1:]+" file already exists.")
                dialogvbox = QVBoxLayout()
                dialoghbox = QHBoxLayout()
                yesbtn = QPushButton("yes")
                nobtn = QPushButton("no")
                yesbtn.clicked.connect(lambda : self.uploadfunc(filename))
                nobtn.clicked.connect(self.closeMDialog)
                content = QLabel("The "+filename[filename.rfind("/")+1:]+" file already exists. Do you want to upload it?")
                self._mfilename = QLineEdit()
                self._mfilename.setText(filename[filename.rfind("/")+1:])
                dialoghbox.addWidget(yesbtn)
                dialoghbox.addWidget(nobtn)
                dialogvbox.addWidget(content)
                dialogvbox.addWidget(self._mfilename)
                dialogvbox.addLayout(dialoghbox)
                self._mdialog.setLayout(dialogvbox)
                self._mdialog.exec_()
                return
            if len(filename[filename.rfind("/")+1:]) >= 30:
                if self._mdialog:
                    self._mdialog.close()
                self._mdialog = QDialog()
                self._mdialog.setWindowTitle("File name is too long to upload, please rename it.")
                dialogvbox = QVBoxLayout()
                dialoghbox = QHBoxLayout()
                yesbtn = QPushButton("yes")
                nobtn = QPushButton("no")
                yesbtn.clicked.connect(lambda : self.renameupload(filename))
                nobtn.clicked.connect(self.closeMDialog)
                content = QLabel("File name is too long to upload, please rename it.")
                self._mfilename = QLineEdit()
                self._mfilename.setText(filename[filename.rfind("/")+1:])
                dialoghbox.addWidget(yesbtn)
                dialoghbox.addWidget(nobtn)
                dialogvbox.addWidget(content)
                dialogvbox.addWidget(self._mfilename)
                dialogvbox.addLayout(dialoghbox)
                self._mdialog.setLayout(dialogvbox)
                self._mdialog.exec_()
                return
            if self.is_contains_chinese(filename[filename.rfind("/")+1:]):
                if self._mdialog:
                    self._mdialog.close()
                self._mdialog = QDialog()
                self._mdialog.setWindowTitle("File name can not include chinese, please rename it.")
                dialogvbox = QVBoxLayout()
                dialoghbox = QHBoxLayout()
                yesbtn = QPushButton("yes")
                nobtn = QPushButton("no")
                yesbtn.clicked.connect(lambda : self.renameupload(filename))
                nobtn.clicked.connect(self.closeMDialog)
                content = QLabel("File name can not include chinese, please rename it.")
                self._mfilename = QLineEdit()
                self._mfilename.setText(filename[filename.rfind("/")+1:])
                dialoghbox.addWidget(yesbtn)
                dialoghbox.addWidget(nobtn)
                dialogvbox.addWidget(content)
                dialogvbox.addWidget(self._mfilename)
                dialogvbox.addLayout(dialoghbox)
                self._mdialog.setLayout(dialogvbox)
                self._mdialog.exec_()
                return
            if self.isBusy():
                if self._exception_message:
                    self._exception_message.hide()
                self._exception_message = Message(i18n_catalog.i18nc("@info:status", "File cannot be transferred during printing."))
                self._exception_message.show()
                return
            self._mdialog.close()
            # preferences = Application.getInstance().getPreferences()
            # if preferences.getValue("KOONOVOwifi/uploadingfile"):
            if self._progress_message:
                if self._error_message is not None:
                    self._error_message.hide()
                self._error_message = Message(i18n_catalog.i18nc("@info:status", "Error: Another file is uploading, please try later."))
                self._error_message.show()
            else:
                self.uploadfunc(filename)
        
        
    
    def uploadfunc(self, filename):
        if self._mdialog:
            self._mdialog.close()
        preferences = Application.getInstance().getPreferences()
        if self._progress_message:
            if self._error_message is not None:
                self._error_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Error: Another file is uploading, please try later."))
            self._error_message.show()
        else:
            preferences.addPreference("KOONOVOwifi/autoprint", "True")
            preferences.addPreference("KOONOVOwifi/savepath", "")
            # preferences.addPreference("KOONOVOwifi/uploadingfile", "True")
            self._update_timer.stop()
            self._isSending = True
            self._preheat_timer.stop()
            single_string_file_data = ""
            try:
                f = open(self._uploadpath, "r", encoding=sys.getfilesystemencoding())
                single_string_file_data = f.read()
                # Logger.log("d", "single_string_file_data: %s" % str(single_string_file_data))
                file_name = filename[filename.rfind("/")+1:]
                # Logger.log("d", "file_namefile_name: %s" % str(file_name))
                self._last_file_name = filename[filename.rfind("/")+1:]
                # self._progress_message = Message(i18n_catalog.i18nc("@info:status", "Sending data to printer"), 0, False, -1,
                #                             i18n_catalog.i18nc("@info:title", "Sending Data"), option_text=i18n_catalog.i18nc("@label", "Print jobs")
                #                             , option_state=preferences.getValue("KOONOVOwifi/autoprint"))
                name0 = "Print Jobs"
                name1 = "Uploading print job to printer"
                name2 = "Sending Print Job"
                namecancel = "Cancel"
                if self._application.getPreferences().getValue("general/language") == "zh_CN":
                    name0 = "传输完成之后，立即打印。"
                    name1 = "正在上传打印文件到打印机"
                    name2 = "正在发送打印文件"
                    namecancel = "取消"
                else:
                    name0 = "Print Jobs"
                    name1 = "Uploading print job to printer"
                    name2 = "Sending Print Job"
                    namecancel = "Cancel"
                    
                self._progress_message = Message(name1, 0, False, -1,
                                            name2, option_text=name0
                                            , option_state=preferences.getValue("KOONOVOwifi/autoprint"))
                self._progress_message.addAction("Cancel", namecancel, None, "")
                self._progress_message.actionTriggered.connect(self._cancelSendGcode)
                self._progress_message.optionToggled.connect(self._onOptionStateChanged)
                self._progress_message.show()
                self._post_multi_part = QHttpMultiPart(QHttpMultiPart.FormDataType)
                self._post_part = QHttpPart()
                # file_name = file_name.encode(sys.getfilesystemencoding())
                # Logger.log("e", "sys.getfilesystemencoding(): %s" % str(sys.getfilesystemencoding()))
                # Logger.log("d", "file_namefile_name222: %s" % str(file_name.encode("utf-8")))
                # Logger.log("d", "QUrl.toPercentEncoding(): %s" % str(QUrl.toPercentEncoding(file_name)))
                self._post_part.setHeader(QNetworkRequest.ContentDispositionHeader,
                                        "form-data; name=\"file\"; filename=\"%s\"" % file_name)
                self._post_part.setBody(single_string_file_data.encode())
                self._post_multi_part.append(self._post_part)
                post_request = QNetworkRequest(QUrl("http://%s/upload?X-Filename=%s" % (self._address, file_name)))
                # post_request = QNetworkRequest(QUrl("http://%s/upload?X-Filename=%s" % (self._address, QUrl.toPercentEncoding(file_name))))
                # post_request = QNetworkRequest(QUrl("http://%s/upload?X-Filename=%s" % (self._address, "%E5%87%A0%E4%BD%95%E4%BD%93.gcode")))
                post_request.setRawHeader(b'Content-Type', b'application/octet-stream')
                # post_request.setRawHeader(b'Content-Type', b'application/x-www-form-urlencoded')
                post_request.setRawHeader(b'Connection', b'keep-alive')
                self._post_reply = self._manager.post(post_request, self._post_multi_part)
                self._post_reply.uploadProgress.connect(self._onUploadProgress)
                self._post_reply.sslErrors.connect(self._onUploadError)
                self._gcode = None
            except IOError as e:
                Logger.log("e", "An exception occurred in network connection: %s" % str(e))
                # preferences.setValue("KOONOVOwifi/uploadingfile", "False")
                self._progress_message.hide()
                self._progress_message = None
                self._error_message = Message(i18n_catalog.i18nc("@info:status", "Send file to printer failed."))
                self._error_message.show()
                self._update_timer.start()
            except Exception as e:
                # preferences.setValue("KOONOVOwifi/uploadingfile", "False")
                self._update_timer.start()
                if self._progress_message is not None:
                    self._progress_message.hide()
                    self._progress_message = None
                Logger.log("e", "An exception occurred in network connection: %s" % str(e))


            

    @pyqtProperty("QVariantList")
    def getSDFiles(self):
        self._sendCommand("M20")
        return list(self.sdFiles)


    def _setTargetBedTemperature(self, temperature):
        if not self._updateTargetBedTemperature(temperature):
            return
        self._sendCommand(["M140 S%s" % temperature])

    @pyqtSlot(str)
    def sendCommand(self, cmd):
        self._sendCommand(cmd)

    def _sendCommand(self, cmd):
        if self._ischanging:
            if "G28" in cmd or "G0" in cmd:
                # Logger.log("d", "_sendCommand G28 in cmd or G0 in cmd-----------: %s" % str(cmd))
                return
        # Logger.log("d", "_sendCommand %s" % str(cmd))
        if self.isBusy():
            if "M20" in cmd:
                # Logger.log("d", "_sendCommand M20 in cmd-----------: %s" % str(cmd))
                return
        if self._socket and self._socket.state() == 2 or self._socket.state() == 3:
            if isinstance(cmd, str):
                self._command_queue.put(cmd + "\r\n")
            elif isinstance(cmd, list):
                for eachCommand in cmd:
                    self._command_queue.put(eachCommand + "\r\n")

    def disconnect(self):
        # Logger.log("d", "disconnect--------------")
        preferencess = Application.getInstance().getPreferences()
        if preferencess.getValue("KOONOVOwifi/stopupdate"):
            # Logger.log("d", "timer_update KOONOVO wifi stopupdate-----------")
            self._error_message = Message("Printer disconneted.")
            self._error_message.show()
        # self._updateJobState("")
        self._isConnect = False
        self.setConnectionState(cast(ConnectionState, UnifiedConnectionState.Closed))
        if self._socket is not None:
            self._socket.readyRead.disconnect(self.on_read)
            self._socket.close()
            # self._socket.abort()
        if self._progress_message:
            self._progress_message.hide()
        if self._error_message:
            self._error_message.hide()
        self._update_timer.stop()

    def isConnected(self):
        return self._isConnect

    def isBusy(self):
        return self._isPrinting or self._isPause

    def requestWrite(self, node, file_name=None, filter_by_machine=False, file_handler=None, **kwargs):
        self.writeStarted.emit(self)
        self._update_timer.stop()
        self._isSending = True
        # imagebuff = self._gl.glReadPixels(0, 0, 800, 800, self._gl.GL_RGB,
        #                                   self._gl.GL_UNSIGNED_BYTE)
        active_build_plate = CuraApplication.getInstance().getMultiBuildPlateModel().activeBuildPlate
        scene = CuraApplication.getInstance().getController().getScene()
        gcode_dict = getattr(scene, "gcode_dict", None)
        if not gcode_dict:
            return
        self._gcode = gcode_dict.get(active_build_plate, None)
        Logger.log("d", "KOONOVO ready for print")
        # preferences = Application.getInstance().getPreferences()
        # if preferences.getValue("KOONOVOwifi/uploadingfile"):
        if self._progress_message:
            if self._error_message is not None:
                self._error_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Error: Another file is uploading, please try later."))
            self._error_message.show()
        else:
            self.startPrint()

    def startPrint(self):
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        if not global_container_stack:
            return
        if self._error_message:
            self._error_message.hide()
            self._error_message = None

        if self._progress_message:
            self._progress_message.hide()
            self._progress_message = None

        if self.isBusy():
            # self._error_message = Message(i18n_catalog.i18nc("@info:status", "Sending data to printer"), 0, False, -1,
            #                              i18n_catalog.i18nc("@info:title", "Sending Data"))
            # self._error_message.show()
            tipsname = "Now is printing. Send file to printer failed."
            if self._application.getPreferences().getValue("general/language") == "zh_CN":
                tipsname = "正在打印中，发送文件失败"
            else:
                tipsname = "Now is printing. Send file to printer failed."
            if self._progress_message is not None:
                self._progress_message.hide()
                self._progress_message = None
            if self._error_message is not None:
                self._error_message.hide()
                self._error_message = None
            self._error_message = Message(tipsname)
            self._error_message.show()
            return
        job_name = Application.getInstance().getPrintInformation().jobName.strip()
        if job_name is "":
            job_name = "untitled_print"
            job_name = "cura_file"
        filename = "%s.gcode" % job_name
        if filename in self.sdFiles:
            if self._mdialog:
                self._mdialog.close()
            self._mdialog = QDialog()
            self._mdialog.setWindowTitle("The "+filename[filename.rfind("/")+1:]+" file already exists.")
            dialogvbox = QVBoxLayout()
            dialoghbox = QHBoxLayout()
            yesbtn = QPushButton("yes")
            nobtn = QPushButton("no")
            yesbtn.clicked.connect(lambda:self._startPrint(filename))
            nobtn.clicked.connect(self.closeMDialog)
            content = QLabel("The "+filename[filename.rfind("/")+1:]+" file already exists. Do you want to upload it?")
            self._mfilename = QLineEdit()
            self._mfilename.setText(filename[filename.rfind("/")+1:])
            dialoghbox.addWidget(yesbtn)
            dialoghbox.addWidget(nobtn)
            dialogvbox.addWidget(content)
            dialogvbox.addWidget(self._mfilename)
            dialogvbox.addLayout(dialoghbox)
            self._mdialog.setLayout(dialogvbox)
            self._mdialog.exec_()
            return
        if len(filename[filename.rfind("/")+1:]) >= 30:
            if self._mdialog:
                self._mdialog.close()
            self._mdialog = QDialog()
            self._mdialog.setWindowTitle("File name is too long to upload, please rename it.")
            dialogvbox = QVBoxLayout()
            dialoghbox = QHBoxLayout()
            yesbtn = QPushButton("yes")
            nobtn = QPushButton("no")
            yesbtn.clicked.connect(self.recheckfilename)
            nobtn.clicked.connect(self.closeMDialog)
            content = QLabel("File name is too long to upload, please rename it.")
            self._mfilename = QLineEdit()
            self._mfilename.setText(filename[filename.rfind("/")+1:])
            dialoghbox.addWidget(yesbtn)
            dialoghbox.addWidget(nobtn)
            dialogvbox.addWidget(content)
            dialogvbox.addWidget(self._mfilename)
            dialogvbox.addLayout(dialoghbox)
            self._mdialog.setLayout(dialogvbox)
            self._mdialog.exec_()
            return
        if self.is_contains_chinese(filename[filename.rfind("/")+1:]):
            if self._mdialog:
                self._mdialog.close()
            self._mdialog = QDialog()
            self._mdialog.setWindowTitle("File name can not include chinese, please rename it.")
            dialogvbox = QVBoxLayout()
            dialoghbox = QHBoxLayout()
            yesbtn = QPushButton("yes")
            nobtn = QPushButton("no")
            yesbtn.clicked.connect(lambda:self.recheckfilename)
            nobtn.clicked.connect(self.closeMDialog)
            content = QLabel("File name can not include chinese, please rename it.")
            self._mfilename = QLineEdit()
            self._mfilename.setText(filename[filename.rfind("/")+1:])
            dialoghbox.addWidget(yesbtn)
            dialoghbox.addWidget(nobtn)
            dialogvbox.addWidget(content)
            dialogvbox.addWidget(self._mfilename)
            dialogvbox.addLayout(dialoghbox)
            self._mdialog.setLayout(dialogvbox)
            self._mdialog.exec_()
            return
        self._startPrint(filename)

    def recheckfilename(self):
        if self._mfilename and ".g" in self._mfilename.text().lower():
            filename = self._mfilename.text()
            if filename in self.sdFiles:
                if self._mdialog:
                    self._mdialog.close()
                self._mdialog = QDialog()
                self._mdialog.setWindowTitle("The "+filename[filename.rfind("/")+1:]+" file already exists.")
                dialogvbox = QVBoxLayout()
                dialoghbox = QHBoxLayout()
                yesbtn = QPushButton("yes")
                nobtn = QPushButton("no")
                yesbtn.clicked.connect(lambda:self._startPrint(filename))
                nobtn.clicked.connect(self.closeMDialog)
                content = QLabel("The "+filename[filename.rfind("/")+1:]+" file already exists. Do you want to upload it?")
                self._mfilename = QLineEdit()
                self._mfilename.setText(filename[filename.rfind("/")+1:])
                dialoghbox.addWidget(yesbtn)
                dialoghbox.addWidget(nobtn)
                dialogvbox.addWidget(content)
                dialogvbox.addWidget(self._mfilename)
                dialogvbox.addLayout(dialoghbox)
                self._mdialog.setLayout(dialogvbox)
                self._mdialog.exec_()
                return
            if len(filename[filename.rfind("/")+1:]) >= 30:
                if self._mdialog:
                    self._mdialog.close()
                self._mdialog = QDialog()
                self._mdialog.setWindowTitle("File name is too long to upload, please rename it.")
                dialogvbox = QVBoxLayout()
                dialoghbox = QHBoxLayout()
                yesbtn = QPushButton("yes")
                nobtn = QPushButton("no")
                yesbtn.clicked.connect(lambda:self.recheckfilename)
                nobtn.clicked.connect(self.closeMDialog)
                content = QLabel("File name is too long to upload, please rename it.")
                self._mfilename = QLineEdit()
                self._mfilename.setText(filename[filename.rfind("/")+1:])
                dialoghbox.addWidget(yesbtn)
                dialoghbox.addWidget(nobtn)
                dialogvbox.addWidget(content)
                dialogvbox.addWidget(self._mfilename)
                dialogvbox.addLayout(dialoghbox)
                self._mdialog.setLayout(dialogvbox)
                self._mdialog.exec_()
                return
            if self.is_contains_chinese(filename[filename.rfind("/")+1:]):
                if self._mdialog:
                    self._mdialog.close()
                self._mdialog = QDialog()
                self._mdialog.setWindowTitle("File name can not include chinese, please rename it.")
                dialogvbox = QVBoxLayout()
                dialoghbox = QHBoxLayout()
                yesbtn = QPushButton("yes")
                nobtn = QPushButton("no")
                yesbtn.clicked.connect(lambda:self.recheckfilename)
                nobtn.clicked.connect(self.closeMDialog)
                content = QLabel("File name can not include chinese, please rename it.")
                self._mfilename = QLineEdit()
                self._mfilename.setText(filename[filename.rfind("/")+1:])
                dialoghbox.addWidget(yesbtn)
                dialoghbox.addWidget(nobtn)
                dialogvbox.addWidget(content)
                dialogvbox.addWidget(self._mfilename)
                dialogvbox.addLayout(dialoghbox)
                self._mdialog.setLayout(dialogvbox)
                self._mdialog.exec_()
                return
            if self.isBusy():
                if self._exception_message:
                    self._exception_message.hide()
                self._exception_message = Message(i18n_catalog.i18nc("@info:status", "File cannot be transferred during printing."))
                self._exception_message.show()
                return
            self._mdialog.close()
            self._startPrint(filename)

    def _messageBoxCallback(self, button):
        def delayedCallback():
            if button == QMessageBox.Yes:
                self.startPrint()                
            else:
                CuraApplication.getInstance().getController().setActiveStage("PrepareStage")

    def _startPrint(self, file_name="cura_file.gcode"):
        if self._mdialog:
            self._mdialog.close()
        preferences = Application.getInstance().getPreferences()
        # if preferences.getValue("KOONOVOwifi/uploadingfile"):
        if self._progress_message:
            if self._error_message is not None:
                self._error_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Error: Another file is uploading, please try later."))
            self._error_message.show()
            return
        self._preheat_timer.stop()
        self._screenShot = utils.take_screenshot()
        try:
            preferences.addPreference("KOONOVOwifi/autoprint", "True")
            preferences.addPreference("KOONOVOwifi/savepath", "")
            # preferences.addPreference("KOONOVOwifi/uploadingfile", "True")
            # CuraApplication.getInstance().showPrintMonitor.emit(True)
            # self._progress_message = Message(i18n_catalog.i18nc("@info:status", "Sending data to printer"), 0, False, -1,
            #                              i18n_catalog.i18nc("@info:title", "Sending Data"), option_text=i18n_catalog.i18nc("@label", "Print jobs")
            #                              , option_state=preferences.getValue("KOONOVOwifi/autoprint"))
            if self._application.getVersion().split(".")[0] == "4":
                self._progress_message = Message(i18n_catalog.i18nc("@info:status", "Uploading print job to printer"), 0, False, -1,
                                        i18n_catalog.i18nc("@info:title", "Sending Print Job"), option_text=i18n_catalog.i18nc("@label", "Print jobs")
                                        , option_state=preferences.getValue("KOONOVOwifi/autoprint"))
                self._progress_message.addAction("Cancel", i18n_catalog.i18nc("@action:button", "Cancel"), None, "")
                self._progress_message.actionTriggered.connect(self._cancelSendGcode)
                self._progress_message.optionToggled.connect(self._onOptionStateChanged)
            else:
                Application.getInstance().showPrintMonitor.emit(True)
                self._progress_message = Message(i18n_catalog.i18nc("@info:status", "Sending file to printer"), 0, False,
                                             -1)

            self._progress_message.show()
            # job_name = Application.getInstance().getPrintInformation().jobName.strip()
            # if job_name is "":
            #     job_name = "untitled_print"
                # job_name = "cura_file"
            # file_name = "%s.gcode" % job_name
            self._last_file_name = file_name
            Logger.log("d", "KOONOVO: "+file_name + Application.getInstance().getPrintInformation().jobName.strip())

            single_string_file_data = ""
            if self._screenShot:
                single_string_file_data += utils.add_screenshot(self._screenShot, 100, 100, ";simage:")
                single_string_file_data += utils.add_screenshot(self._screenShot, 200, 200, ";;gimage:")
                single_string_file_data += "\r"
            last_process_events = time.time()
            for line in self._gcode:
                single_string_file_data += line
                if time.time() > last_process_events + 0.05:
                    QCoreApplication.processEvents()
                    last_process_events = time.time()

            self._post_multi_part = QHttpMultiPart(QHttpMultiPart.FormDataType)
            self._post_part = QHttpPart()
            # self._post_part.setHeader(QNetworkRequest.ContentTypeHeader, b'application/octet-stream')
            self._post_part.setHeader(QNetworkRequest.ContentDispositionHeader,
                                      "form-data; name=\"file\"; filename=\"%s\"" % file_name)
            self._post_part.setBody(single_string_file_data.encode())
            self._post_multi_part.append(self._post_part)
            post_request = QNetworkRequest(QUrl("http://%s/upload?X-Filename=%s" % (self._address, file_name)))
            post_request.setRawHeader(b'Content-Type', b'application/octet-stream')
            post_request.setRawHeader(b'Connection', b'keep-alive')
            self._post_reply = self._manager.post(post_request, self._post_multi_part)
            self._post_reply.uploadProgress.connect(self._onUploadProgress)
            self._post_reply.sslErrors.connect(self._onUploadError)
            # Logger.log("d", "http://%s:80/upload?X-Filename=%s" % (self._address, file_name))
            self._gcode = None
        except IOError as e:
            Logger.log("e", "An exception occurred in network connection: %s" % str(e))
            self._progress_message.hide()
            self._progress_message = None
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Send file to printer failed."))
            self._error_message.show()
            self._update_timer.start()
        except Exception as e:
            self._update_timer.start()
            if self._progress_message is not None:
                self._progress_message.hide()
                self._progress_message = None
            Logger.log("e", "An exception occurred in network connection: %s" % str(e))

    def _printFile(self):
        self._sendCommand("M23 " + self._last_file_name)
        self._sendCommand("M24")

    def _onUploadProgress(self, bytes_sent, bytes_total):
        Logger.log("d", "Upload _onUploadProgress bytes_sent %s" % str(bytes_sent))
        Logger.log("d", "Upload _onUploadProgress bytes_total %s" % str(bytes_total))
        if bytes_sent == bytes_total and bytes_sent > 0:
            self._progress_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Print job was successfully sent to the printer."))
            self._error_message.show()
            CuraApplication.getInstance().getController().setActiveStage("MonitorStage")
            # preferences = Application.getInstance().getPreferences()
            # preferences.setValue("KOONOVOwifi/uploadingfile", "False")
        elif bytes_total > 0:
            new_progress = bytes_sent / bytes_total * 100
            # Treat upload progress as response. Uploading can take more than 10 seconds, so if we don't, we can get
            # timeout responses if this happens.
            self._last_response_time = time.time()
            if new_progress > self._progress_message.getProgress():
                self._progress_message.show()  # Ensure that the message is visible.
                self._progress_message.setProgress(bytes_sent / bytes_total * 100)
        # elif bytes_total == 0 and bytes_sent == 0:
        # # 此时不能判断是否失败
        #     self._progress_message.setProgress(0)
        #     self._progress_message.hide()
        #     self._error_message = Message(i18n_catalog.i18nc("@info:status", "Send file to printer failed."))
        #     self._error_message.show()                
        else: 
            # preferences = Application.getInstance().getPreferences()
            # preferences.setValue("KOONOVOwifi/uploadingfile", "False")       
            if self._progress_message is not None:    
                self._progress_message.setProgress(0)
                self._progress_message.hide()
                self._progress_message = None
            # self._error_message = Message(i18n_catalog.i18nc("@info:status", "Send file to printer failed."))
            # self._error_message.show()
            # self._update_timer.start()

    def _onUploadError(self, reply, sslerror):
        Logger.log("d", "Upload Error")
        # preferences = Application.getInstance().getPreferences()
        # preferences.setValue("KOONOVOwifi/uploadingfile", "False")
        if self._progress_message is not None:
            self._progress_message.hide()
            self._progress_message = None
        self._error_message = Message(i18n_catalog.i18nc("@info:status", "Send file to printer failed."))
        self._error_message.show()
        self._update_timer.start()

    def _setHeadPosition(self, x, y, z, speed):
        self._sendCommand("G0 X%s Y%s Z%s F%s" % (x, y, z, speed))

    def _setHeadX(self, x, speed):
        self._sendCommand("G0 X%s F%s" % (x, speed))

    def _setHeadY(self, y, speed):
        self._sendCommand("G0 Y%s F%s" % (y, speed))

    def _setHeadZ(self, z, speed):
        self._sendCommand("G0 Z%s F%s" % (z, speed))

    def _homeHead(self):
        # Logger.log("e", "_homeHead_homeHead---------------")
        self._sendCommand("G28 X Y")

    def _homeBed(self):
        self._sendCommand("G28 Z")

    def _moveHead(self, x, y, z, speed):
        self._sendCommand(["G91", "G0 X%s Y%s Z%s F%s" % (x, y, z, speed), "G90"])

    def _update(self):
        # Logger.log("d", "timer_update KOONOVO wifi reconnecting")
        preferencess = Application.getInstance().getPreferences()
        if preferencess.getValue("KOONOVOwifi/stopupdate"):
            # Logger.log("d", "timer_update KOONOVO wifi stopupdate-----------")
            self._update_timer.stop()
            return
        # Logger.log("d", "self._socket.state() %s" % self._socket.state())
        if self._socket is not None and (self._socket.state() == 2 or self._socket.state() == 3):
            # _send_data = "M105\r\nM997\r\n"
            if self._command_queue.qsize() > 0:
                _send_data = ""
            else:
                _send_data = "M105\r\nM997\r\n"
            if self.isBusy():
                _send_data += "M994\r\nM992\r\nM27\r\n"
            while self._command_queue.qsize() > 0:
                _queue_data = self._command_queue.get()
                if "M23" in _queue_data:
                    self._socket.writeData(_queue_data.encode(sys.getfilesystemencoding()))
                    continue
                if "M24" in _queue_data:
                    self._socket.writeData(_queue_data.encode(sys.getfilesystemencoding()))
                    continue
                if self.isBusy():
                    if "M20" in _queue_data:
                        # Logger.log("d", "_update M20 in _queue_data-----------: %s" % str(_queue_data))
                        continue
                _send_data += _queue_data
            Logger.log("d", "_send_data: \r\n%s" % _send_data)
            # Logger.log("d", "_send_datasys.getfilesystemencoding(): \r\n%s" % _send_data.encode(sys.getfilesystemencoding()))
            self._socket.writeData(_send_data.encode(sys.getfilesystemencoding()))
            self._socket.flush()
            # self._socket.waitForReadyRead()
        else:
            Logger.log("d", "KOONOVO wifi reconnecting")
            self.disconnect()
            self.connect()

    def _setJobState(self, job_state):
        if job_state == "abort":
            command = "M26"
        elif job_state == "print":
            if self._isPause:
                command = "M25"
            else:
                command = "M24"
        elif job_state == "pause":
            command = "M25"
        if command:
            self._sendCommand(command)

    @pyqtSlot()
    def cancelPrint(self):
        # Logger.log("e", "cancelPrint: %s" % str(self._isPause))
        self._sendCommand("M26")

    @pyqtSlot()
    def pausePrint(self):
        # if self.printers[0].state == "paused":
        # Logger.log("e", "pausePrint: %s" % str(self._isPause))
        if self._isPause:
            self._ischanging = True
            self._sendCommand("M24")
        else:
            self._sendCommand("M25")
        
        

    @pyqtSlot()
    def resumePrint(self):
        # Logger.log("e", "resumePrint: %s" % str(self._isPause))
        if self._isPause:
            self._ischanging = True
        self._sendCommand("M24")

    def on_read(self):
        if not self._socket:
            self.disconnect()
            return
        try:
            if not self._isConnect:
                self._isConnect = True
            if self._connection_state != UnifiedConnectionState.Connected:
                self._sendCommand("M20")
                self.setConnectionState(cast(ConnectionState, UnifiedConnectionState.Connected))
                self.setConnectionText(i18n_catalog.i18nc("@info:status", "TFT Connect succeed"))
            # ss = str(self._socket.readLine().data(), encoding=sys.getfilesystemencoding())
            # while self._socket.canReadLine():
                # ss = str(self._socket.readLine().data(), encoding=sys.getfilesystemencoding())
            # ss_list = ss.split("\r\n")
            # Logger.log("e", "sys.getfilesystemencoding(): %s" % str(sys.getfilesystemencoding()))
            if not self._printers:
                self._createPrinterList()
            printer = self.printers[0]
            while self._socket.canReadLine():
                
                s = str(self._socket.readLine().data(), encoding=sys.getfilesystemencoding())
                Logger.log("d", "KOONOVO recv: "+s)
                # Logger.log("d", "KOONOVO recv self._socket addr: %s" % self._socket.peerAddress)
                # self.__additional_components_view.findChild(QObject, "ManualPrinterControl").setProperty("enabled", False)
                s = s.replace("\r", "").replace("\n", "")
                # if time.time() - self.last_update_time > 10 or time.time() - self.last_update_time<-10:
                #     Logger.log("d", "KOONOVO time:"+str(self.last_update_time)+str(time.time()))
                #     self._sendCommand("M20")
                #     self.last_update_time = time.time() 
                if "T" in s and "B" in s and "T0" in s:
                    t0_temp = s[s.find("T0:") + len("T0:"):s.find("T1:")]
                    t1_temp = s[s.find("T1:") + len("T1:"):s.find("@:")]
                    bed_temp = s[s.find("B:") + len("B:"):s.find("T0:")]
                    t0_nowtemp = float(t0_temp[0:t0_temp.find("/")])
                    t0_targettemp = float(t0_temp[t0_temp.find("/") + 1:len(t0_temp)])
                    t1_nowtemp = float(t1_temp[0:t1_temp.find("/")])
                    t1_targettemp = float(t1_temp[t1_temp.find("/") + 1:len(t1_temp)])
                    bed_nowtemp = float(bed_temp[0:bed_temp.find("/")])
                    bed_targettemp = float(bed_temp[bed_temp.find("/") + 1:len(bed_temp)])
                    # cura 3.4 new api
                    printer.updateBedTemperature(bed_nowtemp)
                    printer.updateTargetBedTemperature(bed_targettemp)
                    extruder = printer.extruders[0]
                    extruder.updateTargetHotendTemperature(t0_targettemp)
                    extruder.updateHotendTemperature(t0_nowtemp)
                    # self._number_of_extruders = 1
                    # extruder = printer.extruders[1]
                    # extruder.updateHotendTemperature(t1_nowtemp)
                    # extruder.updateTargetHotendTemperature(t1_targettemp)
                    # only on lower 3.4
                    # self._setBedTemperature(bed_nowtemp)
                    # self._updateTargetBedTemperature(bed_targettemp)
                    # if self._num_extruders > 1:
                    # self._setHotendTemperature(1, t1_nowtemp)
                    # self._updateTargetHotendTemperature(1, t1_targettemp)
                    # self._setHotendTemperature(0, t0_nowtemp)
                    # self._updateTargetHotendTemperature(0, t0_targettemp)
                    continue
                if printer.activePrintJob is None:
                    print_job = PrintJobOutputModel(output_controller=self._output_controller)
                    printer.updateActivePrintJob(print_job)
                else:
                    print_job = printer.activePrintJob
                if s.startswith("M997"):
                    job_state = "offline"
                    if "IDLE" in s:
                        self._isPrinting = False
                        self._isPause = False
                        job_state = 'idle'
                        printer.acceptsCommands = True
                    elif "PRINTING" in s:
                        self._isPrinting = True
                        self._isPause = False
                        job_state = 'printing'
                        printer.acceptsCommands = False
                    elif "PAUSE" in s:
                        self._isPrinting = False
                        self._isPause = True
                        job_state = 'paused'
                        printer.acceptsCommands = False                        
                    print_job.updateState(job_state)
                    printer.updateState(job_state)
                    if self._isPrinting:
                        self._ischanging = False
                    # self._updateJobState(job_state)
                    continue
                # print_job.updateState('idle')
                # printer.updateState('idle')
                if s.startswith("M994"):
                    if self.isBusy() and s.rfind("/") != -1:
                        self._printing_filename = s[s.rfind("/") + 1:s.rfind(";")]
                    else:
                        self._printing_filename = ""
                    print_job.updateName(self._printing_filename)
                    # self.setJobName(self._printing_filename)
                    continue
                if s.startswith("M992"):
                    if self.isBusy():
                        tm = s[s.find("M992") + len("M992"):len(s)].replace(" ", "")
                        mms = tm.split(":")
                        self._printing_time = int(mms[0]) * 3600 + int(mms[1]) * 60 + int(mms[2])
                    else:
                        self._printing_time = 0
                    # Logger.log("d", self._printing_time)
                    print_job.updateTimeElapsed(self._printing_time)
                    # self.setTimeElapsed(self._printing_time)
                    # print_job.updateTimeTotal(self._printing_time)
                    # self.setTimeTotal(self._printing_time)
                    continue
                if s.startswith("M27"):
                    if self._application.getVersion().split(".")[0] == "4":
                        if self.isBusy():
                            self._printing_progress = float(s[s.find("M27") + len("M27"):len(s)].replace(" ", ""))
                            totaltime = self._printing_time/self._printing_progress*100
                        else:
                            self._printing_progress = 0
                            totaltime = self._printing_time * 100
                        # Logger.log("d", self._printing_time)
                        # Logger.log("d", totaltime)
                        # self.setProgress(self._printing_progress)
                        print_job.updateTimeTotal(self._printing_time)
                        print_job.updateTimeElapsed(self._printing_time*2-totaltime)
                    else:
                        if self.isBusy():
                            self._printing_progress = float(s[s.find("M27") + len("M27"):len(s)].replace(" ", ""))
                            totaltime = 100 / self._printing_progress * self._printing_time
                        else:
                            self._printing_progress = 0
                            totaltime = self._printing_time * 100
                        print_job.updateTimeTotal(totaltime)
                    continue
                if 'Begin file list' in s:
                    self._sdFileList = True
                    self.sdFiles = []
                    self.last_update_time = time.time()
                    continue
                if 'End file list' in s:
                    self._sdFileList = False
                    continue
                if self._sdFileList :
                    s = s.replace("\n", "").replace("\r", "")
                    if s.lower().endswith("gcode") or s.lower().endswith("gco") or s.lower.endswith("g"):
                        self.sdFiles.append(s)
                    continue
                if s.startswith("Upload"):
                    tipsname = "Send file to printer failed."
                    if self._application.getPreferences().getValue("general/language") == "zh_CN":
                        tipsname = "发送文件失败"
                    else:
                        tipsname = "Send file to printer failed."
                    if self._progress_message is not None:
                        self._progress_message.hide()
                        self._progress_message = None
                    if self._error_message is not None:
                        self._error_message.hide()
                        self._error_message = None
                    self._error_message = Message(tipsname)
                    self._error_message.show()
                    self._update_timer.start()
                    continue
        except Exception as e:
            print(e)

    def _updateTargetBedTemperature(self, temperature):
        if self._target_bed_temperature == temperature:
            return False
        self._target_bed_temperature = temperature
        self.targetBedTemperatureChanged.emit()
        return True

    def _updateTargetHotendTemperature(self, index, temperature):
        if self._target_hotend_temperatures[index] == temperature:
            return False
        self._target_hotend_temperatures[index] = temperature
        self.targetHotendTemperaturesChanged.emit()
        return True

    def _createPrinterList(self):
        printer = PrinterOutputModel(output_controller=self._output_controller, number_of_extruders=self._number_of_extruders)
        printer.updateName(self.name)
        self._printers = [printer]
        self.printersChanged.emit()

    def _onRequestFinished(self, reply):
        http_status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        self._isSending = True
        self._update_timer.start()
        self._sendCommand("M20")
        preferences = Application.getInstance().getPreferences()
        preferences.addPreference("KOONOVOwifi/autoprint", "True")
        # preferences.addPreference("KOONOVOwifi/savepath", "")
        # preferences.setValue("KOONOVOwifi/autoprint", str(self._progress_message.getOptionState()))
        if preferences.getValue("KOONOVOwifi/autoprint"):
            self._printFile()
        if not http_status_code:
            return

    def _onOptionStateChanged(self, optstate):
        preferences = Application.getInstance().getPreferences()
        preferences.setValue("KOONOVOwifi/autoprint", str(optstate))

    def _cancelSendGcode(self, message_id, action_id):
        self._update_timer.start()
        self._isSending = False
        self._progress_message.hide()
        self._post_reply.abort()
    
    def CreateKOONOVOController(self):
        Logger.log("d", "Creating additional ui components for KOONOVOcontroller.")
        # self.__additional_components_view = CuraApplication.getInstance().createQmlComponent(self._monitor_view_qml_path, {"KOONOVOcontroller": self})
        self.__additional_components_view = Application.getInstance().createQmlComponent(self._monitor_view_qml_path, {"manager": self})
        # trlist = CuraApplication.getInstance()._additional_components
        # for comp in trlist:
        Logger.log("w", "create KOONOVOcontroller ")
        if not self.__additional_components_view:
            Logger.log("w", "Could not create ui components for tft35.")
            return

    def _onGlobalContainerChanged(self) -> None:
        self._global_container_stack = Application.getInstance().getGlobalContainerStack()
        definitions = self._global_container_stack.definition.findDefinitions(key="cooling")
        Logger.log("d", definitions[0].label)
# coding=utf-8
from UM.i18n import i18nCatalog
from UM.Application import Application
from UM.Logger import Logger
from UM.Signal import signalemitter
from UM.Message import Message
from cura.PrinterOutputDevice import PrinterOutputDevice, ConnectionState
from cura.CuraApplication import CuraApplication

from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice, AuthState
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel
from UM.PluginRegistry import PluginRegistry
from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.Models.SettingDefinitionsModel import SettingDefinitionsModel

from PyQt5.QtQuick import QQuickView
from PyQt5.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton

from cura.PrinterOutput.GenericOutputController import GenericOutputController

from PyQt5.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkRequest, QNetworkAccessManager, QNetworkReply, QTcpSocket
from PyQt5.QtCore import QUrl, QTimer, pyqtSignal, pyqtProperty, pyqtSlot, QCoreApplication, Qt, QObject, QByteArray
from queue import Queue

from . import utils

import UM

import json
import os.path
import time
import base64
import sys
from enum import IntEnum
from UM.Preferences import Preferences

from typing import cast, Any, Callable, Dict, List, Optional, Union, TYPE_CHECKING
if TYPE_CHECKING:
    from UM.Scene.SceneNode import SceneNode #For typing.
    from UM.FileHandler.FileHandler import FileHandler #For typing.

i18n_catalog = i18nCatalog("cura")

class UnifiedConnectionState(IntEnum):
    try:
        Closed = ConnectionState.Closed
        Connecting = ConnectionState.Connecting
        Connected = ConnectionState.Connected
        Busy = ConnectionState.Busy
        Error = ConnectionState.Error
    except AttributeError:
        Closed = ConnectionState.closed          # type: ignore
        Connecting = ConnectionState.connecting  # type: ignore
        Connected = ConnectionState.connected    # type: ignore
        Busy = ConnectionState.busy              # type: ignore
        Error = ConnectionState.error            # type: ignore

@signalemitter
class KOONOVOOutputDevice(NetworkedPrinterOutputDevice):
    def __init__(self, instance_id: str, address: str, properties: dict, **kwargs) -> None:
        super().__init__(device_id = instance_id, address = address, properties = properties, **kwargs)
        self._address = address
        self._port = 8080
        self._key = instance_id
        self._properties = properties

        self._target_bed_temperature = 0
        self._num_extruders = 1
        self._hotend_temperatures = [0] * self._num_extruders
        self._target_hotend_temperatures = [0] * self._num_extruders      

        self._application = CuraApplication.getInstance()
        if self._application.getVersion().split(".")[0] == "4":
            self._monitor_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MonitorItem4x.qml")
        else:
            self._monitor_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MonitorItem.qml")

        self.setPriority(3)  # Make sure the output device gets selected above local file output and Octoprint XD
        self._active_machine = CuraApplication.getInstance().getMachineManager().activeMachine
        self.setName(instance_id)
        self.setShortDescription(i18n_catalog.i18nc("@action:button", "Print over TFT"))
        self.setDescription(i18n_catalog.i18nc("@properties:tooltip", "Print over TFT"))
        self.setIconName("print")
        self.setConnectionText(i18n_catalog.i18nc("@info:status", "Connected to TFT on {0}").format(self._key))
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerChanged)

        self._socket = None
        self._gl = None
        self._command_queue = Queue()
        self._isPrinting = False
        self._isPause = False
        self._isSending = False
        self._gcode = None
        self._isConnect = False
        self._printing_filename = ""
        self._printing_progress = 0
        self._printing_time = 0
        self._start_time = 0
        self._pause_time = 0
        self.last_update_time = 0
        self.angle = 10
        self._connection_state_before_timeout = None
        self._sdFileList = False
        self.sdFiles = []
        self._mdialog = None
        self._mfilename = None
        self._uploadpath = ''

        self._settings_reply = None
        self._printer_reply = None
        self._job_reply = None
        self._command_reply = None
        self._screenShot = None

        self._image_reply = None
        self._stream_buffer = b""
        self._stream_buffer_start_index = -1

        self._post_reply = None
        self._post_multi_part = None
        self._post_part = None
        self._last_file_name = None
        self._last_file_path = None

        self._progress_message = None
        self._error_message = None
        self._connection_message = None
        self.__additional_components_view = None

        self._ischanging = False

        self._update_timer = QTimer()
        self._update_timer.setInterval(2000)  # TODO; Add preference for update interval
        self._update_timer.setSingleShot(False)
        self._update_timer.timeout.connect(self._update)

        self._manager = QNetworkAccessManager()
        self._manager.finished.connect(self._onRequestFinished)

        self._preheat_timer = QTimer()
        self._preheat_timer.setSingleShot(True)
        self._preheat_timer.timeout.connect(self.cancelPreheatBed)
        self._exception_message = None
        self._output_controller = GenericOutputController(self)
        self._number_of_extruders = 1
        self._camera_url = ""
        # Application.getInstance().getOutputDeviceManager().outputDevicesChanged.connect(self._onOutputDevicesChanged)
        CuraApplication.getInstance().getCuraSceneController().activeBuildPlateChanged.connect(self.CreateKOONOVOController)


    def _onOutputDevicesChanged(self):
        Logger.log("d", "KOONOVO _onOutputDevicesChanged")

    def connect(self):
        if self._socket is not None:
            self._socket.close()
            self._socket.abort()
            self._socket = None
        self._socket = QTcpSocket()
        # Logger.log("d","self._socket.connectToHost %s" % self._address)
        # Logger.log("d","self._socket.connectToHost %s" % self._port)
        self._socket.connectToHost(self._address, self._port)
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        name1 = "Print over " + global_container_stack.getName()
        if CuraApplication.getInstance().getPreferences().getValue("general/language") == "zh_CN":
            name1 = "WIFI传输打印"
        else:
            name1 = "Print over " + global_container_stack.getName()
        self.setShortDescription(i18n_catalog.i18nc("@action:button", name1))
        self.setDescription(i18n_catalog.i18nc("@properties:tooltip", name1))
        Logger.log("d", "KOONOVO socket connecting ")
        self._socket.waitForConnected(2000)
        # Logger.log("d","self._socket.connectToHost self._socket.state() %s" % self._socket.state())
        # if self._socket.state() == 0 or self._socket.state() == 1:
        #     self.connect()
        # else:
        self.setConnectionState(cast(ConnectionState, UnifiedConnectionState.Connecting))
        self._setAcceptsCommands(True)
        self._socket.readyRead.connect(self.on_read)
        preferences = Application.getInstance().getPreferences()
        preferences.addPreference("KOONOVOwifi/stopupdate", "False")
        self._update_timer.start()

    def getProperties(self):
        return self._properties

    @pyqtSlot(str, result=str)
    def getProperty(self, key):
        key = key.encode("utf-8")
        if key in self._properties:
            return self._properties.get(key, b"").decode("utf-8")
        else:
            return ""

    @pyqtSlot(result=str)
    def getKey(self):
        return self._key

    @pyqtProperty(str, constant=True)
    def address(self):
        return self._properties.get(b"address", b"").decode("utf-8")

    @pyqtProperty(str, constant=True)
    def name(self):
        return self._properties.get(b"name", b"").decode("utf-8")

    @pyqtProperty(str, constant=True)
    def firmwareVersion(self):
        return self._properties.get(b"firmware_version", b"").decode("utf-8")

    @pyqtProperty(str, constant=True)
    def ipAddress(self):
        return self._address

    @pyqtSlot(float, float)
    def preheatBed(self, temperature, duration):
        self._setTargetBedTemperature(temperature)
        if duration > 0:
            self._preheat_timer.setInterval(duration * 1000)
            self._preheat_timer.start()
        else:
            self._preheat_timer.stop()

    @pyqtSlot()
    def cancelPreheatBed(self):
        self._setTargetBedTemperature(0)
        self._preheat_timer.stop()

    @pyqtSlot()
    def printtest(self):
        self.sendCommand("M104 S0\r\n M140 S0\r\n M106 S255")

    @pyqtSlot()
    def openfan(self):
        self.sendCommand("M106 S255")

    @pyqtSlot()
    def closefan(self):
        self.sendCommand("M106 S0")

    @pyqtSlot()
    def unlockmotor(self):
        self.sendCommand("M84")

    @pyqtSlot()
    def e0down(self):
        if not self._isPrinting:
            self.sendCommand("T0\r\n G91\r\n G1 E10 F1000\r\n G90")
        else:
            if self._error_message is not None:
                self._error_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Error: printing can not send"))
            self._error_message.show()

    @pyqtSlot()
    def e0up(self):
        if not self._isPrinting:
            self.sendCommand("T0\r\n G91\r\n G1 E-10 F1000\r\n G90")
        else:
            if self._error_message is not None:
                self._error_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Error: printing can not send"))
            self._error_message.show()

    @pyqtSlot()
    def e1down(self):
        if not self._isPrinting:
            self.sendCommand("T1\r\n G91\r\n G1 E10 F1000\r\n G90")
        else:
            if self._error_message is not None:
                self._error_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Error: printing can not send"))
            self._error_message.show()

    @pyqtSlot()
    def e1up(self):
        if not self._isPrinting:
            self.sendCommand("T1\r\n G91\r\n G1 E-10 F1000\r\n G90")
        else:
            if self._error_message is not None:
                self._error_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Error: printing can not send"))
            self._error_message.show()

    @pyqtSlot()
    def printer_E_num(self):
        return self._number_of_extruders

    @pyqtSlot()
    def printer_state(self):
        if len(self._printers) <= 0:
            return "offline"
        return self.printers[0].state

    @pyqtSlot()
    def isprinterprinting(self):
        if self._isPrinting:
            return "true"
        return "false"

    @pyqtSlot()
    def selectfile(self):
        if self._last_file_name:
            return True
        else:
            return False

    @pyqtSlot(str)
    def deleteSDFiles(self, filename):
        # filename = "几何图.gcode"
        self._sendCommand("M30 1:/" + filename)
        if filename in self.sdFiles:
            self.sdFiles.remove(filename)
        self._sendCommand("M20")

    @pyqtSlot(str)
    def printSDFiles(self, filename):
        self._sendCommand("M23 "+filename)
        self._sendCommand("M24")

    @pyqtSlot()
    def selectFileToUplload(self):
        preferences = Application.getInstance().getPreferences()
        preferences.addPreference("KOONOVOwifi/autoprint", "True")
        preferences.addPreference("KOONOVOwifi/savepath", "")
        # if preferences.getValue("KOONOVOwifi/uploadingfile"):
        if self._progress_message:
            if self._error_message is not None:
                self._error_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Error: Another file is uploading, please try later."))
            self._error_message.show()
        else:
            filename,_ = QFileDialog.getOpenFileName(None, "choose file", preferences.getValue("KOONOVOwifi/savepath"), "Gcode(*.gcode;*.g;*.goc)")
            preferences.setValue("KOONOVOwifi/savepath", filename)
            self._uploadpath = filename
            if ".g" in filename.lower():
                Logger.log("d", "selectfile:"+filename)
                if filename[filename.rfind("/")+1:] in self.sdFiles:
                    if self._mdialog:
                        self._mdialog.close()
                    self._mdialog = QDialog()
                    self._mdialog.setWindowTitle("The "+filename[filename.rfind("/")+1:]+" file already exists.")
                    dialogvbox = QVBoxLayout()
                    dialoghbox = QHBoxLayout()
                    yesbtn = QPushButton("yes")
                    nobtn = QPushButton("no")
                    yesbtn.clicked.connect(lambda : self.uploadfunc(filename))
                    nobtn.clicked.connect(self.closeMDialog)
                    content = QLabel("The "+filename[filename.rfind("/")+1:]+" file already exists. Do you want to upload it?")
                    self._mfilename = QLineEdit()
                    self._mfilename.setText(filename[filename.rfind("/")+1:])
                    dialoghbox.addWidget(yesbtn)
                    dialoghbox.addWidget(nobtn)
                    dialogvbox.addWidget(content)
                    dialogvbox.addWidget(self._mfilename)
                    dialogvbox.addLayout(dialoghbox)
                    self._mdialog.setLayout(dialogvbox)
                    self._mdialog.exec_()
                    return
                if len(filename[filename.rfind("/")+1:]) >= 30:
                    if self._mdialog:
                        self._mdialog.close()
                    self._mdialog = QDialog()
                    self._mdialog.setWindowTitle("File name is too long to upload, please rename it.")
                    dialogvbox = QVBoxLayout()
                    dialoghbox = QHBoxLayout()
                    yesbtn = QPushButton("yes")
                    nobtn = QPushButton("no")
                    yesbtn.clicked.connect(lambda : self.renameupload(filename))
                    nobtn.clicked.connect(self.closeMDialog)
                    content = QLabel("File name is too long to upload, please rename it.")
                    self._mfilename = QLineEdit()
                    self._mfilename.setText(filename[filename.rfind("/")+1:])
                    dialoghbox.addWidget(yesbtn)
                    dialoghbox.addWidget(nobtn)
                    dialogvbox.addWidget(content)
                    dialogvbox.addWidget(self._mfilename)
                    dialogvbox.addLayout(dialoghbox)
                    self._mdialog.setLayout(dialogvbox)
                    self._mdialog.exec_()
                    return
                if self.is_contains_chinese(filename[filename.rfind("/")+1:]):
                    if self._mdialog:
                        self._mdialog.close()
                    self._mdialog = QDialog()
                    self._mdialog.setWindowTitle("File name can not include chinese, please rename it.")
                    dialogvbox = QVBoxLayout()
                    dialoghbox = QHBoxLayout()
                    yesbtn = QPushButton("yes")
                    nobtn = QPushButton("no")
                    yesbtn.clicked.connect(lambda : self.renameupload(filename))
                    nobtn.clicked.connect(self.closeMDialog)
                    content = QLabel("File name can not include chinese, please rename it.")
                    self._mfilename = QLineEdit()
                    self._mfilename.setText(filename[filename.rfind("/")+1:])
                    dialoghbox.addWidget(yesbtn)
                    dialoghbox.addWidget(nobtn)
                    dialogvbox.addWidget(content)
                    dialogvbox.addWidget(self._mfilename)
                    dialogvbox.addLayout(dialoghbox)
                    self._mdialog.setLayout(dialogvbox)
                    self._mdialog.exec_()
                    return
                if self.isBusy():
                    if self._exception_message:
                        self._exception_message.hide()
                    self._exception_message = Message(i18n_catalog.i18nc("@info:status", "File cannot be transferred during printing."))
                    self._exception_message.show()
                    return
                self.uploadfunc(filename)
    
    def is_contains_chinese(self,strs):
        #检验是否含有中文字符
        # Logger.log("d", "is_contains_chinese---filename==: %s" % str(strs))
        # for _char in strs:
        #     if '\u4e00' <= _char <= '\u9fa5':
        #         return True
        return False

    def closeMDialog(self):
        if self._mdialog:
            self._mdialog.close()
    
    def renameupload(self, filename):
        if self._mfilename and ".g" in self._mfilename.text().lower():
            filename = filename[:filename.rfind("/")]+"/"+self._mfilename.text()
            # Logger.log("d", "renameupload---filename==: %s" % str(filename))
            if self._mfilename.text() in self.sdFiles:
                if self._mdialog:
                    self._mdialog.close()
                self._mdialog = QDialog()
                self._mdialog.setWindowTitle("The "+filename[filename.rfind("/")+1:]+" file already exists.")
                dialogvbox = QVBoxLayout()
                dialoghbox = QHBoxLayout()
                yesbtn = QPushButton("yes")
                nobtn = QPushButton("no")
                yesbtn.clicked.connect(lambda : self.uploadfunc(filename))
                nobtn.clicked.connect(self.closeMDialog)
                content = QLabel("The "+filename[filename.rfind("/")+1:]+" file already exists. Do you want to upload it?")
                self._mfilename = QLineEdit()
                self._mfilename.setText(filename[filename.rfind("/")+1:])
                dialoghbox.addWidget(yesbtn)
                dialoghbox.addWidget(nobtn)
                dialogvbox.addWidget(content)
                dialogvbox.addWidget(self._mfilename)
                dialogvbox.addLayout(dialoghbox)
                self._mdialog.setLayout(dialogvbox)
                self._mdialog.exec_()
                return
            if len(filename[filename.rfind("/")+1:]) >= 30:
                if self._mdialog:
                    self._mdialog.close()
                self._mdialog = QDialog()
                self._mdialog.setWindowTitle("File name is too long to upload, please rename it.")
                dialogvbox = QVBoxLayout()
                dialoghbox = QHBoxLayout()
                yesbtn = QPushButton("yes")
                nobtn = QPushButton("no")
                yesbtn.clicked.connect(lambda : self.renameupload(filename))
                nobtn.clicked.connect(self.closeMDialog)
                content = QLabel("File name is too long to upload, please rename it.")
                self._mfilename = QLineEdit()
                self._mfilename.setText(filename[filename.rfind("/")+1:])
                dialoghbox.addWidget(yesbtn)
                dialoghbox.addWidget(nobtn)
                dialogvbox.addWidget(content)
                dialogvbox.addWidget(self._mfilename)
                dialogvbox.addLayout(dialoghbox)
                self._mdialog.setLayout(dialogvbox)
                self._mdialog.exec_()
                return
            if self.is_contains_chinese(filename[filename.rfind("/")+1:]):
                if self._mdialog:
                    self._mdialog.close()
                self._mdialog = QDialog()
                self._mdialog.setWindowTitle("File name can not include chinese, please rename it.")
                dialogvbox = QVBoxLayout()
                dialoghbox = QHBoxLayout()
                yesbtn = QPushButton("yes")
                nobtn = QPushButton("no")
                yesbtn.clicked.connect(lambda : self.renameupload(filename))
                nobtn.clicked.connect(self.closeMDialog)
                content = QLabel("File name can not include chinese, please rename it.")
                self._mfilename = QLineEdit()
                self._mfilename.setText(filename[filename.rfind("/")+1:])
                dialoghbox.addWidget(yesbtn)
                dialoghbox.addWidget(nobtn)
                dialogvbox.addWidget(content)
                dialogvbox.addWidget(self._mfilename)
                dialogvbox.addLayout(dialoghbox)
                self._mdialog.setLayout(dialogvbox)
                self._mdialog.exec_()
                return
            if self.isBusy():
                if self._exception_message:
                    self._exception_message.hide()
                self._exception_message = Message(i18n_catalog.i18nc("@info:status", "File cannot be transferred during printing."))
                self._exception_message.show()
                return
            self._mdialog.close()
            # preferences = Application.getInstance().getPreferences()
            # if preferences.getValue("KOONOVOwifi/uploadingfile"):
            if self._progress_message:
                if self._error_message is not None:
                    self._error_message.hide()
                self._error_message = Message(i18n_catalog.i18nc("@info:status", "Error: Another file is uploading, please try later."))
                self._error_message.show()
            else:
                self.uploadfunc(filename)
        
        
    
    def uploadfunc(self, filename):
        if self._mdialog:
            self._mdialog.close()
        preferences = Application.getInstance().getPreferences()
        if self._progress_message:
            if self._error_message is not None:
                self._error_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Error: Another file is uploading, please try later."))
            self._error_message.show()
        else:
            preferences.addPreference("KOONOVOwifi/autoprint", "True")
            preferences.addPreference("KOONOVOwifi/savepath", "")
            # preferences.addPreference("KOONOVOwifi/uploadingfile", "True")
            self._update_timer.stop()
            self._isSending = True
            self._preheat_timer.stop()
            single_string_file_data = ""
            try:
                f = open(self._uploadpath, "r", encoding=sys.getfilesystemencoding())
                single_string_file_data = f.read()
                # Logger.log("d", "single_string_file_data: %s" % str(single_string_file_data))
                file_name = filename[filename.rfind("/")+1:]
                # Logger.log("d", "file_namefile_name: %s" % str(file_name))
                self._last_file_name = filename[filename.rfind("/")+1:]
                # self._progress_message = Message(i18n_catalog.i18nc("@info:status", "Sending data to printer"), 0, False, -1,
                #                             i18n_catalog.i18nc("@info:title", "Sending Data"), option_text=i18n_catalog.i18nc("@label", "Print jobs")
                #                             , option_state=preferences.getValue("KOONOVOwifi/autoprint"))
                name0 = "Print Jobs"
                name1 = "Uploading print job to printer"
                name2 = "Sending Print Job"
                namecancel = "Cancel"
                if self._application.getPreferences().getValue("general/language") == "zh_CN":
                    name0 = "传输完成之后，立即打印。"
                    name1 = "正在上传打印文件到打印机"
                    name2 = "正在发送打印文件"
                    namecancel = "取消"
                else:
                    name0 = "Print Jobs"
                    name1 = "Uploading print job to printer"
                    name2 = "Sending Print Job"
                    namecancel = "Cancel"
                    
                self._progress_message = Message(name1, 0, False, -1,
                                            name2, option_text=name0
                                            , option_state=preferences.getValue("KOONOVOwifi/autoprint"))
                self._progress_message.addAction("Cancel", namecancel, None, "")
                self._progress_message.actionTriggered.connect(self._cancelSendGcode)
                self._progress_message.optionToggled.connect(self._onOptionStateChanged)
                self._progress_message.show()

                data = QByteArray()
                data.append(single_string_file_data.encode())

                # self._post_multi_part = QHttpMultiPart(QHttpMultiPart.FormDataType)
                # self._post_part = QHttpPart()
                # file_name = file_name.encode(sys.getfilesystemencoding())
                # Logger.log("e", "sys.getfilesystemencoding(): %s" % str(sys.getfilesystemencoding()))
                # Logger.log("d", "file_namefile_name222: %s" % str(file_name.encode("utf-8")))
                # Logger.log("d", "QUrl.toPercentEncoding(): %s" % str(QUrl.toPercentEncoding(file_name)))
                # self._post_part.setHeader(QNetworkRequest.ContentDispositionHeader,
                #                         "form-data; name=\"file\"; filename=\"%s\"" % file_name)
                # self._post_part.setBody(single_string_file_data.encode())
                # self._post_multi_part.append(self._post_part)
                post_request = QNetworkRequest(QUrl("http://%s/upload?X-Filename=%s" % (self._address, file_name)))
                # post_request = QNetworkRequest(QUrl("http://%s/upload?X-Filename=%s" % (self._address, QUrl.toPercentEncoding(file_name))))
                # post_request = QNetworkRequest(QUrl("http://%s/upload?X-Filename=%s" % (self._address, "%E5%87%A0%E4%BD%95%E4%BD%93.gcode")))
                post_request.setRawHeader(b'Content-Type', b'application/octet-stream')
                # post_request.setRawHeader(b'Content-Type', b'application/x-www-form-urlencoded')
                post_request.setRawHeader(b'Connection', b'keep-alive')
                self._post_reply = self._manager.post(post_request, data)
                self._post_reply.uploadProgress.connect(self._onUploadProgress)
                self._post_reply.sslErrors.connect(self._onUploadError)
                self._gcode = None
            except IOError as e:
                Logger.log("e", "An exception occurred in network connection: %s" % str(e))
                # preferences.setValue("KOONOVOwifi/uploadingfile", "False")
                self._progress_message.hide()
                self._progress_message = None
                self._error_message = Message(i18n_catalog.i18nc("@info:status", "Send file to printer failed."))
                self._error_message.show()
                self._update_timer.start()
            except Exception as e:
                # preferences.setValue("KOONOVOwifi/uploadingfile", "False")
                self._update_timer.start()
                if self._progress_message is not None:
                    self._progress_message.hide()
                    self._progress_message = None
                Logger.log("e", "An exception occurred in network connection: %s" % str(e))


            

    @pyqtProperty("QVariantList")
    def getSDFiles(self):
        self._sendCommand("M20")
        return list(self.sdFiles)


    def _setTargetBedTemperature(self, temperature):
        if not self._updateTargetBedTemperature(temperature):
            return
        self._sendCommand(["M140 S%s" % temperature])

    @pyqtSlot(str)
    def sendCommand(self, cmd):
        self._sendCommand(cmd)

    def _sendCommand(self, cmd):
        if self._ischanging:
            if "G28" in cmd or "G0" in cmd:
                # Logger.log("d", "_sendCommand G28 in cmd or G0 in cmd-----------: %s" % str(cmd))
                return
        # Logger.log("d", "_sendCommand %s" % str(cmd))
        if self.isBusy():
            if "M20" in cmd:
                # Logger.log("d", "_sendCommand M20 in cmd-----------: %s" % str(cmd))
                return
        if self._socket and self._socket.state() == 2 or self._socket.state() == 3:
            if isinstance(cmd, str):
                self._command_queue.put(cmd + "\r\n")
            elif isinstance(cmd, list):
                for eachCommand in cmd:
                    self._command_queue.put(eachCommand + "\r\n")

    def disconnect(self):
        # Logger.log("d", "disconnect--------------")
        preferencess = Application.getInstance().getPreferences()
        if preferencess.getValue("KOONOVOwifi/stopupdate"):
            # Logger.log("d", "timer_update KOONOVO wifi stopupdate-----------")
            self._error_message = Message("Printer disconneted.")
            self._error_message.show()
        # self._updateJobState("")
        self._isConnect = False
        self.setConnectionState(cast(ConnectionState, UnifiedConnectionState.Closed))
        if self._socket is not None:
            self._socket.readyRead.disconnect(self.on_read)
            self._socket.close()
            # self._socket.abort()
        if self._progress_message:
            self._progress_message.hide()
        if self._error_message:
            self._error_message.hide()
        self._update_timer.stop()

    def isConnected(self):
        return self._isConnect

    def isBusy(self):
        return self._isPrinting or self._isPause

    def requestWrite(self, node, file_name=None, filter_by_machine=False, file_handler=None, **kwargs):
        self.writeStarted.emit(self)
        self._update_timer.stop()
        self._isSending = True
        # imagebuff = self._gl.glReadPixels(0, 0, 800, 800, self._gl.GL_RGB,
        #                                   self._gl.GL_UNSIGNED_BYTE)
        active_build_plate = CuraApplication.getInstance().getMultiBuildPlateModel().activeBuildPlate
        scene = CuraApplication.getInstance().getController().getScene()
        gcode_dict = getattr(scene, "gcode_dict", None)
        if not gcode_dict:
            return
        self._gcode = gcode_dict.get(active_build_plate, None)
        Logger.log("d", "KOONOVO ready for print")
        # preferences = Application.getInstance().getPreferences()
        # if preferences.getValue("KOONOVOwifi/uploadingfile"):
        if self._progress_message:
            if self._error_message is not None:
                self._error_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Error: Another file is uploading, please try later."))
            self._error_message.show()
        else:
            self.startPrint()

    def startPrint(self):
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        if not global_container_stack:
            return
        if self._error_message:
            self._error_message.hide()
            self._error_message = None

        if self._progress_message:
            self._progress_message.hide()
            self._progress_message = None

        if self.isBusy():
            # self._error_message = Message(i18n_catalog.i18nc("@info:status", "Sending data to printer"), 0, False, -1,
            #                              i18n_catalog.i18nc("@info:title", "Sending Data"))
            # self._error_message.show()
            tipsname = "Now is printing. Send file to printer failed."
            if self._application.getPreferences().getValue("general/language") == "zh_CN":
                tipsname = "正在打印中，发送文件失败"
            else:
                tipsname = "Now is printing. Send file to printer failed."
            if self._progress_message is not None:
                self._progress_message.hide()
                self._progress_message = None
            if self._error_message is not None:
                self._error_message.hide()
                self._error_message = None
            self._error_message = Message(tipsname)
            self._error_message.show()
            return
        job_name = Application.getInstance().getPrintInformation().jobName.strip()
        if job_name is "":
            job_name = "untitled_print"
            job_name = "cura_file"
        filename = "%s.gcode" % job_name
        if filename in self.sdFiles:
            if self._mdialog:
                self._mdialog.close()
            self._mdialog = QDialog()
            self._mdialog.setWindowTitle("The "+filename[filename.rfind("/")+1:]+" file already exists.")
            dialogvbox = QVBoxLayout()
            dialoghbox = QHBoxLayout()
            yesbtn = QPushButton("yes")
            nobtn = QPushButton("no")
            yesbtn.clicked.connect(self._startPrint(filename))
            nobtn.clicked.connect(self.closeMDialog)
            content = QLabel("The "+filename[filename.rfind("/")+1:]+" file already exists. Do you want to upload it?")
            self._mfilename = QLineEdit()
            self._mfilename.setText(filename[filename.rfind("/")+1:])
            dialoghbox.addWidget(yesbtn)
            dialoghbox.addWidget(nobtn)
            dialogvbox.addWidget(content)
            dialogvbox.addWidget(self._mfilename)
            dialogvbox.addLayout(dialoghbox)
            self._mdialog.setLayout(dialogvbox)
            self._mdialog.exec_()
            return
        if len(filename[filename.rfind("/")+1:]) >= 30:
            if self._mdialog:
                self._mdialog.close()
            self._mdialog = QDialog()
            self._mdialog.setWindowTitle("File name is too long to upload, please rename it.")
            dialogvbox = QVBoxLayout()
            dialoghbox = QHBoxLayout()
            yesbtn = QPushButton("yes")
            nobtn = QPushButton("no")
            yesbtn.clicked.connect(self.recheckfilename)
            nobtn.clicked.connect(self.closeMDialog)
            content = QLabel("File name is too long to upload, please rename it.")
            self._mfilename = QLineEdit()
            self._mfilename.setText(filename[filename.rfind("/")+1:])
            dialoghbox.addWidget(yesbtn)
            dialoghbox.addWidget(nobtn)
            dialogvbox.addWidget(content)
            dialogvbox.addWidget(self._mfilename)
            dialogvbox.addLayout(dialoghbox)
            self._mdialog.setLayout(dialogvbox)
            self._mdialog.exec_()
            return
        if self.is_contains_chinese(filename[filename.rfind("/")+1:]):
            if self._mdialog:
                self._mdialog.close()
            self._mdialog = QDialog()
            self._mdialog.setWindowTitle("File name can not include chinese, please rename it.")
            dialogvbox = QVBoxLayout()
            dialoghbox = QHBoxLayout()
            yesbtn = QPushButton("yes")
            nobtn = QPushButton("no")
            yesbtn.clicked.connect(self.recheckfilename)
            nobtn.clicked.connect(self.closeMDialog)
            content = QLabel("File name can not include chinese, please rename it.")
            self._mfilename = QLineEdit()
            self._mfilename.setText(filename[filename.rfind("/")+1:])
            dialoghbox.addWidget(yesbtn)
            dialoghbox.addWidget(nobtn)
            dialogvbox.addWidget(content)
            dialogvbox.addWidget(self._mfilename)
            dialogvbox.addLayout(dialoghbox)
            self._mdialog.setLayout(dialogvbox)
            self._mdialog.exec_()
            return
        self._startPrint(filename)

    def recheckfilename(self):
        if self._mfilename and ".g" in self._mfilename.text().lower():
            filename = self._mfilename.text()
            if filename in self.sdFiles:
                if self._mdialog:
                    self._mdialog.close()
                self._mdialog = QDialog()
                self._mdialog.setWindowTitle("The "+filename[filename.rfind("/")+1:]+" file already exists.")
                dialogvbox = QVBoxLayout()
                dialoghbox = QHBoxLayout()
                yesbtn = QPushButton("yes")
                nobtn = QPushButton("no")
                yesbtn.clicked.connect(self._startPrint(filename))
                nobtn.clicked.connect(self.closeMDialog)
                content = QLabel("The "+filename[filename.rfind("/")+1:]+" file already exists. Do you want to upload it?")
                self._mfilename = QLineEdit()
                self._mfilename.setText(filename[filename.rfind("/")+1:])
                dialoghbox.addWidget(yesbtn)
                dialoghbox.addWidget(nobtn)
                dialogvbox.addWidget(content)
                dialogvbox.addWidget(self._mfilename)
                dialogvbox.addLayout(dialoghbox)
                self._mdialog.setLayout(dialogvbox)
                self._mdialog.exec_()
                return
            if len(filename[filename.rfind("/")+1:]) >= 30:
                if self._mdialog:
                    self._mdialog.close()
                self._mdialog = QDialog()
                self._mdialog.setWindowTitle("File name is too long to upload, please rename it.")
                dialogvbox = QVBoxLayout()
                dialoghbox = QHBoxLayout()
                yesbtn = QPushButton("yes")
                nobtn = QPushButton("no")
                yesbtn.clicked.connect(self.recheckfilename)
                nobtn.clicked.connect(self.closeMDialog)
                content = QLabel("File name is too long to upload, please rename it.")
                self._mfilename = QLineEdit()
                self._mfilename.setText(filename[filename.rfind("/")+1:])
                dialoghbox.addWidget(yesbtn)
                dialoghbox.addWidget(nobtn)
                dialogvbox.addWidget(content)
                dialogvbox.addWidget(self._mfilename)
                dialogvbox.addLayout(dialoghbox)
                self._mdialog.setLayout(dialogvbox)
                self._mdialog.exec_()
                return
            if self.is_contains_chinese(filename[filename.rfind("/")+1:]):
                if self._mdialog:
                    self._mdialog.close()
                self._mdialog = QDialog()
                self._mdialog.setWindowTitle("File name can not include chinese, please rename it.")
                dialogvbox = QVBoxLayout()
                dialoghbox = QHBoxLayout()
                yesbtn = QPushButton("yes")
                nobtn = QPushButton("no")
                yesbtn.clicked.connect(self.recheckfilename)
                nobtn.clicked.connect(self.closeMDialog)
                content = QLabel("File name can not include chinese, please rename it.")
                self._mfilename = QLineEdit()
                self._mfilename.setText(filename[filename.rfind("/")+1:])
                dialoghbox.addWidget(yesbtn)
                dialoghbox.addWidget(nobtn)
                dialogvbox.addWidget(content)
                dialogvbox.addWidget(self._mfilename)
                dialogvbox.addLayout(dialoghbox)
                self._mdialog.setLayout(dialogvbox)
                self._mdialog.exec_()
                return
            if self.isBusy():
                if self._exception_message:
                    self._exception_message.hide()
                self._exception_message = Message(i18n_catalog.i18nc("@info:status", "File cannot be transferred during printing."))
                self._exception_message.show()
                return
            self._mdialog.close()
            self._startPrint(filename)

    def _messageBoxCallback(self, button):
        def delayedCallback():
            if button == QMessageBox.Yes:
                self.startPrint()                
            else:
                CuraApplication.getInstance().getController().setActiveStage("PrepareStage")

    def _startPrint(self, file_name="cura_file.gcode"):
        if self._mdialog:
            self._mdialog.close()
        preferences = Application.getInstance().getPreferences()
        # if preferences.getValue("KOONOVOwifi/uploadingfile"):
        if self._progress_message:
            if self._error_message is not None:
                self._error_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Error: Another file is uploading, please try later."))
            self._error_message.show()
            return
        self._preheat_timer.stop()
        self._screenShot = utils.take_screenshot()
        try:
            preferences.addPreference("KOONOVOwifi/autoprint", "True")
            preferences.addPreference("KOONOVOwifi/savepath", "")
            # preferences.addPreference("KOONOVOwifi/uploadingfile", "True")
            # CuraApplication.getInstance().showPrintMonitor.emit(True)
            # self._progress_message = Message(i18n_catalog.i18nc("@info:status", "Sending data to printer"), 0, False, -1,
            #                              i18n_catalog.i18nc("@info:title", "Sending Data"), option_text=i18n_catalog.i18nc("@label", "Print jobs")
            #                              , option_state=preferences.getValue("KOONOVOwifi/autoprint"))
            if self._application.getVersion().split(".")[0] == "4":
                self._progress_message = Message(i18n_catalog.i18nc("@info:status", "Uploading print job to printer"), 0, False, -1,
                                        i18n_catalog.i18nc("@info:title", "Sending Print Job"), option_text=i18n_catalog.i18nc("@label", "Print jobs")
                                        , option_state=preferences.getValue("KOONOVOwifi/autoprint"))
                self._progress_message.addAction("Cancel", i18n_catalog.i18nc("@action:button", "Cancel"), None, "")
                self._progress_message.actionTriggered.connect(self._cancelSendGcode)
                self._progress_message.optionToggled.connect(self._onOptionStateChanged)
            else:
                Application.getInstance().showPrintMonitor.emit(True)
                self._progress_message = Message(i18n_catalog.i18nc("@info:status", "Sending file to printer"), 0, False,
                                             -1)

            self._progress_message.show()
            # job_name = Application.getInstance().getPrintInformation().jobName.strip()
            # if job_name is "":
            #     job_name = "untitled_print"
                # job_name = "cura_file"
            # file_name = "%s.gcode" % job_name
            self._last_file_name = file_name
            Logger.log("d", "KOONOVO: "+file_name + Application.getInstance().getPrintInformation().jobName.strip())

            single_string_file_data = ""
            if self._screenShot:
                single_string_file_data += utils.add_screenshot(self._screenShot, 100, 100, ";simage:")
                single_string_file_data += utils.add_screenshot(self._screenShot, 200, 200, ";;gimage:")
                single_string_file_data += "\r"
            last_process_events = time.time()
            for line in self._gcode:
                single_string_file_data += line
                if time.time() > last_process_events + 0.05:
                    QCoreApplication.processEvents()
                    last_process_events = time.time()

            data = QByteArray()
            data.append(single_string_file_data.encode())

            # self._post_multi_part = QHttpMultiPart(QHttpMultiPart.FormDataType)
            # self._post_part = QHttpPart()
            # self._post_part.setHeader(QNetworkRequest.ContentTypeHeader, b'application/octet-stream')
            # self._post_part.setHeader(QNetworkRequest.ContentDispositionHeader,
            #                           "form-data; name=\"file\"; filename=\"%s\"" % file_name)
            # self._post_part.setBody(single_string_file_data.encode())
            # self._post_multi_part.append(self._post_part)
            post_request = QNetworkRequest(QUrl("http://%s/upload?X-Filename=%s" % (self._address, file_name)))
            post_request.setRawHeader(b'Content-Type', b'application/octet-stream')
            post_request.setRawHeader(b'Connection', b'keep-alive')
            self._post_reply = self._manager.post(post_request, data)
            self._post_reply.uploadProgress.connect(self._onUploadProgress)
            self._post_reply.sslErrors.connect(self._onUploadError)
            # Logger.log("d", "http://%s:80/upload?X-Filename=%s" % (self._address, file_name))
            self._gcode = None
        except IOError as e:
            Logger.log("e", "An exception occurred in network connection: %s" % str(e))
            self._progress_message.hide()
            self._progress_message = None
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Send file to printer failed."))
            self._error_message.show()
            self._update_timer.start()
        except Exception as e:
            self._update_timer.start()
            if self._progress_message is not None:
                self._progress_message.hide()
                self._progress_message = None
            Logger.log("e", "An exception occurred in network connection: %s" % str(e))

    def _printFile(self):
        self._sendCommand("M23 " + self._last_file_name)
        self._sendCommand("M24")

    def _onUploadProgress(self, bytes_sent, bytes_total):
        Logger.log("d", "Upload _onUploadProgress bytes_sent %s" % str(bytes_sent))
        Logger.log("d", "Upload _onUploadProgress bytes_total %s" % str(bytes_total))
        if bytes_sent == bytes_total and bytes_sent > 0:
            self._progress_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Print job was successfully sent to the printer."))
            self._error_message.show()
            CuraApplication.getInstance().getController().setActiveStage("MonitorStage")
            # preferences = Application.getInstance().getPreferences()
            # preferences.setValue("KOONOVOwifi/uploadingfile", "False")
        elif bytes_total > 0:
            new_progress = bytes_sent / bytes_total * 100
            # Treat upload progress as response. Uploading can take more than 10 seconds, so if we don't, we can get
            # timeout responses if this happens.
            self._last_response_time = time.time()
            if new_progress > self._progress_message.getProgress():
                self._progress_message.show()  # Ensure that the message is visible.
                self._progress_message.setProgress(bytes_sent / bytes_total * 100)
        # elif bytes_total == 0 and bytes_sent == 0:
        # # 此时不能判断是否失败
        #     self._progress_message.setProgress(0)
        #     self._progress_message.hide()
        #     self._error_message = Message(i18n_catalog.i18nc("@info:status", "Send file to printer failed."))
        #     self._error_message.show()                
        else: 
            # preferences = Application.getInstance().getPreferences()
            # preferences.setValue("KOONOVOwifi/uploadingfile", "False")       
            if self._progress_message is not None:    
                self._progress_message.setProgress(0)
                self._progress_message.hide()
                self._progress_message = None
            # self._error_message = Message(i18n_catalog.i18nc("@info:status", "Send file to printer failed."))
            # self._error_message.show()
            # self._update_timer.start()

    def _onUploadError(self, reply, sslerror):
        Logger.log("d", "Upload Error")
        # preferences = Application.getInstance().getPreferences()
        # preferences.setValue("KOONOVOwifi/uploadingfile", "False")
        if self._progress_message is not None:
            self._progress_message.hide()
            self._progress_message = None
        self._error_message = Message(i18n_catalog.i18nc("@info:status", "Send file to printer failed."))
        self._error_message.show()
        self._update_timer.start()

    def _setHeadPosition(self, x, y, z, speed):
        self._sendCommand("G0 X%s Y%s Z%s F%s" % (x, y, z, speed))

    def _setHeadX(self, x, speed):
        self._sendCommand("G0 X%s F%s" % (x, speed))

    def _setHeadY(self, y, speed):
        self._sendCommand("G0 Y%s F%s" % (y, speed))

    def _setHeadZ(self, z, speed):
        self._sendCommand("G0 Z%s F%s" % (z, speed))

    def _homeHead(self):
        # Logger.log("e", "_homeHead_homeHead---------------")
        self._sendCommand("G28 X Y")

    def _homeBed(self):
        self._sendCommand("G28 Z")

    def _moveHead(self, x, y, z, speed):
        self._sendCommand(["G91", "G0 X%s Y%s Z%s F%s" % (x, y, z, speed), "G90"])

    def _update(self):
        # Logger.log("d", "timer_update KOONOVO wifi reconnecting")
        preferencess = Application.getInstance().getPreferences()
        if preferencess.getValue("KOONOVOwifi/stopupdate"):
            # Logger.log("d", "timer_update KOONOVO wifi stopupdate-----------")
            self._update_timer.stop()
            return
        # Logger.log("d", "self._socket.state() %s" % self._socket.state())
        if self._socket is not None and (self._socket.state() == 2 or self._socket.state() == 3):
            # _send_data = "M105\r\nM997\r\n"
            if self._command_queue.qsize() > 0:
                _send_data = ""
            else:
                _send_data = "M105\r\nM997\r\n"
            if self.isBusy():
                _send_data += "M994\r\nM992\r\nM27\r\n"
            while self._command_queue.qsize() > 0:
                _queue_data = self._command_queue.get()
                if "M23" in _queue_data:
                    self._socket.writeData(_queue_data.encode(sys.getfilesystemencoding()))
                    continue
                if "M24" in _queue_data:
                    self._socket.writeData(_queue_data.encode(sys.getfilesystemencoding()))
                    continue
                if self.isBusy():
                    if "M20" in _queue_data:
                        # Logger.log("d", "_update M20 in _queue_data-----------: %s" % str(_queue_data))
                        continue
                _send_data += _queue_data
            Logger.log("d", "_send_data: \r\n%s" % _send_data)
            # Logger.log("d", "_send_datasys.getfilesystemencoding(): \r\n%s" % _send_data.encode(sys.getfilesystemencoding()))
            self._socket.writeData(_send_data.encode(sys.getfilesystemencoding()))
            self._socket.flush()
            # self._socket.waitForReadyRead()
        else:
            Logger.log("d", "KOONOVO wifi reconnecting")
            self.disconnect()
            self.connect()

    def _setJobState(self, job_state):
        if job_state == "abort":
            command = "M26"
        elif job_state == "print":
            if self._isPause:
                command = "M25"
            else:
                command = "M24"
        elif job_state == "pause":
            command = "M25"
        if command:
            self._sendCommand(command)

    @pyqtSlot()
    def cancelPrint(self):
        # Logger.log("e", "cancelPrint: %s" % str(self._isPause))
        self._sendCommand("M26")

    @pyqtSlot()
    def pausePrint(self):
        # if self.printers[0].state == "paused":
        # Logger.log("e", "pausePrint: %s" % str(self._isPause))
        if self._isPause:
            self._ischanging = True
            self._sendCommand("M24")
        else:
            self._sendCommand("M25")
        
        

    @pyqtSlot()
    def resumePrint(self):
        # Logger.log("e", "resumePrint: %s" % str(self._isPause))
        if self._isPause:
            self._ischanging = True
        self._sendCommand("M24")

    def on_read(self):
        if not self._socket:
            self.disconnect()
            return
        try:
            if not self._isConnect:
                self._isConnect = True
            if self._connection_state != UnifiedConnectionState.Connected:
                self._sendCommand("M20")
                self.setConnectionState(cast(ConnectionState, UnifiedConnectionState.Connected))
                self.setConnectionText(i18n_catalog.i18nc("@info:status", "TFT Connect succeed"))
            # ss = str(self._socket.readLine().data(), encoding=sys.getfilesystemencoding())
            # while self._socket.canReadLine():
                # ss = str(self._socket.readLine().data(), encoding=sys.getfilesystemencoding())
            # ss_list = ss.split("\r\n")
            # Logger.log("e", "sys.getfilesystemencoding(): %s" % str(sys.getfilesystemencoding()))
            if not self._printers:
                self._createPrinterList()
            printer = self.printers[0]
            while self._socket.canReadLine():
                
                s = str(self._socket.readLine().data(), encoding=sys.getfilesystemencoding())
                Logger.log("d", "KOONOVO recv: "+s)
                # Logger.log("d", "KOONOVO recv self._socket addr: %s" % self._socket.peerAddress)
                # self.__additional_components_view.findChild(QObject, "ManualPrinterControl").setProperty("enabled", False)
                s = s.replace("\r", "").replace("\n", "")
                # if time.time() - self.last_update_time > 10 or time.time() - self.last_update_time<-10:
                #     Logger.log("d", "KOONOVO time:"+str(self.last_update_time)+str(time.time()))
                #     self._sendCommand("M20")
                #     self.last_update_time = time.time() 
                if "T" in s and "B" in s and "T0" in s:
                    t0_temp = s[s.find("T0:") + len("T0:"):s.find("T1:")]
                    t1_temp = s[s.find("T1:") + len("T1:"):s.find("@:")]
                    bed_temp = s[s.find("B:") + len("B:"):s.find("T0:")]
                    t0_nowtemp = float(t0_temp[0:t0_temp.find("/")])
                    t0_targettemp = float(t0_temp[t0_temp.find("/") + 1:len(t0_temp)])
                    t1_nowtemp = float(t1_temp[0:t1_temp.find("/")])
                    t1_targettemp = float(t1_temp[t1_temp.find("/") + 1:len(t1_temp)])
                    bed_nowtemp = float(bed_temp[0:bed_temp.find("/")])
                    bed_targettemp = float(bed_temp[bed_temp.find("/") + 1:len(bed_temp)])
                    # cura 3.4 new api
                    printer.updateBedTemperature(bed_nowtemp)
                    printer.updateTargetBedTemperature(bed_targettemp)
                    extruder = printer.extruders[0]
                    extruder.updateTargetHotendTemperature(t0_targettemp)
                    extruder.updateHotendTemperature(t0_nowtemp)
                    # self._number_of_extruders = 1
                    # extruder = printer.extruders[1]
                    # extruder.updateHotendTemperature(t1_nowtemp)
                    # extruder.updateTargetHotendTemperature(t1_targettemp)
                    # only on lower 3.4
                    # self._setBedTemperature(bed_nowtemp)
                    # self._updateTargetBedTemperature(bed_targettemp)
                    # if self._num_extruders > 1:
                    # self._setHotendTemperature(1, t1_nowtemp)
                    # self._updateTargetHotendTemperature(1, t1_targettemp)
                    # self._setHotendTemperature(0, t0_nowtemp)
                    # self._updateTargetHotendTemperature(0, t0_targettemp)
                    continue
                if printer.activePrintJob is None:
                    print_job = PrintJobOutputModel(output_controller=self._output_controller)
                    printer.updateActivePrintJob(print_job)
                else:
                    print_job = printer.activePrintJob
                if s.startswith("M997"):
                    job_state = "offline"
                    if "IDLE" in s:
                        self._isPrinting = False
                        self._isPause = False
                        job_state = 'idle'
                        printer.acceptsCommands = True
                    elif "PRINTING" in s:
                        self._isPrinting = True
                        self._isPause = False
                        job_state = 'printing'
                        printer.acceptsCommands = False
                    elif "PAUSE" in s:
                        self._isPrinting = False
                        self._isPause = True
                        job_state = 'paused'
                        printer.acceptsCommands = False                        
                    print_job.updateState(job_state)
                    printer.updateState(job_state)
                    if self._isPrinting:
                        self._ischanging = False
                    # self._updateJobState(job_state)
                    continue
                # print_job.updateState('idle')
                # printer.updateState('idle')
                if s.startswith("M994"):
                    if self.isBusy() and s.rfind("/") != -1:
                        self._printing_filename = s[s.rfind("/") + 1:s.rfind(";")]
                    else:
                        self._printing_filename = ""
                    print_job.updateName(self._printing_filename)
                    # self.setJobName(self._printing_filename)
                    continue
                if s.startswith("M992"):
                    if self.isBusy():
                        tm = s[s.find("M992") + len("M992"):len(s)].replace(" ", "")
                        mms = tm.split(":")
                        self._printing_time = int(mms[0]) * 3600 + int(mms[1]) * 60 + int(mms[2])
                    else:
                        self._printing_time = 0
                    # Logger.log("d", self._printing_time)
                    print_job.updateTimeElapsed(self._printing_time)
                    # self.setTimeElapsed(self._printing_time)
                    # print_job.updateTimeTotal(self._printing_time)
                    # self.setTimeTotal(self._printing_time)
                    continue
                if s.startswith("M27"):
                    if self._application.getVersion().split(".")[0] == "4":
                        if self.isBusy():
                            self._printing_progress = float(s[s.find("M27") + len("M27"):len(s)].replace(" ", ""))
                            totaltime = self._printing_time/self._printing_progress*100
                        else:
                            self._printing_progress = 0
                            totaltime = self._printing_time * 100
                        # Logger.log("d", self._printing_time)
                        # Logger.log("d", totaltime)
                        # self.setProgress(self._printing_progress)
                        print_job.updateTimeTotal(self._printing_time)
                        print_job.updateTimeElapsed(self._printing_time*2-totaltime)
                    else:
                        if self.isBusy():
                            self._printing_progress = float(s[s.find("M27") + len("M27"):len(s)].replace(" ", ""))
                            totaltime = 100 / self._printing_progress * self._printing_time
                        else:
                            self._printing_progress = 0
                            totaltime = self._printing_time * 100
                        print_job.updateTimeTotal(totaltime)
                    continue
                if 'Begin file list' in s:
                    self._sdFileList = True
                    self.sdFiles = []
                    self.last_update_time = time.time()
                    continue
                if 'End file list' in s:
                    self._sdFileList = False
                    continue
                if self._sdFileList :
                    s = s.replace("\n", "").replace("\r", "")
                    if s.lower().endswith("gcode") or s.lower().endswith("gco") or s.lower.endswith("g"):
                        self.sdFiles.append(s)
                    continue
                if s.startswith("Upload"):
                    tipsname = "Send file to printer failed."
                    if self._application.getPreferences().getValue("general/language") == "zh_CN":
                        tipsname = "发送文件失败"
                    else:
                        tipsname = "Send file to printer failed."
                    if self._progress_message is not None:
                        self._progress_message.hide()
                        self._progress_message = None
                    if self._error_message is not None:
                        self._error_message.hide()
                        self._error_message = None
                    self._error_message = Message(tipsname)
                    self._error_message.show()
                    self._update_timer.start()
                    continue
        except Exception as e:
            print(e)

    def _updateTargetBedTemperature(self, temperature):
        if self._target_bed_temperature == temperature:
            return False
        self._target_bed_temperature = temperature
        self.targetBedTemperatureChanged.emit()
        return True

    def _updateTargetHotendTemperature(self, index, temperature):
        if self._target_hotend_temperatures[index] == temperature:
            return False
        self._target_hotend_temperatures[index] = temperature
        self.targetHotendTemperaturesChanged.emit()
        return True

    def _createPrinterList(self):
        printer = PrinterOutputModel(output_controller=self._output_controller, number_of_extruders=self._number_of_extruders)
        printer.updateName(self.name)
        self._printers = [printer]
        self.printersChanged.emit()

    def _onRequestFinished(self, reply):
        http_status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        self._isSending = True
        self._update_timer.start()
        self._sendCommand("M20")
        preferences = Application.getInstance().getPreferences()
        preferences.addPreference("KOONOVOwifi/autoprint", "True")
        # preferences.addPreference("KOONOVOwifi/savepath", "")
        # preferences.setValue("KOONOVOwifi/autoprint", str(self._progress_message.getOptionState()))
        if preferences.getValue("KOONOVOwifi/autoprint"):
            self._printFile()
        if not http_status_code:
            return

    def _onOptionStateChanged(self, optstate):
        preferences = Application.getInstance().getPreferences()
        preferences.setValue("KOONOVOwifi/autoprint", str(optstate))

    def _cancelSendGcode(self, message_id, action_id):
        self._update_timer.start()
        self._isSending = False
        self._progress_message.hide()
        self._post_reply.abort()
    
    def CreateKOONOVOController(self):
        Logger.log("d", "Creating additional ui components for KOONOVOcontroller.")
        # self.__additional_components_view = CuraApplication.getInstance().createQmlComponent(self._monitor_view_qml_path, {"KOONOVOcontroller": self})
        self.__additional_components_view = Application.getInstance().createQmlComponent(self._monitor_view_qml_path, {"manager": self})
        # trlist = CuraApplication.getInstance()._additional_components
        # for comp in trlist:
        Logger.log("w", "create KOONOVOcontroller ")
        if not self.__additional_components_view:
            Logger.log("w", "Could not create ui components for tft35.")
            return

    def _onGlobalContainerChanged(self) -> None:
        self._global_container_stack = Application.getInstance().getGlobalContainerStack()
        definitions = self._global_container_stack.definition.findDefinitions(key="cooling")
        Logger.log("d", definitions[0].label)
