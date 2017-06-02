import sys
import platform
import traceback
import webbrowser
import faulthandler
import tempfile
import os
import urllib

from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR, Qt, QCoreApplication
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QVBoxLayout, QLabel, QTextEdit

from UM.Logger import Logger
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

def show(exception_type, value, tb):
    Logger.log("c", "An uncaught exception has occurred!")
    for line in traceback.format_exception(exception_type, value, tb):
        for part in line.rstrip("\n").split("\n"):
            Logger.log("c", part)

    if not CuraDebugMode and exception_type not in fatal_exception_types:
        return

    application = QCoreApplication.instance()
    if not application:
        sys.exit(1)

    dialog = QDialog()
    dialog.setMinimumWidth(640)
    dialog.setMinimumHeight(640)
    dialog.setWindowTitle(catalog.i18nc("@title:window", "Crash Report"))

    layout = QVBoxLayout(dialog)

    #label = QLabel(dialog)
    #pixmap = QPixmap()
    #try:
    #    data = urllib.request.urlopen("http://www.randomkittengenerator.com/cats/rotator.php").read()
    #    pixmap.loadFromData(data)
    #except:
    #    try:
    #        from UM.Resources import Resources
    #        path = Resources.getPath(Resources.Images, "kitten.jpg")
    #        pixmap.load(path)
    #    except:
    #        pass
    #pixmap = pixmap.scaled(150, 150)
    #label.setPixmap(pixmap)
    #label.setAlignment(Qt.AlignCenter)
    #layout.addWidget(label)

    label = QLabel(dialog)
    layout.addWidget(label)

    #label.setScaledContents(True)
    label.setText(catalog.i18nc("@label", """<p>A fatal exception has occurred that we could not recover from!</p>
        <p>Please use the information below to post a bug report at <a href=\"http://github.com/Ultimaker/Cura/issues\">http://github.com/Ultimaker/Cura/issues</a></p>
    """))

    textarea = QTextEdit(dialog)
    layout.addWidget(textarea)

    try:
        from UM.Application import Application
        version = Application.getInstance().getVersion()
    except:
        version = "Unknown"

    trace = "".join(traceback.format_exception(exception_type, value, tb))

    crash_info = "Version: {0}\nPlatform: {1}\nQt: {2}\nPyQt: {3}\n\nException:\n{4}"
    crash_info = crash_info.format(version, platform.platform(), QT_VERSION_STR, PYQT_VERSION_STR, trace)

    tmp_file_fd, tmp_file_path = tempfile.mkstemp(prefix = "cura-crash", text = True)
    os.close(tmp_file_fd)
    with open(tmp_file_path, "w") as f:
        faulthandler.dump_traceback(f, all_threads=True)
    with open(tmp_file_path, "r") as f:
        data = f.read()

    msg = "-------------------------\n"
    msg += data
    crash_info += "\n\n" + msg

    textarea.setText(crash_info)

    buttons = QDialogButtonBox(QDialogButtonBox.Close, dialog)
    layout.addWidget(buttons)
    buttons.addButton(catalog.i18nc("@action:button", "Open Web Page"), QDialogButtonBox.HelpRole)
    buttons.rejected.connect(dialog.close)
    buttons.helpRequested.connect(lambda: webbrowser.open("http://github.com/Ultimaker/Cura/issues"))

    dialog.exec_()
    sys.exit(1)
