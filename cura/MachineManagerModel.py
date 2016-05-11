
from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal
from UM.Application import Application
from UM.Signal import Signal, signalemitter

class MachineManagerModel(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerChanged)

    globalContainerChanged = pyqtSignal()

    def _onGlobalContainerChanged(self):
        self.globalContainerChanged.emit()

    @pyqtSlot(str)
    def setActiveMachine(self, stack_id):
        pass

    @pyqtProperty(str, notify = globalContainerChanged)
    def activeMachineId(self):
        return Application.getInstance().getGlobalContainerStack().getId()

def createMachineManagerModel(engine, script_engine):
    return MachineManagerModel()