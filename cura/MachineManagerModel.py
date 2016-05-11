
from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal
from UM.Application import Application
from UM.Settings.ContainerRegistry import ContainerRegistry

class MachineManagerModel(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerChanged)

    globalContainerChanged = pyqtSignal()

    def _onGlobalContainerChanged(self):
        self.globalContainerChanged.emit()

    @pyqtSlot(str)
    def setActiveMachine(self, stack_id):
        containers = ContainerRegistry.getInstance().findContainerStacks(id = stack_id)
        if containers:
            Application.getInstance().setGlobalContainerStack(containers[0])

    @pyqtProperty(str, notify = globalContainerChanged)
    def activeMachineName(self):
        return Application.getInstance().getGlobalContainerStack().getName()

    @pyqtProperty(str, notify = globalContainerChanged)
    def activeMachineId(self):
        return Application.getInstance().getGlobalContainerStack().getId()



def createMachineManagerModel(engine, script_engine):
    return MachineManagerModel()