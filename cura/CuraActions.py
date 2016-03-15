from PyQt5.QtCore import QObject, pyqtSlot, QUrl
from PyQt5.QtGui import QDesktopServices

from UM.Event import CallFunctionEvent
from UM.Application import Application

class CuraActions(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)

    @pyqtSlot()
    def openDocumentation(self):
        # Starting a web browser from a signal handler connected to a menu will crash on windows.
        # So instead, defer the call to the next run of the event loop, since that does work.
        # Note that weirdly enough, only signal handlers that open a web browser fail like that.
        event = CallFunctionEvent(self._openUrl, [QUrl("http://ultimaker.com/en/support/software")], {})
        Application.getInstance().functionEvent(event)

    @pyqtSlot()
    def openBugReportPage(self):
        event = CallFunctionEvent(self._openUrl, [QUrl("http://github.com/Ultimaker/Cura/issues")], {})
        Application.getInstance().functionEvent(event)

    def _openUrl(self, url):
        QDesktopServices.openUrl(url)