from UM.Application import Application
from UM.Qt.ListModel import ListModel

from PyQt5.QtCore import pyqtProperty, Qt, pyqtSignal, pyqtSlot, QUrl

from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.InstanceContainer import InstanceContainer

class ContainerSettingsModel(ListModel):
    LabelRole = Qt.UserRole + 1
    CategoryRole = Qt.UserRole + 2
    UnitRole = Qt.UserRole + 3
    ValuesRole = Qt.UserRole + 4

    def __init__(self, parent = None):
        super().__init__(parent)
        self.addRoleName(self.LabelRole, "label")
        self.addRoleName(self.CategoryRole, "category")
        self.addRoleName(self.UnitRole, "unit")
        self.addRoleName(self.ValuesRole, "values")

        self._container_ids = []
        self._container = None

        self._global_container_stack = None
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerChanged)
        self._update()

    def _onGlobalContainerChanged(self):
        if self._global_container_stack:
            self._global_container_stack.containersChanged.disconnect(self._onInstanceContainersChanged)
            self._global_container_stack.propertyChanged.disconnect(self._onGlobalPropertyChanged)

        self._global_container_stack = Application.getInstance().getGlobalContainerStack()

        if self._global_container_stack:
            Preferences.getInstance().setValue("cura/active_machine", self._global_container_stack.getId())
            self._global_container_stack.containersChanged.connect(self._onInstanceContainersChanged)
            self._global_container_stack.propertyChanged.connect(self._onGlobalPropertyChanged)

        self._update()

    def _onGlobalPropertyChanged(self, key, property_name):
        if property_name == "value":
            self._update()

    def _onInstanceContainersChanged(self, container):
        self._update()

    def _update(self):
        self.clear()

        if len(self._container_ids) == 0:
            return

        keys = []
        containers = []
        for container_id in self._container_ids:
            container = ContainerRegistry.getInstance().findContainers(id = container_id)
            if not container:
                return

            keys = keys + list(container[0].getAllKeys())
            containers.append(container[0])

        keys = list(set(keys))
        keys.sort()

        for key in keys:
            definition = None
            category = None
            values = []
            for container in containers:

                instance = container.getInstance(key)
                if instance:
                    definition = instance.definition

                    # Traverse up to find the category
                    category = definition
                    while category.type != "category":
                        category = category.parent

                    values.append(container.getProperty(key, "value"))
                else:
                    values.append("")

            self.appendItem({
                "key": key,
                "values": values,
                "label": definition.label,
                "unit": definition.unit,
                "category": category.label
            })

    ##  Set the id of the container which has the settings this model should list.
    def setContainers(self, container_ids):
        self._container_ids = container_ids
        self._update()

    containersChanged = pyqtSignal()
    @pyqtProperty("QVariantList", fset = setContainers, notify = containersChanged)
    def containers(self):
        return self.container_ids