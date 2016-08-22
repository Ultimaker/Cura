# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal
from PyQt5.QtWidgets import QMessageBox

from UM.Application import Application
from UM.Preferences import Preferences
from UM.Logger import Logger

import UM.Settings

from cura.PrinterOutputDevice import PrinterOutputDevice
from . import ExtruderManager

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

import time

class MachineManager(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)

        self._active_container_stack = None
        self._global_container_stack = None

        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerChanged)
        ##  When the global container is changed, active material probably needs to be updated.
        self.globalContainerChanged.connect(self.activeMaterialChanged)
        self.globalContainerChanged.connect(self.activeVariantChanged)
        self.globalContainerChanged.connect(self.activeQualityChanged)

        self._active_stack_valid = None
        self._onGlobalContainerChanged()

        ExtruderManager.getInstance().activeExtruderChanged.connect(self._onActiveExtruderStackChanged)
        self._onActiveExtruderStackChanged()

        ExtruderManager.getInstance().activeExtruderChanged.connect(self.activeMaterialChanged)
        ExtruderManager.getInstance().activeExtruderChanged.connect(self.activeVariantChanged)
        ExtruderManager.getInstance().activeExtruderChanged.connect(self.activeQualityChanged)

        self.globalContainerChanged.connect(self.activeStackChanged)
        self.globalValueChanged.connect(self.activeStackChanged)
        ExtruderManager.getInstance().activeExtruderChanged.connect(self.activeStackChanged)

        self._empty_variant_container = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = "empty_variant")[0]
        self._empty_material_container = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = "empty_material")[0]
        self._empty_quality_container = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = "empty_quality")[0]
        self._empty_quality_changes_container = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = "empty_quality_changes")[0]

        Preferences.getInstance().addPreference("cura/active_machine", "")

        self._global_event_keys = set()

        active_machine_id = Preferences.getInstance().getValue("cura/active_machine")

        self._printer_output_devices = []
        Application.getInstance().getOutputDeviceManager().outputDevicesChanged.connect(self._onOutputDevicesChanged)

        if active_machine_id != "":
            # An active machine was saved, so restore it.
            self.setActiveMachine(active_machine_id)
            if self._global_container_stack and self._global_container_stack.getProperty("machine_extruder_count", "value") > 1:
                # Make sure _active_container_stack is properly initiated
                ExtruderManager.getInstance().setActiveExtruderIndex(0)

        self._auto_materials_changed = {}
        self._auto_hotends_changed = {}

    globalContainerChanged = pyqtSignal()
    activeMaterialChanged = pyqtSignal()
    activeVariantChanged = pyqtSignal()
    activeQualityChanged = pyqtSignal()
    activeStackChanged = pyqtSignal()

    globalValueChanged = pyqtSignal()  # Emitted whenever a value inside global container is changed.
    activeValidationChanged = pyqtSignal()  # Emitted whenever a validation inside active container is changed

    blurSettings = pyqtSignal() # Emitted to force fields in the advanced sidebar to un-focus, so they update properly

    outputDevicesChanged = pyqtSignal()

    def _onOutputDevicesChanged(self):
        for printer_output_device in self._printer_output_devices:
            printer_output_device.hotendIdChanged.disconnect(self._onHotendIdChanged)
            printer_output_device.materialIdChanged.disconnect(self._onMaterialIdChanged)

        self._printer_output_devices.clear()

        for printer_output_device in Application.getInstance().getOutputDeviceManager().getOutputDevices():
            if isinstance(printer_output_device, PrinterOutputDevice):
                self._printer_output_devices.append(printer_output_device)
                printer_output_device.hotendIdChanged.connect(self._onHotendIdChanged)
                printer_output_device.materialIdChanged.connect(self._onMaterialIdChanged)

        self.outputDevicesChanged.emit()

    @pyqtProperty("QVariantList", notify = outputDevicesChanged)
    def printerOutputDevices(self):
        return self._printer_output_devices

    def _onHotendIdChanged(self, index, hotend_id):
        if not self._global_container_stack:
            return

        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(type="variant", definition=self._global_container_stack.getBottom().getId(), name=hotend_id)
        if containers:  # New material ID is known
            extruder_manager = ExtruderManager.getInstance()
            extruders = list(extruder_manager.getMachineExtruders(self.activeMachineId))
            matching_extruder = None
            for extruder in extruders:
                if str(index) == extruder.getMetaDataEntry("position"):
                    matching_extruder = extruder
                    break
            if matching_extruder and matching_extruder.findContainer({"type": "variant"}).getName() != hotend_id:
                # Save the material that needs to be changed. Multiple changes will be handled by the callback.
                self._auto_hotends_changed[str(index)] = containers[0].getId()
                self._printer_output_devices[0].materialHotendChangedMessage(self._materialHotendChangedCallback)
        else:
            Logger.log("w", "No variant found for printer definition %s with id %s" % (self._global_container_stack.getBottom().getId(), hotend_id))

    def _autoUpdateHotends(self):
        extruder_manager = ExtruderManager.getInstance()
        for position in self._auto_hotends_changed:
            hotend_id = self._auto_hotends_changed[position]
            old_index = extruder_manager.activeExtruderIndex

            if old_index != int(position):
                extruder_manager.setActiveExtruderIndex(int(position))
            else:
                old_index = None
            Logger.log("d", "Setting hotend variant of hotend %s to %s" % (position, hotend_id))
            self.setActiveVariant(hotend_id)

            if old_index is not None:
                extruder_manager.setActiveExtruderIndex(old_index)

    def _onMaterialIdChanged(self, index, material_id):
        if not self._global_container_stack:
            return

        definition_id = "fdmprinter"
        if self._global_container_stack.getMetaDataEntry("has_machine_materials", False):
            definition_id = self._global_container_stack.getBottom().getId()
        extruder_manager = ExtruderManager.getInstance()
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(type = "material", definition = definition_id, GUID = material_id)
        if containers:  # New material ID is known
            extruders = list(extruder_manager.getMachineExtruders(self.activeMachineId))
            matching_extruder = None
            for extruder in extruders:
                if str(index) == extruder.getMetaDataEntry("position"):
                    matching_extruder = extruder
                    break

            if matching_extruder and matching_extruder.findContainer({"type":"material"}).getMetaDataEntry("GUID") != material_id:
                # Save the material that needs to be changed. Multiple changes will be handled by the callback.
                self._auto_materials_changed[str(index)] = containers[0].getId()
                self._printer_output_devices[0].materialHotendChangedMessage(self._materialHotendChangedCallback)
        else:
            Logger.log("w", "No material definition found for printer definition %s and GUID %s" % (definition_id, material_id))

    def _materialHotendChangedCallback(self, button):
        if button == QMessageBox.No:
            self._auto_materials_changed = {}
            self._auto_hotends_changed = {}
            return
        self._autoUpdateMaterials()
        self._autoUpdateHotends()

    def _autoUpdateMaterials(self):
        extruder_manager = ExtruderManager.getInstance()
        for position in self._auto_materials_changed:
            material_id = self._auto_materials_changed[position]
            old_index = extruder_manager.activeExtruderIndex

            if old_index != int(position):
                extruder_manager.setActiveExtruderIndex(int(position))
            else:
                old_index = None

            Logger.log("d", "Setting material of hotend %s to %s" % (position, material_id))
            self.setActiveMaterial(material_id)

            if old_index is not None:
                extruder_manager.setActiveExtruderIndex(old_index)

    def _onGlobalContainerChanged(self):
        if self._global_container_stack:
            self._global_container_stack.nameChanged.disconnect(self._onMachineNameChanged)
            self._global_container_stack.containersChanged.disconnect(self._onInstanceContainersChanged)
            self._global_container_stack.propertyChanged.disconnect(self._onPropertyChanged)

            material = self._global_container_stack.findContainer({"type": "material"})
            material.nameChanged.disconnect(self._onMaterialNameChanged)

            quality = self._global_container_stack.findContainer({"type": "quality"})
            quality.nameChanged.disconnect(self._onQualityNameChanged)

        self._global_container_stack = Application.getInstance().getGlobalContainerStack()
        self._active_container_stack = self._global_container_stack

        self.globalContainerChanged.emit()

        if self._global_container_stack:
            Preferences.getInstance().setValue("cura/active_machine", self._global_container_stack.getId())
            self._global_container_stack.nameChanged.connect(self._onMachineNameChanged)
            self._global_container_stack.containersChanged.connect(self._onInstanceContainersChanged)
            self._global_container_stack.propertyChanged.connect(self._onPropertyChanged)
            material = self._global_container_stack.findContainer({"type": "material"})
            material.nameChanged.connect(self._onMaterialNameChanged)

            quality = self._global_container_stack.findContainer({"type": "quality"})
            quality.nameChanged.connect(self._onQualityNameChanged)

    def _onActiveExtruderStackChanged(self):
        self.blurSettings.emit()  # Ensure no-one has focus.
        if self._active_container_stack and self._active_container_stack != self._global_container_stack:
            self._active_container_stack.containersChanged.disconnect(self._onInstanceContainersChanged)
            self._active_container_stack.propertyChanged.disconnect(self._onPropertyChanged)
        self._active_container_stack = ExtruderManager.getInstance().getActiveExtruderStack()
        if self._active_container_stack:
            self._active_container_stack.containersChanged.connect(self._onInstanceContainersChanged)
            self._active_container_stack.propertyChanged.connect(self._onPropertyChanged)
        else:
            self._active_container_stack = self._global_container_stack
        self._active_stack_valid = not self._checkStackForErrors(self._active_container_stack)
        self.activeValidationChanged.emit()

    def _onInstanceContainersChanged(self, container):
        container_type = container.getMetaDataEntry("type")

        if container_type == "material":
            self.activeMaterialChanged.emit()
        elif container_type == "variant":
            self.activeVariantChanged.emit()
        elif container_type == "quality":
            self.activeQualityChanged.emit()

    def _onPropertyChanged(self, key, property_name):
        if property_name == "validationState":
            if self._active_stack_valid:
                if self._active_container_stack.getProperty(key, "settable_per_extruder"):
                    changed_validation_state = self._active_container_stack.getProperty(key, property_name)
                else:
                    changed_validation_state = self._global_container_stack.getProperty(key, property_name)
                if changed_validation_state in (UM.Settings.ValidatorState.Exception, UM.Settings.ValidatorState.MaximumError, UM.Settings.ValidatorState.MinimumError):
                    self._active_stack_valid = False
                    self.activeValidationChanged.emit()
            else:
                if not self._checkStackForErrors(self._active_container_stack) and not self._checkStackForErrors(self._global_container_stack):
                    self._active_stack_valid = True
                    self.activeValidationChanged.emit()

        self.activeStackChanged.emit()

    @pyqtSlot(str)
    def setActiveMachine(self, stack_id):
        containers = UM.Settings.ContainerRegistry.getInstance().findContainerStacks(id = stack_id)
        if containers:
            Application.getInstance().setGlobalContainerStack(containers[0])

    @pyqtSlot(str, str)
    def addMachine(self, name, definition_id):
        container_registry = UM.Settings.ContainerRegistry.getInstance()
        definitions = container_registry.findDefinitionContainers(id = definition_id)
        if definitions:
            definition = definitions[0]
            name = self._createUniqueName("machine", "", name, definition.getName())
            new_global_stack = UM.Settings.ContainerStack(name)
            new_global_stack.addMetaDataEntry("type", "machine")
            container_registry.addContainer(new_global_stack)

            variant_instance_container = self._updateVariantContainer(definition)
            material_instance_container = self._updateMaterialContainer(definition, variant_instance_container)
            quality_instance_container = self._updateQualityContainer(definition, variant_instance_container, material_instance_container)

            current_settings_instance_container = UM.Settings.InstanceContainer(name + "_current_settings")
            current_settings_instance_container.addMetaDataEntry("machine", name)
            current_settings_instance_container.addMetaDataEntry("type", "user")
            current_settings_instance_container.setDefinition(definitions[0])
            container_registry.addContainer(current_settings_instance_container)

            new_global_stack.addContainer(definition)
            if variant_instance_container:
                new_global_stack.addContainer(variant_instance_container)
            if material_instance_container:
                new_global_stack.addContainer(material_instance_container)
            if quality_instance_container:
                new_global_stack.addContainer(quality_instance_container)

            new_global_stack.addContainer(self._empty_quality_changes_container)
            new_global_stack.addContainer(current_settings_instance_container)

            ExtruderManager.getInstance().addMachineExtruders(definition, new_global_stack.getId())

            Application.getInstance().setGlobalContainerStack(new_global_stack)


    ##  Create a name that is not empty and unique
    #   \param container_type \type{string} Type of the container (machine, quality, ...)
    #   \param current_name \type{} Current name of the container, which may be an acceptable option
    #   \param new_name \type{string} Base name, which may not be unique
    #   \param fallback_name \type{string} Name to use when (stripped) new_name is empty
    #   \return \type{string} Name that is unique for the specified type and name/id
    def _createUniqueName(self, container_type, current_name, new_name, fallback_name):
        return UM.Settings.ContainerRegistry.getInstance().createUniqueName(container_type, current_name, new_name, fallback_name)

    ##  Convenience function to check if a stack has errors.
    def _checkStackForErrors(self, stack):
        if stack is None:
            return False

        for key in stack.getAllKeys():
            validation_state = stack.getProperty(key, "validationState")
            if validation_state in (UM.Settings.ValidatorState.Exception, UM.Settings.ValidatorState.MaximumError, UM.Settings.ValidatorState.MinimumError):
                return True
        return False

    ##  Remove all instances from the top instanceContainer (effectively removing all user-changed settings)
    @pyqtSlot()
    def clearUserSettings(self):
        if not self._active_container_stack:
            return

        self.blurSettings.emit()
        user_settings = self._active_container_stack.getTop()
        user_settings.clear()

    ##  Check if the global_container has instances in the user container
    @pyqtProperty(bool, notify = activeStackChanged)
    def hasUserSettings(self):
        if not self._global_container_stack:
            return False

        if self._global_container_stack.getTop().findInstances():
            return True

        for stack in ExtruderManager.getInstance().getMachineExtruders(self._global_container_stack.getId()):
            if stack.getTop().findInstances():
                return True

        return False

    ##  Check if the global profile does not contain error states
    #   Note that the _active_stack_valid is cached due to performance issues
    #   Calling _checkStackForErrors on every change is simply too expensive
    @pyqtProperty(bool, notify = activeValidationChanged)
    def isActiveStackValid(self):
        return bool(self._active_stack_valid)

    @pyqtProperty(str, notify = activeStackChanged)
    def activeUserProfileId(self):
        if self._active_container_stack:
            return self._active_container_stack.getTop().getId()

        return ""

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

    @pyqtProperty(str, notify = activeStackChanged)
    def activeStackId(self):
        if self._active_container_stack:
            return self._active_container_stack.getId()

        return ""

    @pyqtProperty(str, notify = activeMaterialChanged)
    def activeMaterialName(self):
        if self._active_container_stack:
            material = self._active_container_stack.findContainer({"type":"material"})
            if material:
                return material.getName()

        return ""

    @pyqtProperty(str, notify=activeMaterialChanged)
    def activeMaterialId(self):
        if self._active_container_stack:
            material = self._active_container_stack.findContainer({"type": "material"})
            if material:
                return material.getId()

        return ""

    @pyqtProperty("QVariantMap", notify = activeMaterialChanged)
    def allActiveMaterialIds(self):
        if not self._global_container_stack:
            return {}

        result = {}

        for stack in ExtruderManager.getInstance().getActiveGlobalAndExtruderStacks():
            material_container = stack.findContainer(type = "material")
            if not material_container:
                continue

            result[stack.getId()] = material_container.getId()

        return result

    @pyqtProperty(str, notify=activeQualityChanged)
    def activeQualityMaterialId(self):
        if self._active_container_stack:
            quality = self._active_container_stack.findContainer({"type": "quality"})
            if quality:
                return quality.getMetaDataEntry("material")

        return ""

    @pyqtProperty(str, notify=activeQualityChanged)
    def activeQualityName(self):
        if self._active_container_stack:
            quality = self._active_container_stack.findContainer({"type": "quality_changes"})
            if quality and quality != self._empty_quality_changes_container:
                return quality.getName()
            quality = self._active_container_stack.findContainer({"type": "quality"})
            if quality:
                return quality.getName()
        return ""

    @pyqtProperty(str, notify=activeQualityChanged)
    def activeQualityId(self):
        if self._global_container_stack:
            quality = self._global_container_stack.findContainer({"type": "quality_changes"})
            if quality and quality != self._empty_quality_changes_container:
                return quality.getId()
            quality = self._global_container_stack.findContainer({"type": "quality"})
            if quality:
                return quality.getId()
        return ""

    @pyqtProperty(str, notify = activeQualityChanged)
    def activeQualityType(self):
        if self._global_container_stack:
            quality = self._global_container_stack.findContainer(type = "quality")
            if quality:
                return quality.getMetaDataEntry("quality_type")
        return ""

    @pyqtProperty(str, notify = activeQualityChanged)
    def activeQualityChangesId(self):
        if self._global_container_stack:
            changes = self._global_container_stack.findContainer(type = "quality_changes")
            if changes:
                return changes.getId()
        return ""

    ## Check if a container is read_only
    @pyqtSlot(str, result = bool)
    def isReadOnly(self, container_id):
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = container_id)
        if not containers or not self._active_container_stack:
            return True
        return containers[0].isReadOnly()

    ## Copy the value of the setting of the current extruder to all other extruders as well as the global container.
    @pyqtSlot(str)
    def copyValueToExtruders(self, key):
        if not self._active_container_stack or self._global_container_stack.getProperty("machine_extruder_count", "value") <= 1:
            return

        new_value = self._active_container_stack.getProperty(key, "value")
        stacks = [stack for stack in ExtruderManager.getInstance().getMachineExtruders(self._global_container_stack.getId())]
        stacks.append(self._global_container_stack)
        for extruder_stack in stacks:
            if extruder_stack != self._active_container_stack and extruder_stack.getProperty(key, "value") != new_value:
                extruder_stack.getTop().setProperty(key, "value", new_value)

    @pyqtSlot(str)
    def setActiveMaterial(self, material_id):
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = material_id)
        if not containers or not self._active_container_stack:
            return

        old_variant = self._active_container_stack.findContainer({"type":"variant"})
        old_material = self._active_container_stack.findContainer({"type":"material"})
        old_quality = self._active_container_stack.findContainer({"type": "quality"})
        if old_material:
            old_material.nameChanged.disconnect(self._onMaterialNameChanged)

            material_index = self._active_container_stack.getContainerIndex(old_material)
            self._active_container_stack.replaceContainer(material_index, containers[0])

            containers[0].nameChanged.connect(self._onMaterialNameChanged)

            preferred_quality_name = None
            if old_quality:
                preferred_quality_name = old_quality.getName()

            self.setActiveQuality(self._updateQualityContainer(self._global_container_stack.getBottom(), old_variant, containers[0], preferred_quality_name).id)
        else:
            Logger.log("w", "While trying to set the active material, no material was found to replace.")

    @pyqtSlot(str)
    def setActiveVariant(self, variant_id):
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = variant_id)
        if not containers or not self._active_container_stack:
            return
        old_variant = self._active_container_stack.findContainer({"type": "variant"})
        old_material = self._active_container_stack.findContainer({"type": "material"})
        if old_variant:
            variant_index = self._active_container_stack.getContainerIndex(old_variant)
            self._active_container_stack.replaceContainer(variant_index, containers[0])

            preferred_material = None
            if old_material:
                preferred_material_name = old_material.getName()
            self.setActiveMaterial(self._updateMaterialContainer(self._global_container_stack.getBottom(), containers[0], preferred_material_name).id)
        else:
            Logger.log("w", "While trying to set the active variant, no variant was found to replace.")

    @pyqtSlot(str)
    def setActiveQuality(self, quality_id):
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = quality_id)
        if not containers or not self._global_container_stack:
            return

        quality_container = None
        quality_changes_container = self._empty_quality_changes_container

        container_type = containers[0].getMetaDataEntry("type")

        if container_type == "quality":
            quality_container = containers[0]
        elif container_type == "quality_changes":
            quality_changes_container = containers[0]
            containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(
                quality_type = quality_changes_container.getMetaDataEntry("quality"))
            if not containers:
                Logger.log("e", "Could not find quality %s for changes %s, not changing quality", quality_changes_container.getMetaDataEntry("quality"), quality_changes_container.getId())
                return
            quality_container = containers[0]
        else:
            Logger.log("e", "Tried to set quality to a container that is not of the right type")
            return

        quality_type = quality_container.getMetaDataEntry("quality_type")
        if not quality_type:
            quality_type = quality_changes_container.getName()

        for stack in ExtruderManager.getInstance().getActiveGlobalAndExtruderStacks():
            extruder_id = stack.getId() if stack != self._global_container_stack else None

            criteria = { "quality_type": quality_type, "extruder": extruder_id }

            if self._global_container_stack.getMetaDataEntry("has_machine_quality"):
                material = stack.findContainer(type = "material")
                criteria["material"] = material.getId()

            stack_quality = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(**criteria)
            if not stack_quality:
                criteria.pop("extruder")
                stack_quality = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(**criteria)
                if not stack_quality:
                    stack_quality = quality_container
                else:
                    stack_quality = stack_quality[0]
            else:
                stack_quality = stack_quality[0]

            if quality_changes_container != self._empty_quality_changes_container:
                stack_quality_changes = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(name = quality_changes_container.getName(), extruder = extruder_id)[0]
            else:
                stack_quality_changes = self._empty_quality_changes_container

            old_quality = stack.findContainer(type = "quality")
            old_quality.nameChanged.disconnect(self._onQualityNameChanged)
            old_changes = stack.findContainer(type = "quality_changes")
            old_changes.nameChanged.disconnect(self._onQualityNameChanged)

            stack.replaceContainer(stack.getContainerIndex(old_quality), stack_quality)
            stack.replaceContainer(stack.getContainerIndex(old_changes), stack_quality_changes)

            stack_quality.nameChanged.connect(self._onQualityNameChanged)
            stack_quality_changes.nameChanged.connect(self._onQualityNameChanged)

        if self.hasUserSettings and Preferences.getInstance().getValue("cura/active_mode") == 1:
            # Ask the user if the user profile should be cleared or not (discarding the current settings)
            # In Simple Mode we assume the user always wants to keep the (limited) current settings
            details = catalog.i18nc("@label", "You made changes to the following setting(s):")
            user_settings = self._active_container_stack.getTop().findInstances(**{})
            for setting in user_settings:
                details = details + "\n    " + setting.definition.label

            Application.getInstance().messageBox(catalog.i18nc("@window:title", "Switched profiles"), catalog.i18nc("@label", "Do you want to transfer your changed settings to this profile?"),
                                                 catalog.i18nc("@label", "If you transfer your settings they will override settings in the profile."), details,
                                                 buttons = QMessageBox.Yes + QMessageBox.No, icon = QMessageBox.Question, callback = self._keepUserSettingsDialogCallback)

        self.activeQualityChanged.emit()

    def _keepUserSettingsDialogCallback(self, button):
        if button == QMessageBox.Yes:
            # Yes, keep the settings in the user profile with this profile
            pass
        elif button == QMessageBox.No:
            # No, discard the settings in the user profile
            global_stack = Application.getInstance().getGlobalContainerStack()
            for extruder in ExtruderManager.getInstance().getMachineExtruders(global_stack.getId()):
                extruder.getTop().clear()

            global_stack.getTop().clear()

    @pyqtProperty(str, notify = activeVariantChanged)
    def activeVariantName(self):
        if self._active_container_stack:
            variant = self._active_container_stack.findContainer({"type": "variant"})
            if variant:
                return variant.getName()

        return ""

    @pyqtProperty(str, notify = activeVariantChanged)
    def activeVariantId(self):
        if self._active_container_stack:
            variant = self._active_container_stack.findContainer({"type": "variant"})
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

    ##  Gets how the active definition calls variants
    #   Caveat: per-definition-variant-title is currently not translated (though the fallback is)
    @pyqtProperty(str, notify = globalContainerChanged)
    def activeDefinitionVariantsName(self):
        fallback_title = catalog.i18nc("@label", "Nozzle")
        if self._global_container_stack:
            return self._global_container_stack.getBottom().getMetaDataEntry("variants_name", fallback_title)

        return fallback_title

    @pyqtSlot(str, str)
    def renameMachine(self, machine_id, new_name):
        containers = UM.Settings.ContainerRegistry.getInstance().findContainerStacks(id = machine_id)
        if containers:
            new_name = self._createUniqueName("machine", containers[0].getName(), new_name, containers[0].getBottom().getName())
            containers[0].setName(new_name)
            self.globalContainerChanged.emit()

    @pyqtSlot(str)
    def removeMachine(self, machine_id):
        # If the machine that is being removed is the currently active machine, set another machine as the active machine.
        activate_new_machine = (self._global_container_stack and self._global_container_stack.getId() == machine_id)

        ExtruderManager.getInstance().removeMachineExtruders(machine_id)

        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(type = "user", machine = machine_id)
        for container in containers:
            UM.Settings.ContainerRegistry.getInstance().removeContainer(container.getId())
        UM.Settings.ContainerRegistry.getInstance().removeContainer(machine_id)

        if activate_new_machine:
            stacks = UM.Settings.ContainerRegistry.getInstance().findContainerStacks(type = "machine")
            if stacks:
                Application.getInstance().setGlobalContainerStack(stacks[0])


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

    ##  Property to indicate if a machine has "specialized" material profiles.
    #   Some machines have their own material profiles that "override" the default catch all profiles.
    @pyqtProperty(bool, notify = globalContainerChanged)
    def filterMaterialsByMachine(self):
        if self._global_container_stack:
            return bool(self._global_container_stack.getMetaDataEntry("has_machine_materials", False))

        return False

    ##  Property to indicate if a machine has "specialized" quality profiles.
    #   Some machines have their own quality profiles that "override" the default catch all profiles.
    @pyqtProperty(bool, notify = globalContainerChanged)
    def filterQualityByMachine(self):
        if self._global_container_stack:
            return bool(self._global_container_stack.getMetaDataEntry("has_machine_quality", False))
        return False

    ##  Get the Definition ID of a machine (specified by ID)
    #   \param machine_id string machine id to get the definition ID of
    #   \returns DefinitionID (string) if found, None otherwise
    @pyqtSlot(str, result = str)
    def getDefinitionByMachineId(self, machine_id):
        containers = UM.Settings.ContainerRegistry.getInstance().findContainerStacks(id=machine_id)
        if containers:
            return containers[0].getBottom().getId()

    @staticmethod
    def createMachineManager(engine=None, script_engine=None):
        return MachineManager()

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

    def _updateMaterialContainer(self, definition, variant_container = None, preferred_material_name = None):
        if not definition.getMetaDataEntry("has_materials"):
            return self._empty_material_container

        search_criteria = { "type": "material" }

        if definition.getMetaDataEntry("has_machine_materials"):
            search_criteria["definition"] = definition.id

            if definition.getMetaDataEntry("has_variants") and variant_container:
                search_criteria["variant"] = variant_container.id
        else:
            search_criteria["definition"] = "fdmprinter"

        if preferred_material_name:
            search_criteria["name"] = preferred_material_name
        else:
            preferred_material = definition.getMetaDataEntry("preferred_material")
            if preferred_material:
                search_criteria["id"] = preferred_material

        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(**search_criteria)
        if containers:
            return containers[0]

        if "name" in search_criteria or "id" in search_criteria:
            # If a material by this name can not be found, try a wider set of search criteria
            search_criteria.pop("name", None)
            search_criteria.pop("id", None)

            containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(**search_criteria)
            if containers:
                return containers[0]

        return self._empty_material_container

    def _updateQualityContainer(self, definition, variant_container, material_container = None, preferred_quality_name = None):
        container_registry = UM.Settings.ContainerRegistry.getInstance()
        search_criteria = { "type": "quality" }

        if definition.getMetaDataEntry("has_machine_quality"):
            search_criteria["definition"] = definition.id

            if definition.getMetaDataEntry("has_materials") and material_container:
                search_criteria["material"] = material_container.id
        else:
            search_criteria["definition"] = "fdmprinter"

        if preferred_quality_name and preferred_quality_name != "empty":
            search_criteria["name"] = preferred_quality_name
        else:
            preferred_quality = definition.getMetaDataEntry("preferred_quality")
            if preferred_quality:
                search_criteria["id"] = preferred_quality

        containers = container_registry.findInstanceContainers(**search_criteria)
        if containers:
            return containers[0]

        if "material" in search_criteria:
            # If a quality for this specific material cannot be found, try finding qualities for a generic version of the material
            material_search_criteria = { "type": "material", "material": material_container.getMetaDataEntry("material"), "color_name": "Generic" }
            if definition.getMetaDataEntry("has_machine_quality"):
                material_search_criteria["definition"] = definition.id

                if definition.getMetaDataEntry("has_variants") and variant_container:
                    material_search_criteria["variant"] = variant_container.id
            else:
                material_search_criteria["definition"] = "fdmprinter"

            material_containers = container_registry.findInstanceContainers(**material_search_criteria)
            if material_containers:
                search_criteria["material"] = material_containers[0].getId()

                containers = container_registry.findInstanceContainers(**search_criteria)
                if containers:
                    return containers[0]

        if "name" in search_criteria or "id" in search_criteria:
            # If a quality by this name can not be found, try a wider set of search criteria
            search_criteria.pop("name", None)
            search_criteria.pop("id", None)

            containers = container_registry.findInstanceContainers(**search_criteria)
            if containers:
                return containers[0]

        return self._empty_quality_container

    def _onMachineNameChanged(self):
        self.globalContainerChanged.emit()

    def _onMaterialNameChanged(self):
        self.activeMaterialChanged.emit()

    def _onQualityNameChanged(self):
        self.activeQualityChanged.emit()
