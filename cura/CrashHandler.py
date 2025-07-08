#  Copyright (c) 2022 UltiMaker
#  Cura is released under the terms of the LGPLv3 or higher.

import platform
import traceback
import faulthandler
import tempfile
import os
import os.path
import uuid
import json
import locale
from typing import cast, Any

try:
    from sentry_sdk.hub import Hub
    from sentry_sdk.utils import event_from_exception
    from sentry_sdk import configure_scope, add_breadcrumb
    with_sentry_sdk = True
except ImportError:
    with_sentry_sdk = False

from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR, QUrl
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QTextEdit, QGroupBox, QCheckBox, QPushButton
from PyQt6.QtGui import QDesktopServices, QTextCursor

from UM.Application import Application
from UM.Logger import Logger
from UM.View.GL.OpenGL import OpenGL
from UM.i18n import i18nCatalog
from UM.Resources import Resources
from cura import ApplicationMetadata

catalog = i18nCatalog("cura")
home_dir = os.path.expanduser("~")


MYPY = False
if MYPY:
    CuraDebugMode = False
else:
    try:
        from cura.CuraVersion import CuraDebugMode
    except ImportError:
        CuraDebugMode = False  # [CodeStyle: Reflecting imported value]

# List of exceptions that should not be considered "fatal" and abort the program.
# These are primarily some exception types that we simply skip
skip_exception_types = [
    SystemExit,
    KeyboardInterrupt,
    GeneratorExit
]


