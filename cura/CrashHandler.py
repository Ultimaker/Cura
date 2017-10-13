import sys
import platform
import traceback
import webbrowser
import faulthandler
import tempfile
import os
import os.path
import time
import json
import ssl
import urllib.request
import urllib.error

from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR, QCoreApplication, Qt
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QTextEdit, QGroupBox

from UM.Logger import Logger
from UM.PluginError import InvalidMetaDataError
from UM.PluginRegistry import PluginRegistry
from UM.View.GL.OpenGL import OpenGL
from UM.i18n import i18nCatalog
from UM.Platform import Platform

catalog = i18nCatalog("cura")

MYPY = False
if MYPY:
    CuraDebugMode = False
else:
    try:
        from cura.CuraVersion import CuraDebugMode
    except ImportError:
        CuraDebugMode = False  # [CodeStyle: Reflecting imported value]

# List of exceptions that should be considered "fatal" and abort the program.
# These are primarily some exception types that we simply cannot really recover from
# (MemoryError and SystemError) and exceptions that indicate grave errors in the
# code that cause the Python interpreter to fail (SyntaxError, ImportError). 
fatal_exception_types = [
    MemoryError,
    SyntaxError,
    ImportError,
    SystemError,
]

class CrashHandler:
    crash_url = "https://stats.ultimaker.com/api/cura"

    def __init__(self, exception_type, value, tb):

        self.exception_type = exception_type
        self.value = value
        self.traceback = tb

        # While we create the GUI, the information will be stored for sending afterwards
        self.data = dict()
        self.data["time_stamp"] = time.time()

        Logger.log("c", "An uncaught exception has occurred!")
        for line in traceback.format_exception(exception_type, value, tb):
            for part in line.rstrip("\n").split("\n"):
                Logger.log("c", part)

        if not CuraDebugMode and exception_type not in fatal_exception_types:
            return

        application = QCoreApplication.instance()
        if not application:
            sys.exit(1)

        self._createDialog()

    ##  Creates a modal dialog.
    def _createDialog(self):

        self.dialog = QDialog()
        self.dialog.setMinimumWidth(640)
        self.dialog.setMinimumHeight(640)
        self.dialog.setWindowTitle(catalog.i18nc("@title:window", "Crash Report"))

        layout = QVBoxLayout(self.dialog)

        layout.addWidget(self._messageWidget())
        layout.addWidget(self._informationWidget())
        layout.addWidget(self._exceptionInfoWidget())
        layout.addWidget(self._logInfoWidget())
        layout.addWidget(self._userDescriptionWidget())
        layout.addWidget(self._buttonsWidget())

    def _messageWidget(self):
        label = QLabel()
        label.setText(catalog.i18nc("@label", """<p><b>A fatal exception has occurred that we could not recover from!</p></b>
            <p>Please use the button below to post a bug report automatically to our servers</p>
        """))

        return label

    def _informationWidget(self):
        group = QGroupBox()
        group.setTitle("System information")
        layout = QVBoxLayout()
        label = QLabel()

        try:
            from UM.Application import Application
            self.cura_version = Application.getInstance().getVersion()
        except:
            self.cura_version = "Unknown"

        crash_info = "<b>Version:</b> {0}<br/><b>Platform:</b> {1}<br/><b>Qt:</b> {2}<br/><b>PyQt:</b> {3}<br/><b>OpenGL:</b> {4}"
        crash_info = crash_info.format(self.cura_version, platform.platform(), QT_VERSION_STR, PYQT_VERSION_STR, self._getOpenGLInfo())
        label.setText(crash_info)

        layout.addWidget(label)
        group.setLayout(layout)

        self.data["cura_version"] = self.cura_version
        self.data["os"] = {"type": platform.system(), "version": platform.version()}
        self.data["qt_version"] = QT_VERSION_STR
        self.data["pyqt_version"] = PYQT_VERSION_STR

        return group

    def _getOpenGLInfo(self):
        info = "<ul><li>OpenGL Version: {0}</li><li>OpenGL Vendor: {1}</li><li>OpenGL Renderer: {2}</li></ul>"
        info =  info.format(OpenGL.getInstance().getOpenGLVersion(), OpenGL.getInstance().getGPUVendorName(), OpenGL.getInstance().getGPUType())

        self.data["opengl"] = {"version": OpenGL.getInstance().getOpenGLVersion(), "vendor": OpenGL.getInstance().getGPUVendorName(), "type": OpenGL.getInstance().getGPUType()}

        return info

    def _exceptionInfoWidget(self):
        group = QGroupBox()
        group.setTitle("Exception traceback")
        layout = QVBoxLayout()

        text_area = QTextEdit()
        trace_dict = traceback.format_exception(self.exception_type, self.value, self.traceback)
        trace = "".join(trace_dict)
        text_area.setText(trace)
        text_area.setReadOnly(True)

        layout.addWidget(text_area)
        group.setLayout(layout)

        # Parsing all the information to fill the dictionary
        summary = trace_dict[len(trace_dict)-1].rstrip("\n")
        module = trace_dict[len(trace_dict)-2].rstrip("\n").split("\n")
        module_split = module[0].split(", ")
        filepath = module_split[0].split("\"")[1]
        directory, filename = os.path.split(filepath)
        line = int(module_split[1].lstrip("line "))
        function = module_split[2].lstrip("in ")
        code = module[1].lstrip(" ")

        # Using this workaround for a cross-platform path splitting
        split_path = []
        folder_name = ""
        # Split until reach folder "cura"
        while folder_name != "cura":
            directory, folder_name = os.path.split(directory)
            if not folder_name:
                break
            split_path.append(folder_name)

        # Look for plugins. If it's not a plugin, the current cura version is set
        isPlugin = False
        module_version = self.cura_version
        module_name = "Cura"
        if split_path.__contains__("plugins"):
            isPlugin = True
            # Look backwards until plugin.json is found
            directory, name = os.path.split(filepath)
            while not os.listdir(directory).__contains__("plugin.json"):
                directory, name = os.path.split(directory)

            json_metadata_file = os.path.join(directory, "plugin.json")
            try:
                with open(json_metadata_file, "r") as f:
                    try:
                        metadata = json.loads(f.read())
                        module_version = metadata["version"]
                        module_name = metadata["name"]
                    except json.decoder.JSONDecodeError:
                        # Not throw new exceptions
                        Logger.logException("e", "Failed to parse plugin.json for plugin %s", name)
            except:
                # Not throw new exceptions
                pass

        exception_dict = dict()
        exception_dict["traceback"] = {"summary": summary, "full_trace": trace}
        exception_dict["location"] = {"path": filepath, "file": filename, "function": function, "code": code, "line": line,
                                      "module_name": module_name, "version": module_version, "is_plugin": isPlugin}
        self.data["exception"] = exception_dict

        return group

    def _logInfoWidget(self):
        group = QGroupBox()
        group.setTitle("Logs")
        layout = QVBoxLayout()

        text_area = QTextEdit()
        tmp_file_fd, tmp_file_path = tempfile.mkstemp(prefix = "cura-crash", text = True)
        os.close(tmp_file_fd)
        with open(tmp_file_path, "w") as f:
            faulthandler.dump_traceback(f, all_threads=True)
        with open(tmp_file_path, "r") as f:
            logdata = f.read()

        text_area.setText(logdata)
        text_area.setReadOnly(True)

        layout.addWidget(text_area)
        group.setLayout(layout)

        self.data["log"] = logdata

        return group


    def _userDescriptionWidget(self):
        group = QGroupBox()
        group.setTitle("User description")
        layout = QVBoxLayout()

        # When sending the report, the user comments will be collected
        self.user_description_text_area = QTextEdit()
        self.user_description_text_area.setFocus(True)

        layout.addWidget(self.user_description_text_area)
        group.setLayout(layout)

        return group

    def _buttonsWidget(self):
        buttons = QDialogButtonBox()
        buttons.addButton(QDialogButtonBox.Close)
        buttons.addButton(catalog.i18nc("@action:button", "Send to developers"), QDialogButtonBox.AcceptRole)
        buttons.rejected.connect(self.dialog.close)
        buttons.accepted.connect(self._sendCrashReport)

        return buttons

    def _sendCrashReport(self):
        # Before sending data, the user comments are stored
        self.data["user_info"] = self.user_description_text_area.toPlainText()

        # Convert data to bytes
        binary_data = json.dumps(self.data).encode("utf-8")

        # Submit data
        kwoptions = {"data": binary_data, "timeout": 5}

        if Platform.isOSX():
            kwoptions["context"] = ssl._create_unverified_context()

        Logger.log("i", "Sending crash report info to [%s]...", self.crash_url)

        try:
            f = urllib.request.urlopen(self.crash_url, **kwoptions)
            Logger.log("i", "Sent crash report info.")
            f.close()
        except urllib.error.HTTPError:
            Logger.logException("e", "An HTTP error occurred while trying to send crash report")
        except Exception:  # We don't want any exception to cause problems
            Logger.logException("e", "An exception occurred while trying to send crash report")

        sys.exit(1)

    def show(self):
        self.dialog.exec_()
        sys.exit(1)