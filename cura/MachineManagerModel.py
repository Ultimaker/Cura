
from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal
from UM.Application import Application
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.InstanceContainer import InstanceContainer

class MachineManagerModel(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerChanged)

        ##  When the global container is changed, active material probably needs to be updated.
        self.globalContainerChanged.connect(self.activeMaterialChanged)

    globalContainerChanged = pyqtSignal()
    activeMaterialChanged = pyqtSignal()

    def _onGlobalContainerChanged(self):
        self.globalContainerChanged.emit()

    @pyqtSlot(str)
    def setActiveMachine(self, stack_id):
        containers = ContainerRegistry.getInstance().findContainerStacks(id = stack_id)
        if containers:
            Application.getInstance().setGlobalContainerStack(containers[0])

    @pyqtSlot(str, str)
    def addMachine(self,name, definition_id):
        definitions = ContainerRegistry.getInstance().findDefinitionContainers(id=definition_id)
        if definitions:
            new_global_stack = ContainerStack(name)
            new_global_stack.addMetaDataEntry("type", "machine")
            ContainerRegistry.getInstance().addContainer(new_global_stack)

            variant_instance_container = InstanceContainer(name + "_variant")
            material_instance_container = InstanceContainer("test_material")
            material_instance_container.addMetaDataEntry("type", "material")
            material_instance_container.setDefinition(definitions[0])
            #material_instance_container.setMetaData({"type","material"})
            quality_instance_container = InstanceContainer(name + "_quality")
            current_settings_instance_container = InstanceContainer(name + "_current_settings")
            ContainerRegistry.getInstance().addContainer(material_instance_container)

            # If a definition is found, its a list. Should only have one item.
            new_global_stack.addContainer(definitions[0])
            new_global_stack.addContainer(material_instance_container)
            Application.getInstance().setGlobalContainerStack(new_global_stack)

    @pyqtProperty(str, notify = globalContainerChanged)
    def activeMachineName(self):
        return Application.getInstance().getGlobalContainerStack().getName()

    @pyqtProperty(str, notify = globalContainerChanged)
    def activeMachineId(self):
        return Application.getInstance().getGlobalContainerStack().getId()

    @pyqtProperty(str, notify = activeMaterialChanged)
    def activeMaterialName(self):
        material = Application.getInstance().getGlobalContainerStack().findContainer({"type":"material"})
        if material:
            return material.getName()

    @pyqtSlot(str, str)
    def renameMachine(self, machine_id, new_name):
        containers = ContainerRegistry.getInstance().findContainerStacks(id = machine_id)
        if containers:
            containers[0].setName(new_name)

    @pyqtSlot(str)
    def removeMachine(self, machine_id):
        ContainerRegistry.getInstance().removeContainer(machine_id)



def createMachineManagerModel(engine, script_engine):
    return MachineManagerModel()