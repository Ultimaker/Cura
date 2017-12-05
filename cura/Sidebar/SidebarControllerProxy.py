# Copyright (c) 2017 Ultimaker B.V.
from PyQt5.QtCore import QObject, pyqtSlot, QUrl, pyqtProperty, pyqtSignal
from UM.Application import Application


##  The sidebar controller proxy acts a proxy between the sidebar controller and the QMl context of the controller.
from UM.Logger import Logger


class SidebarControllerProxy(QObject):

    def __init__(self, parent = None):
        super().__init__(parent)
        self._controller = Application.getInstance().getSidebarController()
        self._controller.activeSidebarViewChanged.connect(self._onActiveSidebarViewChanged)

    activeSidebarViewChanged = pyqtSignal()

    @classmethod
    def createSidebarControllerProxy(self, engine, script_engine):
        return SidebarControllerProxy()

    @pyqtProperty(str, notify = activeSidebarViewChanged)
    def activeSidebarId(self):
        return self._controller.getActiveSidebarViewId()

    @pyqtSlot(str)
    def setActiveSidebarView(self, sidebar_view_id):
        Logger.log("d", "Setting active sidebar view to %s", sidebar_view_id)
        self._controller.setActiveSidebarView(sidebar_view_id)

    @pyqtSlot(str, result = QObject)
    def getSidebarComponent(self, sidebar_id):
        return self._controller.getSidebarView(sidebar_id).getComponent()

    @pyqtSlot(str, result = QUrl)
    def getSidebarComponentPath(self, sidebar_id):
        return self._controller.getSidebarView(sidebar_id).getComponentPath()

    def _onActiveSidebarViewChanged(self):
        self.activeSidebarViewChanged.emit()
