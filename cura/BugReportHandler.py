
import os
import os.path
import platform
from collections import OrderedDict

from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR, QUrl
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QTextEdit, QGroupBox, QCheckBox, \
    QPushButton, QPlainTextEdit, QLineEdit
from PyQt5.QtGui import QDesktopServices, QTextCursor

from UM.Application import Application
from UM.Logger import Logger
from UM.View.GL.OpenGL import OpenGL
from UM.i18n import i18nCatalog
from UM.Resources import Resources
from cura import ApplicationMetadata

catalog = i18nCatalog("cura")
home_dir = os.path.expanduser("~")


class BugReportHandler:
    def __init__(self):
        from cura.CuraApplication import CuraApplication
        self._application = CuraApplication.getInstance()
        self.machine_manager = self._application.getMachineManager()
        self.global_stack = self.machine_manager.activeMachine
        self.data = OrderedDict([
            ("cura_version", {"header": "Application Version", "content": "Cura {}".format(self._application.getVersion())}),
            ("platform", {"header": "Platform", "content": "{} {}".format(platform.system(), platform.release())}),
            ("printer", {"header": "Printer", "content": "Type: {}, Manufacturer: {}".format(self.global_stack.getDefinition().getName(), self.global_stack.getDefinition().getMetaDataEntry("manufacturer", "unknown")) }),
            ("reproduction_steps", {"header": "Reproduction Steps", "content": "1. (Step 1:...)\n2. (Step 2:...)"}),
            ("screenshots", {"header": "Screenshots", "content": "(Image showing the problem, perhaps before/after images.) "}),
            ("actual_results", {"header": "Actual Results", "content": "(What happens after the above steps have been followed.)"}),
            ("expected_results", {"header": "Expected Results", "content": "(What should happen after the above steps have been followed.)"}),
            ("project_file", {"header": "Project file", "content": "(For slicing bugs, provide a project which clearly shows the bug, by going to File->Save. For big files you may need to use WeTransfer or similar file sharing sites.)"}),
            ("log_file", {"header": "Log File", "content": "(See https://github.com/Ultimaker/Cura#logging-issues to find the log file to upload, or copy a relevant snippet from it.)"}),
            ("additional_information", {"header": "Additional Information", "content": "(Extra information relevant to the issue.)"}),
        ])
        self.machine_manager = self._application.getMachineManager()
        self.global_stack = self.machine_manager.activeMachine
        if ApplicationMetadata.CuraBuildType != "":
            self.data["cura_version"]["content"] += ", Build Type: " + ApplicationMetadata.CuraBuildType
        self.dialog = QDialog() # Don't create a QDialog before there is a QApplication
        self._createDialog()

    def _createDialog(self):
        self.dialog.setMinimumWidth(640)
        self.dialog.setMinimumHeight(640)
        self.dialog.setWindowTitle(catalog.i18nc("@title:window", "Bug Report Template"))
        layout = QVBoxLayout(self.dialog)

        layout.addWidget(self._prefilledInfoWidget())
        reproduction_label, self.reproduction_steps_textbox = self._createTextBoxWithLabel(self.data["reproduction_steps"])
        layout.addWidget(reproduction_label)
        layout.addWidget(self.reproduction_steps_textbox)

        actual_results_label, self.actual_results_textbox = self._createTextBoxWithLabel(self.data["actual_results"])
        layout.addWidget(actual_results_label)
        layout.addWidget(self.actual_results_textbox)

        expected_results_label, self.expected_results_textbox = self._createTextBoxWithLabel(self.data["expected_results"])
        layout.addWidget(expected_results_label)
        layout.addWidget(self.expected_results_textbox)

        additional_information_label, self.additional_information_textbox,  = self._createTextBoxWithLabel(self.data["additional_information"])
        layout.addWidget(additional_information_label)
        layout.addWidget(self.additional_information_textbox)
        # layout.addWidget(self._exceptionInfoWidget())
        # layout.addWidget(self._logInfoWidget())
        # layout.addWidget(self._buttonsWidget())

    def _prefilledInfoWidget(self):
        group = QGroupBox()
        # layout = QVBoxLayout()
        label = QLabel()
        prefilled_info = "<b>{}</b><br/> {}<br/><br/>".format(self.data["cura_version"]["header"], self.data["cura_version"]["content"])
        prefilled_info += "<b>{}</b><br/> {}<br/><br/>".format(self.data["platform"]["header"], self.data["platform"]["content"])
        prefilled_info += "<b>{}</b><br/> {}<br/><br/>".format(self.data["printer"]["header"], self.data["printer"]["content"])

        label.setText(prefilled_info)
        # layout.addWidget(label)
        return label

    @staticmethod
    def _createTextBoxWithLabel(item):
        label = QLabel()
        label.setText(item["header"])
        text_area = QPlainTextEdit()
        # text_area.setCursor(QTextCursor())
        text_area.setPlainText(item["content"])
        return label, text_area

    def show(self):
        # must run the GUI code on the Qt thread, otherwise the widgets on the dialog won't react correctly.
        self._application.callLater(self._show)

    def _show(self):
        # When the exception is in the skip_exception_types list, the dialog is not created, so we don't need to show it
        if self.dialog:
            self.dialog.exec_()