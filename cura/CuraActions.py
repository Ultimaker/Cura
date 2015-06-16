from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, pyqtProperty

import webbrowser

class CuraActions(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)

    @pyqtSlot()
    def openDocumentation(self):
        webbrowser.open("http://ultimaker.com/en/support/software")

    @pyqtSlot()
    def openBugReportPage(self):
        webbrowser.open("http://github.com/Ultimaker/Cura/issues")
