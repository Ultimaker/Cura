from PyQt5.QtCore import Qt, QUrl, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtQml import QQmlComponent, QQmlContext
from UM.PluginRegistry import PluginRegistry
from UM.Application import Application

import os
import threading

class WorkspaceDialog(QObject):
    showDialogSignal = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)
        self._component = None
        self._context = None
        self._view = None
        self._qml_url = "WorkspaceDialog.qml"
        self._lock = threading.Lock()
        self._result = None  # What option did the user pick?
        self._visible = False
        self.showDialogSignal.connect(self.__show)

    def getResult(self):
        return self._result

    def _createViewFromQML(self):
        path = QUrl.fromLocalFile(os.path.join(PluginRegistry.getInstance().getPluginPath("3MFReader"), self._qml_url))
        self._component = QQmlComponent(Application.getInstance()._engine, path)
        self._context = QQmlContext(Application.getInstance()._engine.rootContext())
        self._context.setContextProperty("manager", self)
        self._view = self._component.create(self._context)

    def show(self):
        # Emit signal so the right thread actually shows the view.
        self._lock.acquire()
        self._result = None
        self._visible = True
        self.showDialogSignal.emit()

    @pyqtSlot()
    ##  Used to notify the dialog so the lock can be released.
    def notifyClosed(self):
        if self._result is None:
            self._result = "cancel"
        self._lock.release()

    def hide(self):
        self._visible = False
        self._lock.release()
        self._view.hide()

    @pyqtSlot()
    def onOverrideButtonClicked(self):
        self._view.hide()
        self.hide()
        self._result = "override"

    @pyqtSlot()
    def onNewButtonClicked(self):
        self._view.hide()
        self.hide()
        self._result = "new"

    @pyqtSlot()
    def onCancelButtonClicked(self):
        self._view.hide()
        self.hide()
        self._result = "cancel"

    ##  Block thread until the dialog is closed.
    def waitForClose(self):
        if self._visible:
            self._lock.acquire()
            self._lock.release()

    def __show(self):
        if self._view is None:
            self._createViewFromQML()
        self._view.show()
