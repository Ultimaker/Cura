# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
from UM import Util

from UM.Application import Application
from UM.Preferences import Preferences
from UM.Logger import Logger
from UM.Message import Message

import UM.Settings

from cura.QualityManager import QualityManager
from cura.PrinterOutputDevice import PrinterOutputDevice
from . import ExtruderManager

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

import os

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
        self.globalValueChanged.connect(self.activeStackValueChanged)
        ExtruderManager.getInstance().activeExtruderChanged.connect(self.activeStackChanged)
        self.activeStackChanged.connect(self.activeStackValueChanged)

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

        self._material_incompatible_message = Message(catalog.i18nc("@info:status",
                                              "The selected material is incompatible with the selected machine or configuration."))

    globalContainerChanged = pyqtSignal() # Emitted whenever the global stack is changed (ie: when changing between printers, changing a global profile, but not when changing a value)
    activeMaterialChanged = pyqtSignal()
    activeVariantChanged = pyqtSignal()
    activeQualityChanged = pyqtSignal()
    activeStackChanged = pyqtSignal()  # Emitted whenever the active stack is changed (ie: when changing between extruders, changing a profile, but not when changing a value)

    globalValueChanged = pyqtSignal()  # Emitted whenever a value inside global container is changed.
    activeStackValueChanged = pyqtSignal()  # Emitted whenever a value inside the active stack is changed.
    activeStackValidationChanged = pyqtSignal()  # Emitted whenever a validation inside active container is changed

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

    def _onMaterialIdChanged(self, index, material_id):
        if not self._global_container_stack:
            return

        definition_id = "fdmprinter"
        if self._global_container_stack.getMetaDataEntry("has_machine_materials", False):
            definition_id = self.activeQualityDefinitionId
        extruder_manager = ExtruderManager.getInstance()
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(type = "material", definition = definition_id, GUID = material_id)
        if containers:  # New material ID is known
            extruders = list(extruder_manager.getMachineExtruders(self.activeMachineId))
            matching_extruder = None
            for extruder in extruders:
                if str(index) == extruder.getMetaDataEntry("position"):
                    matching_extruder = extruder
                    break

            if matching_extruder and matching_extruder.findContainer({"type": "material"}).getMetaDataEntry("GUID") != material_id:
                # Save the material that needs to be changed. Multiple changes will be handled by the callback.
                variant_container = matching_extruder.findContainer({"type": "variant"})
                if self._global_container_stack.getBottom().getMetaDataEntry("has_variants") and variant_container:
                    variant_id = self.getQualityVariantId(self._global_container_stack.getBottom(), variant_container)
                    for container in containers:
                        if container.getMetaDataEntry("variant") == variant_id:
                            self._auto_materials_changed[str(index)] = container.getId()
                            break
                else:
                    # Just use the first result we found.
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

        old_active_container_stack = self._active_container_stack

        if self._active_container_stack and self._active_container_stack != self._global_container_stack:
            self._active_container_stack.containersChanged.disconnect(self._onInstanceContainersChanged)
            self._active_container_stack.propertyChanged.disconnect(self._onPropertyChanged)
        self._active_container_stack = ExtruderManager.getInstance().getActiveExtruderStack()
        if self._active_container_stack:
            self._active_container_stack.containersChanged.connect(self._onInstanceContainersChanged)
            self._active_container_stack.propertyChanged.connect(self._onPropertyChanged)
        else:
            self._active_container_stack = self._global_container_stack

        old_active_stack_valid = self._active_stack_valid
        self._active_stack_valid = not self._checkStackForErrors(self._active_container_stack)
        if old_active_stack_valid != self._active_stack_valid:
            self.activeStackValidationChanged.emit()

        if old_active_container_stack != self._active_container_stack:
            # Many methods and properties related to the active quality actually depend
            # on _active_container_stack. If it changes, then the properties change.
            self.activeQualityChanged.emit()

    def _onInstanceContainersChanged(self, container):
        container_type = container.getMetaDataEntry("type")

        if container_type == "material":
            self.activeMaterialChanged.emit()
        elif container_type == "variant":
            self.activeVariantChanged.emit()
        elif container_type == "quality":
            self.activeQualityChanged.emit()

    def _onPropertyChanged(self, key, property_name):
        if property_name == "value":
            # Notify UI items, such as the "changed" star in profile pull down menu.
            self.activeStackValueChanged.emit()

        if property_name == "validationState":
            if self._active_stack_valid:
                if self._active_container_stack.getProperty(key, "settable_per_extruder"):
                    changed_validation_state = self._active_container_stack.getProperty(key, property_name)
                else:
                    changed_validation_state = self._global_container_stack.getProperty(key, property_name)
                if changed_validation_state in (UM.Settings.ValidatorState.Exception, UM.Settings.ValidatorState.MaximumError, UM.Settings.ValidatorState.MinimumError):
                    self._active_stack_valid = False
                    self.activeStackValidationChanged.emit()
            else:
                if not self._checkStackForErrors(self._active_container_stack) and not self._checkStackForErrors(self._global_container_stack):
                    self._active_stack_valid = True
                    self.activeStackValidationChanged.emit()

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
    @pyqtProperty(bool, notify = activeStackValueChanged)
    def hasUserSettings(self):
        if not self._global_container_stack:
            return False

        if self._global_container_stack.getTop().findInstances():
            return True

        stacks = list(ExtruderManager.getInstance().getMachineExtruders(self._global_container_stack.getId()))
        for stack in stacks:
            if stack.getTop().findInstances():
                return True

        return False

    ##  Delete a user setting from the global stack and all extruder stacks.
    #   \param key \type{str} the name of the key to delete
    @pyqtSlot(str)
    def clearUserSettingAllCurrentStacks(self, key):
        if not self._global_container_stack:
            return

        send_emits_containers = []

        top_container = self._global_container_stack.getTop()
        top_container.removeInstance(key, postpone_emit=True)
        send_emits_containers.append(top_container)

        linked = not self._global_container_stack.getProperty(key, "settable_per_extruder") or \
                      self._global_container_stack.getProperty(key, "limit_to_extruder") != "-1"

        if not linked:
            stack = ExtruderManager.getInstance().getActiveExtruderStack()
            stacks = [stack]
        else:
            stacks = ExtruderManager.getInstance().getMachineExtruders(self._global_container_stack.getId())

        for stack in stacks:
            if stack is not None:
                container = stack.getTop()
                container.removeInstance(key, postpone_emit=True)
                send_emits_containers.append(container)

        for container in send_emits_containers:
            container.sendPostponedEmits()

    ##  Check if the global profile does not contain error states
    #   Note that the _active_stack_valid is cached due to performance issues
    #   Calling _checkStackForErrors on every change is simply too expensive
    @pyqtProperty(bool, notify = activeStackValidationChanged)
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

    ##  Gets the layer height of the currently active quality profile.
    #
    #   This is indicated together with the name of the active quality profile.
    #
    #   \return The layer height of the currently active quality profile. If
    #   there is no quality profile, this returns 0.
    @pyqtProperty(float, notify=activeQualityChanged)
    def activeQualityLayerHeight(self):
        if not self._global_container_stack:
            return 0

        quality_changes = self._global_container_stack.findContainer({"type": "quality_changes"})
        if quality_changes:
            value = self._global_container_stack.getRawProperty("layer_height", "value", skip_until_container = quality_changes.getId())
            if isinstance(value, UM.Settings.SettingFunction):
                value = value(self._global_container_stack)
            return value
        quality = self._global_container_stack.findContainer({"type": "quality"})
        if quality:
            value = self._global_container_stack.getRawProperty("layer_height", "value", skip_until_container = quality.getId())
            if isinstance(value, UM.Settings.SettingFunction):
                value = value(self._global_container_stack)
            return value

        return 0 #No quality profile.

    ##  Get the Material ID associated with the currently active material
    #   \returns MaterialID (string) if found, empty string otherwise
    @pyqtProperty(str, notify=activeQualityChanged)
    def activeQualityMaterialId(self):
        if self._active_container_stack:
            quality = self._active_container_stack.findContainer({"type": "quality"})
            if quality:
                material_id = quality.getMetaDataEntry("material")
                if material_id:
                    # if the currently active machine inherits its qualities from a different machine
                    # definition, make sure to return a material that is relevant to that machine definition
                    definition_id = self.activeDefinitionId
                    quality_definition_id = self.activeQualityDefinitionId
                    if definition_id != quality_definition_id:
                        material_id = material_id.replace(definition_id, quality_definition_id, 1)

                    return material_id
        return ""

    @pyqtProperty(str, notify=activeQualityChanged)
    def activeQualityName(self):
        if self._active_container_stack and self._global_container_stack:
            quality = self._global_container_stack.findContainer({"type": "quality_changes"})
            if quality and quality != self._empty_quality_changes_container:
                return quality.getName()
            quality = self._active_container_stack.findContainer({"type": "quality"})
            if quality:
                return quality.getName()
        return ""

    @pyqtProperty(str, notify=activeQualityChanged)
    def activeQualityId(self):
        if self._active_container_stack:
            quality = self._active_container_stack.findContainer({"type": "quality_changes"})
            if quality and quality != self._empty_quality_changes_container:
                return quality.getId()
            quality = self._active_container_stack.findContainer({"type": "quality"})
            if quality:
                return quality.getId()
        return ""

    @pyqtProperty(str, notify=activeQualityChanged)
    def globalQualityId(self):
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
        if self._active_container_stack:
            quality = self._active_container_stack.findContainer(type = "quality")
            if quality:
                return quality.getMetaDataEntry("quality_type")
        return ""

    @pyqtProperty(bool, notify = activeQualityChanged)
    def isActiveQualitySupported(self):
        if self._active_container_stack:
            quality = self._active_container_stack.findContainer(type = "quality")
            if quality:
                return Util.parseBool(quality.getMetaDataEntry("supported", True))
        return ""

    ##  Get the Quality ID associated with the currently active extruder
    #   Note that this only returns the "quality", not the "quality_changes"
    #   \returns QualityID (string) if found, empty string otherwise
    #   \sa activeQualityId()
    #   \todo Ideally, this method would be named activeQualityId(), and the other one
    #         would be named something like activeQualityOrQualityChanges() for consistency
    @pyqtProperty(str, notify = activeQualityChanged)
    def activeQualityContainerId(self):
        # We're using the active stack instead of the global stack in case the list of qualities differs per extruder
        if self._global_container_stack:
            quality = self._active_container_stack.findContainer(type = "quality")
            if quality:
                return quality.getId()
        return ""

    @pyqtProperty(str, notify = activeQualityChanged)
    def activeQualityChangesId(self):
        if self._active_container_stack:
            changes = self._active_container_stack.findContainer(type = "quality_changes")
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

    ## Set the active material by switching out a container
    #  Depending on from/to material+current variant, a quality profile is chosen and set.
    @pyqtSlot(str)
    def setActiveMaterial(self, material_id):
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = material_id)
        if not containers or not self._active_container_stack:
            return
        material_container = containers[0]

        Logger.log("d", "Attempting to change the active material to %s", material_id)

        old_material = self._active_container_stack.findContainer({"type": "material"})
        old_quality = self._active_container_stack.findContainer({"type": "quality"})
        old_quality_changes = self._active_container_stack.findContainer({"type": "quality_changes"})
        if not old_material:
            Logger.log("w", "While trying to set the active material, no material was found to replace it.")
            return

        if old_quality_changes.getId() == "empty_quality_changes":
            old_quality_changes = None

        self.blurSettings.emit()
        old_material.nameChanged.disconnect(self._onMaterialNameChanged)

        material_index = self._active_container_stack.getContainerIndex(old_material)
        self._active_container_stack.replaceContainer(material_index, material_container)
        Logger.log("d", "Active material changed")

        material_container.nameChanged.connect(self._onMaterialNameChanged)

        if material_container.getMetaDataEntry("compatible") == False:
            self._material_incompatible_message.show()
        else:
            self._material_incompatible_message.hide()

        new_quality_id = old_quality.getId()
        quality_type = old_quality.getMetaDataEntry("quality_type")
        if old_quality_changes:
            quality_type = old_quality_changes.getMetaDataEntry("quality_type")
            new_quality_id = old_quality_changes.getId()

        # See if the requested quality type is available in the new situation.
        machine_definition = self._active_container_stack.getBottom()
        quality_manager = QualityManager.getInstance()
        candidate_quality = quality_manager.findQualityByQualityType(quality_type,
                                   quality_manager.getWholeMachineDefinition(machine_definition),
                                   [material_container])
        if not candidate_quality or candidate_quality.getId() == "empty_quality":
            # Fall back to a quality
            new_quality = quality_manager.findQualityByQualityType(None,
                                quality_manager.getWholeMachineDefinition(machine_definition),
                                [material_container])
            if new_quality:
                new_quality_id = new_quality.getId()
        else:
            if not old_quality_changes:
                new_quality_id = candidate_quality.getId()

        self.setActiveQuality(new_quality_id)

    @pyqtSlot(str)
    def setActiveVariant(self, variant_id):
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = variant_id)
        if not containers or not self._active_container_stack:
            return
        Logger.log("d", "Attempting to change the active variant to %s", variant_id)
        old_variant = self._active_container_stack.findContainer({"type": "variant"})
        old_material = self._active_container_stack.findContainer({"type": "material"})
        if old_variant:
            self.blurSettings.emit()
            variant_index = self._active_container_stack.getContainerIndex(old_variant)
            self._active_container_stack.replaceContainer(variant_index, containers[0])
            Logger.log("d", "Active variant changed")
            preferred_material = None
            if old_material:
                preferred_material_name = old_material.getName()

            self.setActiveMaterial(self._updateMaterialContainer(self._global_container_stack.getBottom(), containers[0], preferred_material_name).id)
        else:
            Logger.log("w", "While trying to set the active variant, no variant was found to replace.")

    ##  set the active quality
    #   \param quality_id The quality_id of either a quality or a quality_changes
    @pyqtSlot(str)
    def setActiveQuality(self, quality_id):
        self.blurSettings.emit()

        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = quality_id)
        if not containers or not self._global_container_stack:
            return

        Logger.log("d", "Attempting to change the active quality to %s", quality_id)

        # Quality profile come in two flavours: type=quality and type=quality_changes
        # If we found a quality_changes profile then look up its parent quality profile.
        container_type = containers[0].getMetaDataEntry("type")
        quality_name = containers[0].getName()
        quality_type = containers[0].getMetaDataEntry("quality_type")

        # Get quality container and optionally the quality_changes container.
        if container_type == "quality":
            new_quality_settings_list = self.determineQualityAndQualityChangesForQualityType(quality_type)
        elif container_type == "quality_changes":
            new_quality_settings_list = self._determineQualityAndQualityChangesForQualityChanges(quality_name)
        else:
            Logger.log("e", "Tried to set quality to a container that is not of the right type")
            return

        name_changed_connect_stacks = []  # Connect these stacks to the name changed callback
        for setting_info in new_quality_settings_list:
            stack = setting_info["stack"]
            stack_quality = setting_info["quality"]
            stack_quality_changes = setting_info["quality_changes"]

            name_changed_connect_stacks.append(stack_quality)
            name_changed_connect_stacks.append(stack_quality_changes)
            self._replaceQualityOrQualityChangesInStack(stack, stack_quality, postpone_emit = True)
            self._replaceQualityOrQualityChangesInStack(stack, stack_quality_changes, postpone_emit = True)

        # Send emits that are postponed in replaceContainer.
        # Here the stacks are finished replacing and every value can be resolved based on the current state.
        for setting_info in new_quality_settings_list:
            setting_info["stack"].sendPostponedEmits()

        # Connect to onQualityNameChanged
        for stack in name_changed_connect_stacks:
            stack.nameChanged.connect(self._onQualityNameChanged)

        if self.hasUserSettings and Preferences.getInstance().getValue("cura/active_mode") == 1:
            self._askUserToKeepOrClearCurrentSettings()

        self.activeQualityChanged.emit()

    ##  Determine the quality and quality changes settings for the current machine for a quality name.
    #
    #   \param quality_name \type{str} the name of the quality.
    #   \return \type{List[Dict]} with keys "stack", "quality" and "quality_changes".
    def determineQualityAndQualityChangesForQualityType(self, quality_type):
        quality_manager = QualityManager.getInstance()
        result = []
        empty_quality_changes = self._empty_quality_changes_container
        global_container_stack = self._global_container_stack
        global_machine_definition = quality_manager.getParentMachineDefinition(global_container_stack.getBottom())

        extruder_stacks = ExtruderManager.getInstance().getActiveExtruderStacks()
        if extruder_stacks:
            stacks = extruder_stacks
        else:
            stacks = [global_container_stack]

        for stack in stacks:
            material = stack.findContainer(type="material")
            quality = quality_manager.findQualityByQualityType(quality_type, global_machine_definition, [material])
            result.append({"stack": stack, "quality": quality, "quality_changes": empty_quality_changes})

        if extruder_stacks:
            # Add an extra entry for the global stack.
            result.append({"stack": global_container_stack, "quality": result[0]["quality"],
                           "quality_changes": empty_quality_changes})
        return result

    ##  Determine the quality and quality changes settings for the current machine for a quality changes name.
    #
    #   \param quality_changes_name \type{str} the name of the quality changes.
    #   \return \type{List[Dict]} with keys "stack", "quality" and "quality_changes".
    def _determineQualityAndQualityChangesForQualityChanges(self, quality_changes_name):
        result = []
        quality_manager = QualityManager.getInstance()

        global_container_stack = self._global_container_stack
        global_machine_definition = quality_manager.getParentMachineDefinition(global_container_stack.getBottom())

        quality_changes_profiles = quality_manager.findQualityChangesByName(quality_changes_name,
                                                                            global_machine_definition)

        global_quality_changes = [qcp for qcp in quality_changes_profiles if qcp.getMetaDataEntry("extruder") is None][0]
        material = global_container_stack.findContainer(type="material")

        # For the global stack, find a quality which matches the quality_type in
        # the quality changes profile and also satisfies any material constraints.
        quality_type = global_quality_changes.getMetaDataEntry("quality_type")
        global_quality = quality_manager.findQualityByQualityType(quality_type, global_machine_definition, [material])

        # Find the values for each extruder.
        extruder_stacks = ExtruderManager.getInstance().getActiveExtruderStacks()

        for stack in extruder_stacks:
            extruder_definition = quality_manager.getParentMachineDefinition(stack.getBottom())

            quality_changes_list = [qcp for qcp in quality_changes_profiles
                                    if qcp.getMetaDataEntry("extruder") == extruder_definition.getId()]
            if quality_changes_list:
                quality_changes = quality_changes_list[0]
            else:
                quality_changes = global_quality_changes

            material = stack.findContainer(type="material")
            quality = quality_manager.findQualityByQualityType(quality_type, global_machine_definition, [material])

            result.append({"stack": stack, "quality": quality, "quality_changes": quality_changes})

        if extruder_stacks:
            # Duplicate the quality from the 1st extruder into the global stack. If anyone
            # then looks in the global stack, they should get a reasonable view.
            result.append({"stack": global_container_stack, "quality": result[0]["quality"], "quality_changes": global_quality_changes})
        else:
            result.append({"stack": global_container_stack, "quality": global_quality, "quality_changes": global_quality_changes})

        return result

    def _replaceQualityOrQualityChangesInStack(self, stack, container, postpone_emit = False):
        # Disconnect the signal handling from the old container.
        old_container = stack.findContainer(type=container.getMetaDataEntry("type"))
        if old_container:
            old_container.nameChanged.disconnect(self._onQualityNameChanged)
        else:
            Logger.log("w", "Could not find old "+  container.getMetaDataEntry("type") + " while changing active " + container.getMetaDataEntry("type") + ".")

        # Swap in the new container into the stack.
        stack.replaceContainer(stack.getContainerIndex(old_container), container, postpone_emit = postpone_emit)

        # Attach the needed signal handling.
        container.nameChanged.connect(self._onQualityNameChanged)

    def _askUserToKeepOrClearCurrentSettings(self):
        # Ask the user if the user profile should be cleared or not (discarding the current settings)
        # In Simple Mode we assume the user always wants to keep the (limited) current settings
        details_text = catalog.i18nc("@label", "You made changes to the following setting(s):")

        # user changes in global stack
        details_list = [setting.definition.label for setting in self._global_container_stack.getTop().findInstances(**{})]

        # user changes in extruder stacks
        stacks = list(ExtruderManager.getInstance().getMachineExtruders(self._global_container_stack.getId()))
        for stack in stacks:
            details_list.extend([
                "%s (%s)" % (setting.definition.label, stack.getName())
                for setting in stack.getTop().findInstances(**{})])

        # Format to output string
        details = "\n    ".join([details_text, ] + details_list)

        Application.getInstance().messageBox(catalog.i18nc("@window:title", "Switched profiles"),
                                             catalog.i18nc("@label",
                                                           "Do you want to transfer your changed settings to this profile?"),
                                             catalog.i18nc("@label",
                                                           "If you transfer your settings they will override settings in the profile."),
                                             details,
                                             buttons=QMessageBox.Yes + QMessageBox.No, icon=QMessageBox.Question,
                                             callback=self._keepUserSettingsDialogCallback)

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

    ##  Get the Definition ID to use to select quality profiles for the currently active machine
    #   \returns DefinitionID (string) if found, empty string otherwise
    #   \sa getQualityDefinitionId
    @pyqtProperty(str, notify = globalContainerChanged)
    def activeQualityDefinitionId(self):
        if self._global_container_stack:
            return self.getQualityDefinitionId(self._global_container_stack.getBottom())
        return ""

    ##  Get the Definition ID to use to select quality profiles for machines of the specified definition
    #   This is normally the id of the definition itself, but machines can specify a different definition to inherit qualities from
    #   \param definition (DefinitionContainer) machine definition
    #   \returns DefinitionID (string) if found, empty string otherwise
    def getQualityDefinitionId(self, definition):
        return QualityManager.getInstance().getParentMachineDefinition(definition).getId()

    ##  Get the Variant ID to use to select quality profiles for the currently active variant
    #   \returns VariantID (string) if found, empty string otherwise
    #   \sa getQualityVariantId
    @pyqtProperty(str, notify = activeVariantChanged)
    def activeQualityVariantId(self):
        if self._active_container_stack:
            variant = self._active_container_stack.findContainer({"type": "variant"})
            if variant:
                return self.getQualityVariantId(self._global_container_stack.getBottom(), variant)
        return ""

    ##  Get the Variant ID to use to select quality profiles for variants of the specified definitions
    #   This is normally the id of the variant itself, but machines can specify a different definition
    #   to inherit qualities from, which has consequences for the variant to use as well
    #   \param definition (DefinitionContainer) machine definition
    #   \param variant (DefinitionContainer) variant definition
    #   \returns VariantID (string) if found, empty string otherwise
    def getQualityVariantId(self, definition, variant):
        variant_id = variant.getId()
        definition_id = definition.getId()
        quality_definition_id = self.getQualityDefinitionId(definition)

        if definition_id != quality_definition_id:
            variant_id = variant_id.replace(definition_id, quality_definition_id, 1)
        return variant_id

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
        machine_definition_id = UM.Application.getInstance().getMachineManager().getQualityDefinitionId(definition)
        containers = []
        preferred_variant = definition.getMetaDataEntry("preferred_variant")
        if preferred_variant:
            containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(type = "variant", definition = machine_definition_id, id = preferred_variant)
        if not containers:
            containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(type = "variant", definition = machine_definition_id)

        if containers:
            return containers[0]

        return self._empty_variant_container

    def _updateMaterialContainer(self, definition, variant_container = None, preferred_material_name = None):
        if not definition.getMetaDataEntry("has_materials"):
            return self._empty_material_container

        search_criteria = { "type": "material" }

        if definition.getMetaDataEntry("has_machine_materials"):
            search_criteria["definition"] = self.getQualityDefinitionId(definition)

            if definition.getMetaDataEntry("has_variants") and variant_container:
                search_criteria["variant"] = self.getQualityVariantId(definition, variant_container)
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

        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(**search_criteria)
        if "variant" in search_criteria or "id" in search_criteria:
            # If a material by this name can not be found, try a wider set of search criteria
            search_criteria.pop("variant", None)
            search_criteria.pop("id", None)
            containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(**search_criteria)
            if containers:
                return containers[0]
        Logger.log("w", "Unable to find a material container with provided criteria, returning an empty one instead.")
        return self._empty_material_container

    def _updateQualityContainer(self, definition, variant_container, material_container = None, preferred_quality_name = None):
        container_registry = UM.Settings.ContainerRegistry.getInstance()
        search_criteria = { "type": "quality" }

        if definition.getMetaDataEntry("has_machine_quality"):
            search_criteria["definition"] = self.getQualityDefinitionId(definition)

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
            # First check if we can solve our material not found problem by checking if we can find quality containers
            # that are assigned to the parents of this material profile.
            try:
                inherited_files = material_container.getInheritedFiles()
            except AttributeError:  # Material_container does not support inheritance.
                inherited_files = []

            if inherited_files:
                for inherited_file in inherited_files:
                    # Extract the ID from the path we used to load the file.
                    search_criteria["material"] = os.path.basename(inherited_file).split(".")[0]
                    containers = container_registry.findInstanceContainers(**search_criteria)
                    if containers:
                        return containers[0]
            # We still weren't able to find a quality for this specific material.
            # Try to find qualities for a generic version of the material.
            material_search_criteria = { "type": "material", "material": material_container.getMetaDataEntry("material"), "color_name": "Generic"}
            if definition.getMetaDataEntry("has_machine_quality"):
                if material_container:
                    material_search_criteria["definition"] = material_container.getDefinition().id

                    if definition.getMetaDataEntry("has_variants"):
                        material_search_criteria["variant"] = material_container.getMetaDataEntry("variant")
                else:
                    material_search_criteria["definition"] = self.getQualityDefinitionId(definition)

                    if definition.getMetaDataEntry("has_variants") and variant_container:
                        material_search_criteria["variant"] = self.getQualityVariantId(definition, variant_container)
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

        # Notify user that we were unable to find a matching quality
        message = Message(catalog.i18nc("@info:status", "Unable to find a quality profile for this combination. Default settings will be used instead."))
        message.show()
        return self._empty_quality_container

    ##  Finds a quality-changes container to use if any other container
    #   changes.
    #
    #   \param quality_type The quality type to find a quality-changes for.
    #   \param preferred_quality_changes_name The name of the quality-changes to
    #   pick, if any such quality-changes profile is available.
    def _updateQualityChangesContainer(self, quality_type, preferred_quality_changes_name = None):
        container_registry = UM.Settings.ContainerRegistry.getInstance() # Cache.
        search_criteria = { "type": "quality_changes" }

        search_criteria["quality"] = quality_type
        if preferred_quality_changes_name:
            search_criteria["name"] = preferred_quality_changes_name

        # Try to search with the name in the criteria first, since we prefer to have the correct name.
        containers = container_registry.findInstanceContainers(**search_criteria)
        if containers: # Found one!
            return containers[0]

        if "name" in search_criteria:
            del search_criteria["name"] # Not found, then drop the name requirement (if we had one) and search again.
            containers = container_registry.findInstanceContainers(**search_criteria)
            if containers:
                return containers[0]

        return self._empty_quality_changes_container # Didn't find anything with the required quality_type.

    def _onMachineNameChanged(self):
        self.globalContainerChanged.emit()

    def _onMaterialNameChanged(self):
        self.activeMaterialChanged.emit()

    def _onQualityNameChanged(self):
        self.activeQualityChanged.emit()
