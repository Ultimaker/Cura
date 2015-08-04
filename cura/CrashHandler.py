import sys
import platform
import traceback
import webbrowser

from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR, QCoreApplication
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QTextEdit

def show(type, value, tb):
    application = QCoreApplication.instance()
    if not application:
        traceback.print_exception(type, value, tb)
        exit(1)

    dialog = QDialog()
    dialog.setWindowTitle("Oops!")

    layout = QVBoxLayout(dialog)

    label = QLabel(dialog)
    layout.addWidget(label)
    label.setText("<p>An uncaught exception has occurred!</p><p>Please use the information below to post a bug report at <a href=\"http://github.com/Ultimaker/Cura/issues\">http://github.com/Ultimaker/Cura/issues</a></p>")

    textarea = QTextEdit(dialog)
    layout.addWidget(textarea)

    try:
        from UM.Application import Application
        version = Application.getInstance().getVersion()
    except:
        version = "Unknown"

    trace = "".join(traceback.format_exception(type, value, tb))

    crash_info = "Version: {0}\nPlatform: {1}\nQt: {2}\nPyQt: {3}\n\nException:\n{4}"
    crash_info = crash_info.format(version, platform.platform(), QT_VERSION_STR, PYQT_VERSION_STR, trace)

    textarea.setText(crash_info)

    buttons = QDialogButtonBox(QDialogButtonBox.Close, dialog)
    layout.addWidget(buttons)
    buttons.addButton("Open Web Page", QDialogButtonBox.HelpRole)
    buttons.rejected.connect(lambda: dialog.close())
    buttons.helpRequested.connect(lambda: webbrowser.open("http://github.com/Ultimaker/Cura/issues"))

    dialog.exec_()
    exit(1)