class CrashHandler:
    def __init__(self, exception_type, value, tb, has_started = True):
        self.exception_type = exception_type
        self.value = value
        self.traceback = tb
        self.has_started = has_started
        self.dialog = None # Don't create a QDialog before there is a QApplication
        self.cura_version = None
        self.cura_locale = None

        Logger.log("c", "An uncaught error has occurred!")
        for line in traceback.format_exception(exception_type, value, tb):
            for part in line.rstrip("\n").split("\n"):
                Logger.log("c", part)
        self.data = {}
        # If Cura has fully started, we only show fatal errors.
        # If Cura has not fully started yet, we always show the early crash dialog. Otherwise, Cura will just crash
        # without any information.
        if has_started and exception_type in skip_exception_types:
            return

        if with_sentry_sdk:
            with configure_scope() as scope:
                scope.set_tag("during_startup", not has_started)

        if not has_started:
            self._send_report_checkbox = None
            self.early_crash_dialog = self._createEarlyCrashDialog()

        self.dialog = QDialog()
        self._createDialog()

    @staticmethod
    def pruneSensitiveData(obj: Any) -> Any:
        if isinstance(obj, str):
            return obj.replace("\\\\", "\\").replace(home_dir, "<user_home>")
        if isinstance(obj, list):
            return [CrashHandler.pruneSensitiveData(item) for item in obj]
        if isinstance(obj, dict):
            return {k: CrashHandler.pruneSensitiveData(v) for k, v in obj.items()}

        return obj

    @staticmethod
    def sentryBeforeSend(event, hint):
        return CrashHandler.pruneSensitiveData(event)

    def _createEarlyCrashDialog(self):
        dialog = QDialog()
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(170)
        dialog.setWindowTitle(catalog.i18nc("@title:window", "Cura can't start"))
        dialog.finished.connect(self._closeEarlyCrashDialog)

        layout = QVBoxLayout(dialog)

        label = QLabel()
        label.setText(catalog.i18nc("@label crash message", """<p><b>Oops, UltiMaker Cura has encountered something that doesn't seem right.</p></b>
                    <p>We encountered an unrecoverable error during start up. It was possibly caused by some incorrect configuration files. We suggest to backup and reset your configuration.</p>
                    <p>Backups can be found in the configuration folder.</p>
                    <p>Please send us this Crash Report to fix the problem.</p>
                """))
        label.setWordWrap(True)
        layout.addWidget(label)

        # "send report" check box and show details
        self._send_report_checkbox = QCheckBox(catalog.i18nc("@action:button", "Send crash report to UltiMaker"), dialog)
        self._send_report_checkbox.setChecked(True)

        show_details_button = QPushButton(catalog.i18nc("@action:button", "Show detailed crash report"), dialog)
        show_details_button.setMaximumWidth(200)
        show_details_button.clicked.connect(self._showDetailedReport)

        show_configuration_folder_button = QPushButton(catalog.i18nc("@action:button", "Show configuration folder"), dialog)
        show_configuration_folder_button.setMaximumWidth(200)
        show_configuration_folder_button.clicked.connect(self._showConfigurationFolder)

        layout.addWidget(self._send_report_checkbox)
        layout.addWidget(show_details_button)
        layout.addWidget(show_configuration_folder_button)

        # "backup and start clean" and "close" buttons
        buttons = QDialogButtonBox()
        buttons.addButton(QDialogButtonBox.StandardButton.Close)
        buttons.addButton(catalog.i18nc("@action:button", "Backup and Reset Configuration"), QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.rejected.connect(self._closeEarlyCrashDialog)
        buttons.accepted.connect(self._backupAndStartClean)

        layout.addWidget(buttons)

        return dialog

    def _closeEarlyCrashDialog(self):
        if self._send_report_checkbox.isChecked():
            self._sendCrashReport()
        os._exit(1)

    def _backupAndStartClean(self):
        """Backup the current resource directories and create clean ones."""

        Resources.factoryReset()
        self.early_crash_dialog.close()

    def _showConfigurationFolder(self):
        path = Resources.getConfigStoragePath()
        QDesktopServices.openUrl(QUrl.fromLocalFile( path ))

    def _showDetailedReport(self):
        self.dialog.exec()

    def _createDialog(self):
        """Creates a modal dialog."""

        self.dialog.setMinimumWidth(640)
        self.dialog.setMinimumHeight(640)
        self.dialog.setWindowTitle(catalog.i18nc("@title:window", "Crash Report"))
        # if the application has not fully started, this will be a detailed report dialog which should not
        # close the application when it's closed.
        if self.has_started:
            self.dialog.finished.connect(self._close)

        layout = QVBoxLayout(self.dialog)

        layout.addWidget(self._messageWidget())
        layout.addWidget(self._informationWidget())
        layout.addWidget(self._exceptionInfoWidget())
        layout.addWidget(self._logInfoWidget())
        layout.addWidget(self._buttonsWidget())

    def _close(self):
        os._exit(1)

    def _messageWidget(self):
        label = QLabel()
        label.setText(catalog.i18nc("@label crash message", """<p><b>A fatal error has occurred in Cura. Please send us this Crash Report to fix the problem</p></b>
            <p>Please use the "Send report" button to post a bug report automatically to our servers</p>
        """))

        return label

    def _informationWidget(self):
        group = QGroupBox()
        group.setTitle(catalog.i18nc("@title:groupbox", "System information"))
        layout = QVBoxLayout()
        label = QLabel()

        try:
            from UM.Application import Application
            self.cura_version = Application.getInstance().getVersion()
            self.cura_locale = Application.getInstance().getPreferences().getValue("general/language")
        except:
            self.cura_version = catalog.i18nc("@label unknown version of Cura", "Unknown")
            self.cura_locale = "??_??"

        self.data["cura_version"] = self.cura_version
        self.data["os"] = {"type": platform.system(), "version": platform.version()}
        self.data["qt_version"] = QT_VERSION_STR
        self.data["pyqt_version"] = PYQT_VERSION_STR
        self.data["locale_os"] = locale.getlocale(locale.LC_MESSAGES)[0] if hasattr(locale, "LC_MESSAGES") else \
        locale.getdefaultlocale()[0]
        self.data["locale_cura"] = self.cura_locale

        try:
            from cura.CuraApplication import CuraApplication
            plugins = CuraApplication.getInstance().getPluginRegistry()
            self.data["plugins"] = {
                plugin_id: plugins.getMetaData(plugin_id)["plugin"]["version"]
                for plugin_id in plugins.getInstalledPlugins() if not plugins.isBundledPlugin(plugin_id)
            }
        except:
            self.data["plugins"] = {"[FAILED]": "0.0.0"}

        crash_info = "<b>" + catalog.i18nc("@label Cura version number", "Cura version") + ":</b> " + str(self.cura_version) + "<br/>"
        crash_info += "<b>" + catalog.i18nc("@label", "Cura language") + ":</b> " + str(self.cura_locale) + "<br/>"
        crash_info += "<b>" + catalog.i18nc("@label", "OS language") + ":</b> " + str(self.data["locale_os"]) + "<br/>"
        crash_info += "<b>" + catalog.i18nc("@label Type of platform", "Platform") + ":</b> " + str(platform.platform()) + "<br/>"
        crash_info += "<b>" + catalog.i18nc("@label", "Qt version") + ":</b> " + str(QT_VERSION_STR) + "<br/>"
        crash_info += "<b>" + catalog.i18nc("@label", "PyQt version") + ":</b> " + str(PYQT_VERSION_STR) + "<br/>"
        crash_info += "<b>" + catalog.i18nc("@label OpenGL version", "OpenGL") + ":</b> " + str(self._getOpenGLInfo()) + "<br/>"

        label.setText(crash_info)

        layout.addWidget(label)
        group.setLayout(layout)

        if with_sentry_sdk:
            with configure_scope() as scope:
                scope.set_tag("qt_version", QT_VERSION_STR)
                scope.set_tag("pyqt_version", PYQT_VERSION_STR)
                scope.set_tag("os", platform.system())
                scope.set_tag("os_version", platform.version())
                scope.set_tag("locale_os", self.data["locale_os"])
                scope.set_tag("locale_cura", self.cura_locale)
                scope.set_tag("is_enterprise", ApplicationMetadata.IsEnterpriseVersion)

                scope.set_context("plugins", self.data["plugins"])

                user_id = uuid.getnode()  # On all of Cura's supported platforms, this returns the MAC address which is pseudonymical information (!= anonymous).
                user_id %= 2 ** 16  # So to make it anonymous, apply a bitmask selecting only the last 16 bits.
                                    # This prevents it from being traceable to a specific user but still gives somewhat of an idea of whether it's just the same user hitting the same crash over and over again, or if it's widespread.
                scope.set_user({"id": str(user_id)})

        return group

    def _getOpenGLInfo(self):
        opengl_instance = OpenGL.getInstance()
        if not opengl_instance:
            self.data["opengl"] = {"version": "n/a", "vendor": "n/a", "type": "n/a"}
            return catalog.i18nc("@label", "Not yet initialized") + "<br />"

        info = "<ul>"
        info += catalog.i18nc("@label OpenGL version", "<li>OpenGL Version: {version}</li>").format(version=opengl_instance.getOpenGLVersion())
        info += catalog.i18nc("@label OpenGL vendor", "<li>OpenGL Vendor: {vendor}</li>").format(vendor=opengl_instance.getGPUVendorName())
        info += catalog.i18nc("@label OpenGL renderer", "<li>OpenGL Renderer: {renderer}</li>").format(renderer=opengl_instance.getGPUType())
        info += "</ul>"

        self.data["opengl"] = {"version": opengl_instance.getOpenGLVersion(), "vendor": opengl_instance.getGPUVendorName(), "type": opengl_instance.getGPUType()}

        active_machine_definition_id = "unknown"
        active_machine_manufacturer = "unknown"

        try:
            from cura.CuraApplication import CuraApplication
            application = cast(CuraApplication, Application.getInstance())
            machine_manager = application.getMachineManager()
            global_stack = machine_manager.activeMachine
            if global_stack is None:
                active_machine_definition_id = "empty"
                active_machine_manufacturer = "empty"
            else:
                active_machine_definition_id = global_stack.definition.getId()
                active_machine_manufacturer = global_stack.definition.getMetaDataEntry("manufacturer", "unknown")
        except:
            pass

        if with_sentry_sdk:
            with configure_scope() as scope:
                scope.set_tag("opengl_version", opengl_instance.getOpenGLVersion())
                scope.set_tag("opengl_version_short", opengl_instance.getOpenGLVersionShort())
                scope.set_tag("gpu_vendor", opengl_instance.getGPUVendorName())
                scope.set_tag("gpu_type", opengl_instance.getGPUType())
                scope.set_tag("active_machine", active_machine_definition_id)
                scope.set_tag("active_machine_manufacturer", active_machine_manufacturer)

        return info

    def _exceptionInfoWidget(self):
        group = QGroupBox()
        group.setTitle(catalog.i18nc("@title:groupbox", "Error traceback"))
        layout = QVBoxLayout()

        text_area = QTextEdit()
        trace_list = traceback.format_exception(self.exception_type, self.value, self.traceback)
        trace = "".join(trace_list)
        text_area.setText(trace)
        text_area.setReadOnly(True)
        text_area.moveCursor(QTextCursor.MoveOperation.End)  # Move cursor to end, so we see last bit of the exception
        layout.addWidget(text_area)
        group.setLayout(layout)

        # Parsing all the information to fill the dictionary
        summary = ""
        if len(trace_list) >= 1:
            summary = trace_list[len(trace_list)-1].rstrip("\n")
        module = [""]
        if len(trace_list) >= 2:
            module = trace_list[len(trace_list)-2].rstrip("\n").split("\n")
        module_split = module[0].split(", ")

        filepath_directory_split = module_split[0].split("\"")
        filepath = ""
        if len(filepath_directory_split) > 1:
            filepath = filepath_directory_split[1]
        directory, filename = os.path.split(filepath)
        line = ""
        if len(module_split) > 1:
            line = int(module_split[1].lstrip("line "))
        function = ""
        if len(module_split) > 2:
            function = module_split[2].lstrip("in ")
        code = ""
        if len(module) > 1:
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
                with open(json_metadata_file, "r", encoding="utf-8") as f:
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

        if with_sentry_sdk:
            with configure_scope() as scope:
                scope.set_tag("is_plugin", isPlugin)
                scope.set_tag("module", module_name)

        return group

    def _logInfoWidget(self):
        group = QGroupBox()
        group.setTitle(catalog.i18nc("@title:groupbox", "Logs"))
        layout = QVBoxLayout()

        text_area = QTextEdit()
        tmp_file_fd, tmp_file_path = tempfile.mkstemp(prefix="cura-crash", text=True)
        os.close(tmp_file_fd)
        with open(tmp_file_path, "w", encoding="utf-8") as f:
            faulthandler.dump_traceback(f, all_threads=True)
        with open(tmp_file_path, "r", encoding="utf-8") as f:
            logdata = f.read()

        text_area.setText(logdata)
        text_area.setReadOnly(True)
        text_area.moveCursor(QTextCursor.MoveOperation.End)  # Move cursor to end, so we see last bit of the log
        layout.addWidget(text_area)
        group.setLayout(layout)

        self.data["log"] = logdata

        return group

    def _buttonsWidget(self):
        buttons = QDialogButtonBox()
        buttons.addButton(QDialogButtonBox.StandardButton.Close)
        # Like above, this will be served as a separate detailed report dialog if the application has not yet been
        # fully loaded. In this case, "send report" will be a check box in the early crash dialog, so there is no
        # need for this extra button.
        if self.has_started:
            buttons.addButton(catalog.i18nc("@action:button", "Send report"), QDialogButtonBox.ButtonRole.AcceptRole)
            buttons.accepted.connect(self._sendCrashReport)
        buttons.rejected.connect(self.dialog.close)

        return buttons

    def _sendCrashReport(self):
        if with_sentry_sdk:
            try:
                hub = Hub.current
                if not Logger.getLoggers():
                    # No loggers have been loaded yet, so we don't have any breadcrumbs :(
                    # So add them manually so we at least have some info...
                    add_breadcrumb(level="info", message="SentryLogging was not initialised yet")
                    for log_type, line in Logger.getUnloggedLines():
                        add_breadcrumb(message=line)

                event, hint = event_from_exception((self.exception_type, self.value, self.traceback))
                hub.capture_event(event, hint=hint)
                hub.flush()
            except Exception as e:  # We don't want any exception to cause problems
                Logger.logException("e", "An exception occurred while trying to send crash report")
                if not self.has_started:
                    print("An exception occurred while trying to send crash report: %s" % e)
        else:
            msg = "SentrySDK is not available and the report could not be sent."
            Logger.logException("e", msg)
            if not self.has_started:
                print(msg)
                print("Exception type: {}".format(self.exception_type))
                print("Value: {}".format(self.value))
                print("Traceback: {}".format(self.traceback))

        os._exit(1)

    def show(self):
        # must run the GUI code on the Qt thread, otherwise the widgets on the dialog won't react correctly.
        Application.getInstance().callLater(self._show)

    def _show(self):
        # When the exception is in the skip_exception_types list, the dialog is not created, so we don't need to show it
        if self.dialog:
            self.dialog.exec()
        os._exit(1)
