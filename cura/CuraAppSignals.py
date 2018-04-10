from PyQt5.QtCore import pyqtSignal, QObject


class CuraAppSignals(QObject):

    showMoreInfoOnAnonymousDataCollection = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)
