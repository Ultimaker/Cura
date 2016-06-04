
import re

from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal
from UM.Application import Application
from UM.Preferences import Preferences
from UM.Logger import Logger

import UM.Settings
from UM.Settings.Validator import ValidatorState
from UM.Settings.InstanceContainer import InstanceContainer


class MachineManagerModel(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)

        self._global_container_stack = None
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerChanged)
        self._global_stack_valid = None
        self._onGlobalContainerChanged()

        ##  When the global container is changed, active material probably needs to be updated.
        self.globalContainerChanged.connect(self.activeMaterialChanged)
        self.globalContainerChanged.connect(self.activeVariantChanged)
        self.globalContainerChanged.connect(self.activeQualityChanged)

        self._empty_variant_container = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = "empty_variant")[0]
        self._empty_material_container = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = "empty_material")[0]
        self._empty_quality_container = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = "empty_quality")[0]

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

    globalValueChanged = pyqtSignal()  # Emitted whenever a value inside global container is changed.
    globalValidationChanged = pyqtSignal()  # Emitted whenever a validation inside global container is changed.

    def _onGlobalPropertyChanged(self, key, property_name):
        if property_name == "value":
            self.globalValueChanged.emit()
        if property_name == "validationState":
            if self._global_stack_valid:
                changed_validation_state = self._global_container_stack.getProperty(key, property_name)
                if changed_validation_state in (ValidatorState.Exception, ValidatorState.MaximumError, ValidatorState.MinimumError):
                    self._global_stack_valid = False
                    self.globalValidationChanged.emit()
            else:
                new_validation_state = self._checkStackForErrors(self._global_container_stack)
                if new_validation_state:
                    self._global_stack_valid = True
                    self.globalValidationChanged.emit()

    def _onGlobalContainerChanged(self):
        if self._global_container_stack:
            self._global_container_stack.containersChanged.disconnect(self._onInstanceContainersChanged)
            self._global_container_stack.propertyChanged.disconnect(self._onGlobalPropertyChanged)

        self._global_container_stack = Application.getInstance().getGlobalContainerStack()
        self.globalContainerChanged.emit()

        if self._global_container_stack:
            Preferences.getInstance().setValue("cura/active_machine", self._global_container_stack.getId())
            self._global_container_stack.containersChanged.connect(self._onInstanceContainersChanged)
            self._global_container_stack.propertyChanged.connect(self._onGlobalPropertyChanged)
            self._global_stack_valid = not self._checkStackForErrors(self._global_container_stack)

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
            name = self._createUniqueStackName(name, definition.getName())

            new_global_stack = UM.Settings.ContainerStack(name)
            new_global_stack.addMetaDataEntry("type", "machine")
            UM.Settings.ContainerRegistry.getInstance().addContainer(new_global_stack)

            variant_instance_container = self._updateVariantContainer(definition)
            material_instance_container = self._updateMaterialContainer(definition)
            quality_instance_container = self._updateQualityContainer(definition)

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
    def _createUniqueStackName(self, name, fallback_name):
        name = name.strip()
        num_check = re.compile("(.*?)\s*#\d$").match(name)
        if(num_check):
            name = num_check.group(1)
        if name == "":
            name = fallback_name
        unique_name = name
        i = 1

        # Check both the id and the name, because they may not be the same and it is better if they are both unique
        while UM.Settings.ContainerRegistry.getInstance().findContainers(None, id = unique_name) or \
                UM.Settings.ContainerRegistry.getInstance().findContainers(None, name = unique_name):
            i += 1
            unique_name = "%s #%d" % (name, i)

        return unique_name

    ##  Convenience function to check if a stack has errors.
    def _checkStackForErrors(self, stack):
        if stack is None:
            return False

        for key in stack.getAllKeys():
            validation_state = stack.getProperty(key, "validationState")
            if validation_state in (ValidatorState.Exception, ValidatorState.MaximumError, ValidatorState.MinimumError):
                return True
        return False

    ##  Remove all instances from the top instanceContainer (effectively removing all user-changed settings)
    @pyqtSlot()
    def clearUserSettings(self):
        if not self._global_container_stack:
            return
        user_settings = self._global_container_stack.getTop()
        user_settings.clear()

    ##  Check if the global_container has instances in the user container
    @pyqtProperty(bool, notify = globalValueChanged)
    def hasUserSettings(self):
        if not self._global_container_stack:
            return

        user_settings = self._global_container_stack.getTop().findInstances(**{})
        return len(user_settings) != 0

    ##  Check if the global profile does not contain error states
    #   Note that the _global_stack_valid is cached due to performance issues
    #   Calling _checkStackForErrors on every change is simply too expensive
    @pyqtProperty(bool, notify = globalValidationChanged)
    def isGlobalStackValid(self):
        return self._global_stack_valid

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

    ## Check if a container is read_only
    @pyqtSlot(str, result = bool)
    def isReadOnly(self, container_id):
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id=container_id)
        if not containers or not self._global_container_stack:
            return True
        return containers[0].getMetaDataEntry("read_only", False) == "True"

    @pyqtSlot(result = str)
    def convertUserContainerToQuality(self):
        if not self._global_container_stack:
            return

        name = self._createUniqueStackName("Custom profile", "")
        user_settings = self._global_container_stack.getTop()
        new_quality_container = InstanceContainer("")

        ## Copy all values
        new_quality_container.deserialize(user_settings.serialize())

        ## Change type / id / name
        new_quality_container.setMetaDataEntry("type","quality")
        new_quality_container.setName(name)
        new_quality_container._id = name

        UM.Settings.ContainerRegistry.getInstance().addContainer(new_quality_container)
        self.clearUserSettings()  # As all users settings are noq a quality, remove them.
        self.setActiveQuality(name)
        return name

    @pyqtSlot(str, result=str)
    def duplicateContainer(self, container_id):
        if not self._global_container_stack:
            return
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id=container_id)
        if containers:
            new_name = self._createUniqueStackName(containers[0].getName(), "")

            new_container = InstanceContainer("")

            ## Copy all values
            new_container.deserialize(containers[0].serialize())

            new_container.setName(new_name)
            new_container._id = new_name
            UM.Settings.ContainerRegistry.getInstance().addContainer(new_container)
            return new_name

        return ""

    @pyqtSlot()
    def updateUserContainerToQuality(self):
        if not self._global_container_stack:
            return
        user_settings = self._global_container_stack.getTop()
        quality = self._global_container_stack.findContainer({"type": "quality"})
        for key in user_settings.getAllKeys():
            quality.setProperty(key, "value", user_settings.getProperty(key, "value"))
        self.clearUserSettings()  # As all users settings are noq a quality, remove them.


    @pyqtSlot(str)
    def setActiveMaterial(self, material_id):
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id=material_id)
        if not containers or not self._global_container_stack:
            return

        old_material = self._global_container_stack.findContainer({"type":"material"})
        if old_material:
            material_index = self._global_container_stack.getContainerIndex(old_material)
            self._global_container_stack.replaceContainer(material_index, containers[0])

            self.setActiveQuality(self._updateQualityContainer(self._global_container_stack.getBottom(), containers[0]).id)

    @pyqtSlot(str)
    def setActiveVariant(self, variant_id):
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id=variant_id)
        if not containers or not self._global_container_stack:
            return

        old_variant = self._global_container_stack.findContainer({"type": "variant"})
        if old_variant:
            variant_index = self._global_container_stack.getContainerIndex(old_variant)
            self._global_container_stack.replaceContainer(variant_index, containers[0])

            self.setActiveMaterial(self._updateMaterialContainer(self._global_container_stack.getBottom(), containers[0]).id)

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
            new_name = self._createUniqueStackName(new_name, containers[0].getBottom().getName())
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

    def _updateVariantContainer(self, definition):
        if not definition.getMetaDataEntry("has_variants"):
            return self._empty_variant_container

        containers = []
        preferred_variant = definition.getMetaDataEntry("preferred_variant")
        if preferred_variant:
            containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(type = "variant", definition = definition.id, id = preferred_variant)

        if not containers:
            containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(type = "variant", definition = definition.id)

        if containers:
            return containers[0]

        return self._empty_variant_container

    def _updateMaterialContainer(self, definition, variant_container):
        if not definition.getMetaDataEntry("has_materials"):
            return self._empty_material_container

        search_criteria = { "type": "material" }

        if definition.getMetaDataEntry("has_machine_materials"):
            search_criteria["definition"] = definition.id

            if definition.getMetaDataEntry("has_variants") and variant_container:
                search_criteria["variant"] = variant_container.id
        else:
            search_criteria["definition"] = "fdmprinter"

        preferred_material = definition.getMetaDataEntry("preferred_material")
        if preferred_material:
            search_criteria["id"] = preferred_material

        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(**search_criteria)
        if containers:
            return containers[0]

        return self._empty_material_container

    def _updateQualityContainer(self, definition, material_container):
        search_criteria = { "type": "quality" }

        if definition.getMetaDataEntry("has_machine_quality"):
            search_criteria["definition"] = definition.id

            if definition.getMetaDataEntry("has_materials") and material_container:
                search_criteria["material"] = material_container.id
        else:
            search_criteria["definition"] = "fdmprinter"

        preferred_quality = definition.getMetaDataEntry("preferred_quality")
        if preferred_quality:
            search_criteria["id"] = preferred_quality

        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(**search_criteria)
        if containers:
            return containers[0]

        return self._empty_quality_container

def createMachineManagerModel(engine, script_engine):
    return MachineManagerModel()
