from PyQt5.QtCore import Qt, QUrl, pyqtSignal, pyqtSlot, QObject, pyqtProperty, QCoreApplication
from PyQt5.QtQml import QQmlComponent, QQmlContext
from UM.PluginRegistry import PluginRegistry
from UM.Application import Application
from UM.Logger import Logger

import os
import threading
import time

class WorkspaceDialog(QObject):
    showDialogSignal = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)
        self._component = None
        self._context = None
        self._view = None
        self._qml_url = "WorkspaceDialog.qml"
        self._lock = threading.Lock()
        self._default_strategy = "override"
        self._result = {"machine": self._default_strategy,
                        "quality_changes": self._default_strategy,
                        "material": self._default_strategy}
        self._visible = False
        self.showDialogSignal.connect(self.__show)

        self._has_quality_changes_conflict = False
        self._has_machine_conflict = False
        self._has_material_conflict = False

    machineConflictChanged = pyqtSignal()
    qualityChangesConflictChanged = pyqtSignal()
    materialConflictChanged = pyqtSignal()

    @pyqtProperty(bool, notify = machineConflictChanged)
    def machineConflict(self):
        return self._has_machine_conflict

    @pyqtProperty(bool, notify=qualityChangesConflictChanged)
    def qualityChangesConflict(self):
        return self._has_quality_changes_conflict

    @pyqtProperty(bool, notify=materialConflictChanged)
    def materialConflict(self):
        return self._has_material_conflict

    @pyqtSlot(str, str)
    def setResolveStrategy(self, key, strategy):
        if key in self._result:
            self._result[key] = strategy

    def setMaterialConflict(self, material_conflict):
        self._has_material_conflict = material_conflict
        self.materialConflictChanged.emit()

    def setMachineConflict(self, machine_conflict):
        self._has_machine_conflict = machine_conflict
        self.machineConflictChanged.emit()

    def setQualityChangesConflict(self, quality_changes_conflict):
        self._has_quality_changes_conflict = quality_changes_conflict
        self.qualityChangesConflictChanged.emit()

    def getResult(self):
        if "machine" in self._result and not self._has_machine_conflict:
            self._result["machine"] = None
        if "quality_changes" in self._result and not self._has_quality_changes_conflict:
            self._result["quality_changes"] = None
        if "material" in self._result and not self._has_material_conflict:
            self._result["material"] = None
        return self._result

    def _createViewFromQML(self):
        path = QUrl.fromLocalFile(os.path.join(PluginRegistry.getInstance().getPluginPath("3MFReader"), self._qml_url))
        self._component = QQmlComponent(Application.getInstance()._engine, path)
        self._context = QQmlContext(Application.getInstance()._engine.rootContext())
        self._context.setContextProperty("manager", self)
        self._view = self._component.create(self._context)
        if self._view is None:
            Logger.log("c", "QQmlComponent status %s", self._component.status())
            Logger.log("c", "QQmlComponent error string %s", self._component.errorString())

    def show(self):
        # Emit signal so the right thread actually shows the view.
        if threading.current_thread() != threading.main_thread():
            self._lock.acquire()
        # Reset the result
        self._result = {"machine": self._default_strategy,
                        "quality_changes": self._default_strategy,
                        "material": self._default_strategy}
        self._visible = True
        self.showDialogSignal.emit()

    @pyqtSlot()
    ##  Used to notify the dialog so the lock can be released.
    def notifyClosed(self):
        if self._result is None:
            self._result = {}
        self._lock.release()

    def hide(self):
        self._visible = False
        self._lock.release()
        self._view.hide()

    @pyqtSlot()
    def onOkButtonClicked(self):
        self._view.hide()
        self.hide()

    @pyqtSlot()
    def onCancelButtonClicked(self):
        self._view.hide()
        self.hide()
        self._result = {}

    ##  Block thread until the dialog is closed.
    def waitForClose(self):
        if self._visible:
            if threading.current_thread() != threading.main_thread():
                self._lock.acquire()
                self._lock.release()
            else:
                # If this is not run from a separate thread, we need to ensure that the events are still processed.
                while self._visible:
                    time.sleep(1 / 50)
                    QCoreApplication.processEvents()  # Ensure that the GUI does not freeze.

    def __show(self):
        if self._view is None:
            self._createViewFromQML()
        if self._view:
            self._view.show()
