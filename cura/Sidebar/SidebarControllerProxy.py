# Copyright (c) 2017 Ultimaker B.V.
from PyQt5.QtCore import QObject, pyqtSlot, QUrl, pyqtProperty, pyqtSignal
from UM.Application import Application


##  The sidebar controller proxy acts a proxy between the sidebar controller and the QMl context of the controller.
class SidebarControllerProxy(QObject):

    def __init__(self, parent = None):
        super().__init__(parent)
        self._controller = Application.getInstance().getSidebarController()
        self._controller.activeSidebarViewChanged.connect(self._onActiveSidebarComponentChanged)

    ##  Emitted when the active view changes.
    activeSidebarViewChanged = pyqtSignal()

    @classmethod
    def createSidebarControllerProxy(self, engine, script_engine):
        return SidebarControllerProxy()

    @pyqtSlot()
    def setActiveView(self, sidebar_view):
        self._controller.setActiveSidebarView(sidebar_view)

    @pyqtProperty(QUrl, notify = activeSidebarViewChanged)
    def activeComponentPath(self):
        if not self._controller.getActiveSidebarView():
            return QUrl()
        return self._controller.getActiveSidebarView().getComponentPath()

    @pyqtSlot(QUrl)
    def getSidebarComponentPath(self, sidebar_id):
        self._controller.getSidebarView(sidebar_id).getComponentPath()

    def _onActiveSidebarComponentChanged(self):
        self.activeSidebarViewChanged.emit()
