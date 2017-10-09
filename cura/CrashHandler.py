import sys
import platform
import traceback
import webbrowser
import faulthandler
import tempfile
import os

from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR, QCoreApplication
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QTextEdit, QGroupBox
from PyQt5.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkRequest, QNetworkAccessManager, QNetworkReply

from UM.Logger import Logger
from UM.View.GL.OpenGL import OpenGL
from UM.i18n import i18nCatalog

catalog = i18nCatalog("cura")

MYPY = False
if MYPY:
    CuraDebugMode = False
else:
    try:
        from cura.CuraVersion import CuraDebugMode
    except ImportError:
        CuraDebugMode = False  # [CodeStyle: Reflecting imported value]
CuraDebugMode = True ## TODO Remove when done. Just for debug purposes

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

    def __init__(self, exception_type, value, tb):

        self.exception_type = exception_type
        self.value = value
        self.traceback = tb

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
            version = Application.getInstance().getVersion()
        except:
            version = "Unknown"

        crash_info = "<b>Version:</b> {0}<br/><b>Platform:</b> {1}<br/><b>Qt:</b> {2}<br/><b>PyQt:</b> {3}<br/><b>OpenGL:</b> {4}"
        crash_info = crash_info.format(version, platform.platform(), QT_VERSION_STR, PYQT_VERSION_STR, self._getOpenGLInfo())
        label.setText(crash_info)

        layout.addWidget(label)
        group.setLayout(layout)

        return group

    def _exceptionInfoWidget(self):
        group = QGroupBox()
        group.setTitle("Exception traceback")
        layout = QVBoxLayout()

        text_area = QTextEdit()
        trace = "".join(traceback.format_exception(self.exception_type, self.value, self.traceback))
        text_area.setText(trace)

        layout.addWidget(text_area)
        group.setLayout(layout)

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
            data = f.read()

        text_area.setText(data)

        layout.addWidget(text_area)
        group.setLayout(layout)

        return group


    def _userDescriptionWidget(self):
        group = QGroupBox()
        group.setTitle("User description")
        layout = QVBoxLayout()

        text_area = QTextEdit()

        layout.addWidget(text_area)
        group.setLayout(layout)

        return group

    def _buttonsWidget(self):
        buttons = QDialogButtonBox()
        buttons.addButton(QDialogButtonBox.Close)
        buttons.addButton(catalog.i18nc("@action:button", "Send to developers"), QDialogButtonBox.AcceptRole)
        buttons.rejected.connect(self.dialog.close)
        buttons.accepted.connect(self._sendCrashReport)

        return buttons

    def _getOpenGLInfo(self):
        info = "<ul><li>OpenGL Version: {0}</li><li>OpenGL Vendor: {1}</li><li>OpenGL Renderer: {2}</li></ul>"
        info =  info.format(OpenGL.getInstance().getGPUVersion(), OpenGL.getInstance().getGPUVendorName(), OpenGL.getInstance().getGPUType())
        return info

    def _sendCrashReport(self):
        print("Hello")
        # _manager = QNetworkAccessManager()
        # api_url = QUrl("url")
        # put_request = QNetworkRequest(api_url)
        # put_request.setHeader(QNetworkRequest.ContentTypeHeader, "text/plain")
        # _manager.put(put_request, crash_info.encode())
        #
        # sys.exit(1)

    def show(self):
        self.dialog.exec_()
        sys.exit(1)