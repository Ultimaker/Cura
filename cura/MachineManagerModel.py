
import re

from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal
from UM.Application import Application
from UM.Preferences import Preferences
from UM.Logger import Logger

import UM.Settings


class MachineManagerModel(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)

        self._global_container_stack = None
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerChanged)
        self._onGlobalContainerChanged()

        ##  When the global container is changed, active material probably needs to be updated.
        self.globalContainerChanged.connect(self.activeMaterialChanged)
        self.globalContainerChanged.connect(self.activeVariantChanged)
        self.globalContainerChanged.connect(self.activeQualityChanged)

        Preferences.getInstance().addPreference("cura/active_machine", "")

        active_machine_id = Preferences.getInstance().getValue("cura/active_machine")

        if active_machine_id != "":
            # An active machine was saved, so restore it.
            self.setActiveMachine(active_machine_id)
            pass


    globalContainerChanged = pyqtSignal()
    activeMaterialChanged = pyqtSignal()
    activeVariantChanged = pyqtSignal()
    activeQualityChanged = pyqtSignal()

    def _onGlobalContainerChanged(self):
        if self._global_container_stack:
            self._global_container_stack.containersChanged.disconnect(self._onInstanceContainersChanged)

        self._global_container_stack = Application.getInstance().getGlobalContainerStack()
        self.globalContainerChanged.emit()

        if self._global_container_stack:
            Preferences.getInstance().setValue("cura/active_machine", self._global_container_stack.getId())
            self._global_container_stack.containersChanged.connect(self._onInstanceContainersChanged)

    def _onInstanceContainersChanged(self, container):
        container_type = container.getMetaDataEntry("type")
        if container_type == "material":
            self.activeMaterialChanged.emit()
        elif container_type == "variant":
            self.activeVariantChanged.emit()
        elif container_type == "quality":
            self.activeQualityChanged.emit()

    @pyqtSlot(str)
    def setActiveMachine(self, stack_id):
        containers = UM.Settings.ContainerRegistry.getInstance().findContainerStacks(id = stack_id)
        if containers:
            Application.getInstance().setGlobalContainerStack(containers[0])

    @pyqtSlot(str, str)
    def addMachine(self,name, definition_id):
        definitions = UM.Settings.ContainerRegistry.getInstance().findDefinitionContainers(id=definition_id)
        if definitions:
            definition = definitions[0]
            name = self._uniqueMachineName(name, definition.getName())

            new_global_stack = UM.Settings.ContainerStack(name)
            new_global_stack.addMetaDataEntry("type", "machine")
            UM.Settings.ContainerRegistry.getInstance().addContainer(new_global_stack)

            empty_container = UM.Settings.ContainerRegistry.getInstance().getEmptyInstanceContainer()

            variant_instance_container = empty_container
            if definition.getMetaDataEntry("has_variants"):
                variant_instance_container = self._getPreferredContainer(definition, "preferred_variant", empty_container)

                if variant_instance_container == empty_container:
                    variants = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(type = "variant", definition = definition.id)
                    if variants:
                        variant_instance_container = variants[0]

                if variant_instance_container == empty_container:
                    Logger.log("w", "Machine %s defines it has variants but no variants found", definition.id)

            material_instance_container = empty_container
            if definition.getMetaDataEntry("has_materials"):
                material_instance_container = self._getPreferredContainer(definition, "preferred_material", empty_container)

                if material_instance_container == empty_container:
                    materials = None
                    if definition.getMetaDataEntry("has_machine_materials"):
                        if variant_instance_container != empty_container:
                            materials = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(type = "material", definition = definition.id, variant = variant_instance_container.id)
                        else:
                            materials = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(type = "material", definition = definition.id)
                    else:
                        materials = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(type = "material", definition = "fdmprinter")

                    if materials:
                        material_instance_container = materials[0]

            quality_instance_container = self._getPreferredContainer(definition, "preferred_quality", empty_container)

            if quality_instance_container == empty_container:
                if definition.getMetaDataEntry("has_machine_quality"):
                    if material_instance_container:
                        qualities = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(type = "quality", definition = definition.id, material = material_instance_container.id)
                    else:
                        qualities = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(type = "quality", definition = definition.id)
                else:
                    qualities = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(type = "quality", definition = "fdmprinter")

                if qualities:
                    quality_instance_container = qualities[0]

            current_settings_instance_container = UM.Settings.InstanceContainer(name + "_current_settings")
            current_settings_instance_container.addMetaDataEntry("machine", name)
            current_settings_instance_container.addMetaDataEntry("type", "user")
            current_settings_instance_container.setDefinition(definitions[0])
            UM.Settings.ContainerRegistry.getInstance().addContainer(current_settings_instance_container)

            # If a definition is found, its a list. Should only have one item.
            new_global_stack.addContainer(definitions[0])
            if variant_instance_container:
                new_global_stack.addContainer(variant_instance_container)
            if material_instance_container:
                new_global_stack.addContainer(material_instance_container)
            if quality_instance_container:
                new_global_stack.addContainer(quality_instance_container)
            new_global_stack.addContainer(current_settings_instance_container)

            Application.getInstance().setGlobalContainerStack(new_global_stack)

    # Create a name that is not empty and unique
    def _uniqueMachineName(self, name, fallback_name):
        name = name.strip()
        num_check = re.compile("(.*?)\s*#\d$").match(name)
        if(num_check):
            name = num_check.group(1)
        if name == "":
            name = fallback_name
        unique_name = name
        i = 1

        #Check both the id and the name, because they may not be the same and it is better if they are both unique
        while UM.Settings.ContainerRegistry.getInstance().findContainers(None, id = unique_name) or \
                UM.Settings.ContainerRegistry.getInstance().findContainers(None, name = unique_name):
            i = i + 1
            unique_name = "%s #%d" % (name, i)

        return unique_name

    @pyqtProperty(str, notify = globalContainerChanged)
    def activeMachineName(self):
        if self._global_container_stack:
            return self._global_container_stack.getName()

        return ""

    @pyqtProperty(str, notify = globalContainerChanged)
    def activeMachineId(self):
        if self._global_container_stack:
            return self._global_container_stack.getId()

        return ""

    @pyqtProperty(str, notify = activeMaterialChanged)
    def activeMaterialName(self):
        if self._global_container_stack:
            material = self._global_container_stack.findContainer({"type":"material"})
            if material:
                return material.getName()

        return ""

    @pyqtProperty(str, notify=activeMaterialChanged)
    def activeMaterialId(self):
        if self._global_container_stack:
            material = self._global_container_stack.findContainer({"type": "material"})
            if material:
                return material.getId()

        return ""

    @pyqtProperty(str, notify=activeQualityChanged)
    def activeQualityName(self):
        if self._global_container_stack:
            quality = self._global_container_stack.findContainer({"type": "quality"})
            if quality:
                return quality.getName()
        return ""

    @pyqtProperty(str, notify=activeQualityChanged)
    def activeQualityId(self):
        if self._global_container_stack:
            quality = self._global_container_stack.findContainer({"type": "quality"})
            if quality:
                return quality.getId()
        return ""

    @pyqtSlot(str)
    def setActiveMaterial(self, material_id):
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id=material_id)
        if not containers or not self._global_container_stack:
            return

        old_material = self._global_container_stack.findContainer({"type":"material"})
        if old_material:
            material_index = self._global_container_stack.getContainerIndex(old_material)
            self._global_container_stack.replaceContainer(material_index, containers[0])

    @pyqtSlot(str)
    def setActiveVariant(self, variant_id):
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id=variant_id)
        if not containers or not self._global_container_stack:
            return

        old_variant = self._global_container_stack.findContainer({"type": "variant"})
        if old_variant:
            variant_index = self._global_container_stack.getContainerIndex(old_variant)
            self._global_container_stack.replaceContainer(variant_index, containers[0])

    @pyqtSlot(str)
    def setActiveQuality(self, quality_id):
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = quality_id)
        if not containers or not self._global_container_stack:
            return

        old_quality = self._global_container_stack.findContainer({"type": "quality"})
        if old_quality:
            quality_index = self._global_container_stack.getContainerIndex(old_quality)
            self._global_container_stack.replaceContainer(quality_index, containers[0])

    @pyqtProperty(str, notify = activeVariantChanged)
    def activeVariantName(self):
        if self._global_container_stack:
            variant = self._global_container_stack.findContainer({"type": "variant"})
            if variant:
                return variant.getName()

        return ""

    @pyqtProperty(str, notify = activeVariantChanged)
    def activeVariantId(self):
        if self._global_container_stack:
            variant = self._global_container_stack.findContainer({"type": "variant"})
            if variant:
                return variant.getId()

        return ""

    @pyqtProperty(str, notify = globalContainerChanged)
    def activeDefinitionId(self):
        if self._global_container_stack:
            definition = self._global_container_stack.getBottom()
            if definition:
                return definition.id

        return ""

    @pyqtSlot(str, str)
    def renameMachine(self, machine_id, new_name):
        containers = UM.Settings.ContainerRegistry.getInstance().findContainerStacks(id = machine_id)
        if containers:
            new_name = self._uniqueMachineName(new_name, containers[0].getBottom().getName())
            containers[0].setName(new_name)
            self.globalContainerChanged.emit()

    @pyqtSlot(str)
    def removeMachine(self, machine_id):
        # If the machine that is being removed is the currently active machine, set another machine as the active machine
        if self._global_container_stack and self._global_container_stack.getId() == machine_id:
            containers = UM.Settings.ContainerRegistry.getInstance().findContainerStacks()
            if containers:
                Application.getInstance().setGlobalContainerStack(containers[0])
        UM.Settings.ContainerRegistry.getInstance().removeContainer(machine_id)

    @pyqtProperty(bool, notify = globalContainerChanged)
    def hasMaterials(self):
        if self._global_container_stack:
            return bool(self._global_container_stack.getMetaDataEntry("has_materials", False))

        return False

    @pyqtProperty(bool, notify = globalContainerChanged)
    def hasVariants(self):
        if self._global_container_stack:
            return bool(self._global_container_stack.getMetaDataEntry("has_variants", False))

        return False

    @pyqtProperty(bool, notify = globalContainerChanged)
    def filterMaterialsByMachine(self):
        if self._global_container_stack:
            return bool(self._global_container_stack.getMetaDataEntry("has_machine_materials", False))

        return False

    @pyqtProperty(bool, notify = globalContainerChanged)
    def filterQualityByMachine(self):
        if self._global_container_stack:
            return bool(self._global_container_stack.getMetaDataEntry("has_machine_quality", False))

        return False

    def _getPreferredContainer(self, definition, property_name, default_container):
        preferred_id = definition.getMetaDataEntry(property_name)
        if preferred_id:
            preferred_id = preferred_id.lower()
            container = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = preferred_id)
            if container:
                return container[0]

        return default_container

def createMachineManagerModel(engine, script_engine):
    return MachineManagerModel()
