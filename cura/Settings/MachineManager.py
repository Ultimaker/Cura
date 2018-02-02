# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import collections
import time
#Type hinting.
from typing import Union, List, Dict

from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Signal import Signal

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, QTimer
from UM.FlameProfiler import pyqtSlot
from PyQt5.QtWidgets import QMessageBox
from UM import Util

from UM.Application import Application
from UM.Preferences import Preferences
from UM.Logger import Logger
from UM.Message import Message
from UM.Decorators import deprecated

from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.SettingFunction import SettingFunction
from UM.Signal import postponeSignals, CompressTechnique
import UM.FlameProfiler

from cura.QualityManager import QualityManager
from cura.PrinterOutputDevice import PrinterOutputDevice
from cura.Settings.ExtruderManager import ExtruderManager

from .CuraStackBuilder import CuraStackBuilder

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

from cura.Settings.ProfilesModel import ProfilesModel
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from UM.Settings.DefinitionContainer import DefinitionContainer
    from cura.Settings.CuraContainerStack import CuraContainerStack
    from cura.Settings.GlobalStack import GlobalStack


class MachineManager(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)

        self._active_container_stack = None     # type: CuraContainerStack
        self._global_container_stack = None     # type: GlobalStack

        self.machine_extruder_material_update_dict = collections.defaultdict(list)

        # Used to store the new containers until after confirming the dialog
        self._new_variant_container = None
        self._new_buildplate_container = None
        self._new_material_container = None
        self._new_quality_containers = []

        self._error_check_timer = QTimer()
        self._error_check_timer.setInterval(250)
        self._error_check_timer.setSingleShot(True)
        self._error_check_timer.timeout.connect(self._updateStacksHaveErrors)

        self._instance_container_timer = QTimer()
        self._instance_container_timer.setInterval(250)
        self._instance_container_timer.setSingleShot(True)
        self._instance_container_timer.timeout.connect(self.__emitChangedSignals)

        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerChanged)
        Application.getInstance().getContainerRegistry().containerLoadComplete.connect(self._onInstanceContainersChanged)
        self._connected_to_profiles_model = False

        ##  When the global container is changed, active material probably needs to be updated.
        self.globalContainerChanged.connect(self.activeMaterialChanged)
        self.globalContainerChanged.connect(self.activeVariantChanged)
        self.globalContainerChanged.connect(self.activeQualityChanged)

        self._stacks_have_errors = None

        self._empty_definition_changes_container = ContainerRegistry.getInstance().findContainers(id = "empty_definition_changes")[0]
        self._empty_variant_container = ContainerRegistry.getInstance().findContainers(id = "empty_variant")[0]
        self._empty_material_container = ContainerRegistry.getInstance().findContainers(id = "empty_material")[0]
        self._empty_quality_container = ContainerRegistry.getInstance().findContainers(id = "empty_quality")[0]
        self._empty_quality_changes_container = ContainerRegistry.getInstance().findContainers(id = "empty_quality_changes")[0]

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

        # when a user closed dialog check if any delayed material or variant changes need to be applied
        Application.getInstance().onDiscardOrKeepProfileChangesClosed.connect(self._executeDelayedActiveContainerStackChanges)

        Preferences.getInstance().addPreference("cura/active_machine", "")

        self._global_event_keys = set()

        active_machine_id = Preferences.getInstance().getValue("cura/active_machine")

        self._printer_output_devices = []
        Application.getInstance().getOutputDeviceManager().outputDevicesChanged.connect(self._onOutputDevicesChanged)
        # There might already be some output devices by the time the signal is connected
        self._onOutputDevicesChanged()

        if active_machine_id != "" and ContainerRegistry.getInstance().findContainerStacksMetadata(id = active_machine_id):
            # An active machine was saved, so restore it.
            self.setActiveMachine(active_machine_id)
            # Make sure _active_container_stack is properly initiated
            ExtruderManager.getInstance().setActiveExtruderIndex(0)

        self._auto_materials_changed = {}
        self._auto_hotends_changed = {}

        self._material_incompatible_message = Message(catalog.i18nc("@info:status",
                                                "The selected material is incompatible with the selected machine or configuration."),
                                                title = catalog.i18nc("@info:title", "Incompatible Material"))

        containers = ContainerRegistry.getInstance().findInstanceContainers(id = self.activeMaterialId)
        if containers:
            containers[0].nameChanged.connect(self._onMaterialNameChanged)

    globalContainerChanged = pyqtSignal()  # Emitted whenever the global stack is changed (ie: when changing between printers, changing a global profile, but not when changing a value)
    activeMaterialChanged = pyqtSignal()
    activeVariantChanged = pyqtSignal()
    activeQualityChanged = pyqtSignal()
    activeStackChanged = pyqtSignal()  # Emitted whenever the active stack is changed (ie: when changing between extruders, changing a profile, but not when changing a value)

    globalValueChanged = pyqtSignal()  # Emitted whenever a value inside global container is changed.
    activeStackValueChanged = pyqtSignal()  # Emitted whenever a value inside the active stack is changed.
    activeStackValidationChanged = pyqtSignal()  # Emitted whenever a validation inside active container is changed
    stacksValidationChanged = pyqtSignal()  # Emitted whenever a validation is changed

    blurSettings = pyqtSignal()  # Emitted to force fields in the advanced sidebar to un-focus, so they update properly

    outputDevicesChanged = pyqtSignal()

    def _onOutputDevicesChanged(self) -> None:
        for printer_output_device in self._printer_output_devices:
            printer_output_device.hotendIdChanged.disconnect(self._onHotendIdChanged)
            printer_output_device.materialIdChanged.disconnect(self._onMaterialIdChanged)

        self._printer_output_devices = []
        for printer_output_device in Application.getInstance().getOutputDeviceManager().getOutputDevices():
            if isinstance(printer_output_device, PrinterOutputDevice):
                self._printer_output_devices.append(printer_output_device)
                printer_output_device.hotendIdChanged.connect(self._onHotendIdChanged)
                printer_output_device.materialIdChanged.connect(self._onMaterialIdChanged)

        self.outputDevicesChanged.emit()

    @property
    def newVariant(self):
        return self._new_variant_container

    @property
    def newBuildplate(self):
        return self._new_buildplate_container

    @property
    def newMaterial(self):
        return self._new_material_container

    @pyqtProperty("QVariantList", notify = outputDevicesChanged)
    def printerOutputDevices(self):
        return self._printer_output_devices

    @pyqtProperty(int, constant=True)
    def totalNumberOfSettings(self) -> int:
        return len(ContainerRegistry.getInstance().findDefinitionContainers(id = "fdmprinter")[0].getAllKeys())

    def _onHotendIdChanged(self):
        if not self._global_container_stack or not self._printer_output_devices:
            return
        
        active_printer_model = self._printer_output_devices[0].activePrinter
        if not active_printer_model:
            return

        change_found = False
        machine_id = self.activeMachineId
        extruders = sorted(ExtruderManager.getInstance().getMachineExtruders(machine_id),
                           key=lambda k: k.getMetaDataEntry("position"))

        for extruder_model, extruder in zip(active_printer_model.extruders, extruders):
            containers = ContainerRegistry.getInstance().findInstanceContainersMetadata(type="variant",
                                                                                        definition=self._global_container_stack.definition.getId(),
                                                                                        name=extruder_model.hotendID)
            if containers:
                # The hotend ID is known.
                machine_id = self.activeMachineId
                if extruder.variant.getName() != extruder_model.hotendID:
                    change_found = True
                    self._auto_hotends_changed[extruder.getMetaDataEntry("position")] = containers[0]["id"]

        if change_found:
            # A change was found, let the output device handle this.
            self._printer_output_devices[0].materialHotendChangedMessage(self._materialHotendChangedCallback)

    def _onMaterialIdChanged(self):
        if not self._global_container_stack or not self._printer_output_devices:
            return

        active_printer_model = self._printer_output_devices[0].activePrinter
        if not active_printer_model:
            return

        change_found = False
        machine_id = self.activeMachineId
        extruders = sorted(ExtruderManager.getInstance().getMachineExtruders(machine_id),
                           key=lambda k: k.getMetaDataEntry("position"))

        for extruder_model, extruder in zip(active_printer_model.extruders, extruders):
            if extruder_model.activeMaterial is None:
                continue
            containers = ContainerRegistry.getInstance().findInstanceContainersMetadata(type="material",
                                                                                        definition=self._global_container_stack.definition.getId(),
                                                                                        GUID=extruder_model.activeMaterial.guid)
            if containers:
                # The material is known.
                if extruder.material.getMetaDataEntry("GUID") != extruder_model.activeMaterial.guid:
                    change_found = True
                    if self._global_container_stack.definition.getMetaDataEntry("has_variants") and extruder.variant:
                        variant_id = self.getQualityVariantId(self._global_container_stack.definition,
                                                              extruder.variant)
                        for container in containers:
                            if container.get("variant") == variant_id:
                                self._auto_materials_changed[extruder.getMetaDataEntry("position")] = container["id"]
                                break
                    else:
                        # Just use the first result we found.
                        self._auto_materials_changed[extruder.getMetaDataEntry("position")] = containers[0]["id"]
        if change_found:
            # A change was found, let the output device handle this.
            self._printer_output_devices[0].materialHotendChangedMessage(self._materialHotendChangedCallback)

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
        self._auto_materials_changed = {} #Processed all of them now.

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
        self._auto_hotends_changed = {}  # Processed all of them now.

    def _onGlobalContainerChanged(self):
        if self._global_container_stack:
            try:
                self._global_container_stack.nameChanged.disconnect(self._onMachineNameChanged)
            except TypeError:  # pyQtSignal gives a TypeError when disconnecting from something that was already disconnected.
                pass
            try:
                self._global_container_stack.containersChanged.disconnect(self._onInstanceContainersChanged)
            except TypeError:
                pass
            try:
                self._global_container_stack.propertyChanged.disconnect(self._onPropertyChanged)
            except TypeError:
                pass

            for extruder_stack in ExtruderManager.getInstance().getActiveExtruderStacks():
                extruder_stack.propertyChanged.disconnect(self._onPropertyChanged)
                extruder_stack.containersChanged.disconnect(self._onInstanceContainersChanged)

        # update the local global container stack reference
        self._global_container_stack = Application.getInstance().getGlobalContainerStack()

        self.globalContainerChanged.emit()

        # after switching the global stack we reconnect all the signals and set the variant and material references
        if self._global_container_stack:
            Preferences.getInstance().setValue("cura/active_machine", self._global_container_stack.getId())

            self._global_container_stack.nameChanged.connect(self._onMachineNameChanged)
            self._global_container_stack.containersChanged.connect(self._onInstanceContainersChanged)
            self._global_container_stack.propertyChanged.connect(self._onPropertyChanged)

            # Global stack can have only a variant if it is a buildplate
            global_variant = self._global_container_stack.variant
            if global_variant != self._empty_variant_container:
                if global_variant.getMetaDataEntry("hardware_type") != "buildplate":
                    self._global_container_stack.setVariant(self._empty_variant_container)

            # set the global material to empty as we now use the extruder stack at all times - CURA-4482
            global_material = self._global_container_stack.material
            if global_material != self._empty_material_container:
                self._global_container_stack.setMaterial(self._empty_material_container)

            # Listen for changes on all extruder stacks
            for extruder_stack in ExtruderManager.getInstance().getActiveExtruderStacks():
                extruder_stack.propertyChanged.connect(self._onPropertyChanged)
                extruder_stack.containersChanged.connect(self._onInstanceContainersChanged)

            if self._global_container_stack.getId() in self.machine_extruder_material_update_dict:
                for func in self.machine_extruder_material_update_dict[self._global_container_stack.getId()]:
                    Application.getInstance().callLater(func)
                del self.machine_extruder_material_update_dict[self._global_container_stack.getId()]

        self._error_check_timer.start()

    ##  Update self._stacks_valid according to _checkStacksForErrors and emit if change.
    def _updateStacksHaveErrors(self):
        old_stacks_have_errors = self._stacks_have_errors
        self._stacks_have_errors = self._checkStacksHaveErrors()
        if old_stacks_have_errors != self._stacks_have_errors:
            self.stacksValidationChanged.emit()
        Application.getInstance().stacksValidationFinished.emit()

    def _onActiveExtruderStackChanged(self):
        self.blurSettings.emit()  # Ensure no-one has focus.
        old_active_container_stack = self._active_container_stack

        self._active_container_stack = ExtruderManager.getInstance().getActiveExtruderStack()

        self._error_check_timer.start()

        if old_active_container_stack != self._active_container_stack:
            # Many methods and properties related to the active quality actually depend
            # on _active_container_stack. If it changes, then the properties change.
            self.activeQualityChanged.emit()

    def __emitChangedSignals(self):
        self.activeQualityChanged.emit()
        self.activeVariantChanged.emit()
        self.activeMaterialChanged.emit()
        self._updateStacksHaveErrors()  # Prevents unwanted re-slices after changing machine
        self._error_check_timer.start()

    def _onProfilesModelChanged(self, *args):
        self.__emitChangedSignals()

    def _onInstanceContainersChanged(self, container):
        # This should not trigger the ProfilesModel to be created, or there will be an infinite recursion
        if not self._connected_to_profiles_model and ProfilesModel.hasInstance():
            # This triggers updating the qualityModel in SidebarSimple whenever ProfilesModel is updated
            Logger.log("d", "Connecting profiles model...")
            ProfilesModel.getInstance().itemsChanged.connect(self._onProfilesModelChanged)
            self._connected_to_profiles_model = True

        self._instance_container_timer.start()

    def _onPropertyChanged(self, key: str, property_name: str):
        if property_name == "value":
            # Notify UI items, such as the "changed" star in profile pull down menu.
            self.activeStackValueChanged.emit()

        elif property_name == "validationState":
            self._error_check_timer.start()

    @pyqtSlot(str)
    def setActiveMachine(self, stack_id: str) -> None:
        self.blurSettings.emit()  # Ensure no-one has focus.
        self._cancelDelayedActiveContainerStackChanges()

        container_registry = ContainerRegistry.getInstance()

        containers = container_registry.findContainerStacks(id = stack_id)
        if containers:
            Application.getInstance().setGlobalContainerStack(containers[0])

        self.__emitChangedSignals()

    @pyqtSlot(str, str)
    def addMachine(self, name: str, definition_id: str) -> None:
        new_stack = CuraStackBuilder.createMachine(name, definition_id)
        if new_stack:
            # Instead of setting the global container stack here, we set the active machine and so the signals are emitted
            self.setActiveMachine(new_stack.getId())
        else:
            Logger.log("w", "Failed creating a new machine!")

    def _checkStacksHaveErrors(self) -> bool:
        time_start = time.time()
        if self._global_container_stack is None: #No active machine.
            return False

        if self._global_container_stack.hasErrors():
            Logger.log("d", "Checking global stack for errors took %0.2f s and we found and error" % (time.time() - time_start))
            return True

        # Not a very pretty solution, but the extruder manager doesn't really know how many extruders there are
        machine_extruder_count = self._global_container_stack.getProperty("machine_extruder_count", "value")
        extruder_stacks = ExtruderManager.getInstance().getMachineExtruders(self._global_container_stack.getId())
        count = 1  # we start with the global stack
        for stack in extruder_stacks:
            md = stack.getMetaData()
            if "position" in md and int(md["position"]) >= machine_extruder_count:
                continue
            count += 1
            if stack.hasErrors():
                Logger.log("d", "Checking %s stacks for errors took %.2f s and we found an error in stack [%s]" % (count, time.time() - time_start, str(stack)))
                return True

        Logger.log("d", "Checking %s stacks for errors took %.2f s" % (count, time.time() - time_start))
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
    def hasUserSettings(self) -> bool:
        if not self._global_container_stack:
            return False

        if self._global_container_stack.getTop().findInstances():
            return True

        stacks = list(ExtruderManager.getInstance().getMachineExtruders(self._global_container_stack.getId()))
        for stack in stacks:
            if stack.getTop().findInstances():
                return True

        return False

    @pyqtProperty(int, notify = activeStackValueChanged)
    def numUserSettings(self) -> int:
        if not self._global_container_stack:
            return 0
        num_user_settings = 0
        num_user_settings += len(self._global_container_stack.getTop().findInstances())
        stacks = list(ExtruderManager.getInstance().getMachineExtruders(self._global_container_stack.getId()))
        for stack in stacks:
            num_user_settings += len(stack.getTop().findInstances())
        return num_user_settings

    ##  Delete a user setting from the global stack and all extruder stacks.
    #   \param key \type{str} the name of the key to delete
    @pyqtSlot(str)
    def clearUserSettingAllCurrentStacks(self, key: str):
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

    ##  Check if none of the stacks contain error states
    #   Note that the _stacks_have_errors is cached due to performance issues
    #   Calling _checkStack(s)ForErrors on every change is simply too expensive
    @pyqtProperty(bool, notify = stacksValidationChanged)
    def stacksHaveErrors(self) -> bool:
        return bool(self._stacks_have_errors)

    @pyqtProperty(str, notify = activeStackChanged)
    def activeUserProfileId(self) -> str:
        if self._active_container_stack:
            return self._active_container_stack.getTop().getId()

        return ""

    @pyqtProperty(str, notify = globalContainerChanged)
    def activeMachineName(self) -> str:
        if self._global_container_stack:
            return self._global_container_stack.getName()

        return ""

    @pyqtProperty(str, notify = globalContainerChanged)
    def activeMachineId(self) -> str:
        if self._global_container_stack:
            return self._global_container_stack.getId()

        return ""

    @pyqtProperty(QObject, notify = globalContainerChanged)
    def activeMachine(self) -> Optional["GlobalStack"]:
        return self._global_container_stack

    @pyqtProperty(str, notify = activeStackChanged)
    def activeStackId(self) -> str:
        if self._active_container_stack:
            return self._active_container_stack.getId()

        return ""

    @pyqtProperty(str, notify = activeMaterialChanged)
    def activeMaterialName(self) -> str:
        if self._active_container_stack:
            material = self._active_container_stack.material
            if material:
                return material.getName()

        return ""

    @pyqtProperty("QVariantList", notify=activeVariantChanged)
    def activeVariantNames(self) -> List[str]:
        result = []

        active_stacks = ExtruderManager.getInstance().getActiveGlobalAndExtruderStacks()
        if active_stacks is not None:
            for stack in active_stacks:
                variant_container = stack.variant
                if variant_container and variant_container != self._empty_variant_container:
                    result.append(variant_container.getName())

        return result

    @pyqtProperty("QVariantList", notify = activeMaterialChanged)
    def activeMaterialNames(self) -> List[str]:
        result = []

        active_stacks = ExtruderManager.getInstance().getActiveGlobalAndExtruderStacks()
        if active_stacks is not None:
            for stack in active_stacks:
                material_container = stack.material
                if material_container and material_container != self._empty_material_container:
                    result.append(material_container.getName())
        return result

    @pyqtProperty(str, notify=activeMaterialChanged)
    def activeMaterialId(self) -> str:
        if self._active_container_stack:
            material = self._active_container_stack.material
            if material:
                return material.getId()

        return ""

    @pyqtProperty("QVariantMap", notify = activeVariantChanged)
    def allActiveVariantIds(self) -> Dict[str, str]:
        result = {}

        active_stacks = ExtruderManager.getInstance().getActiveExtruderStacks()
        if active_stacks is not None: #If we have a global stack.
            for stack in active_stacks:
                variant_container = stack.variant
                if not variant_container:
                    continue

                result[stack.getId()] = variant_container.getId()

        return result

    ##  Gets a dict with the active materials ids set in all extruder stacks and the global stack
    #   (when there is one extruder, the material is set in the global stack)
    #
    #   \return The material ids in all stacks
    @pyqtProperty("QVariantMap", notify = activeMaterialChanged)
    def allActiveMaterialIds(self) -> Dict[str, str]:
        result = {}

        active_stacks = ExtruderManager.getInstance().getActiveExtruderStacks()
        if active_stacks is not None:  # If we have extruder stacks
            for stack in active_stacks:
                material_container = stack.material
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
    def activeQualityLayerHeight(self) -> float:
        if not self._global_container_stack:
            return 0

        quality_changes = self._global_container_stack.qualityChanges
        if quality_changes:
            value = self._global_container_stack.getRawProperty("layer_height", "value", skip_until_container = quality_changes.getId())
            if isinstance(value, SettingFunction):
                value = value(self._global_container_stack)
            return value
        quality = self._global_container_stack.quality
        if quality:
            value = self._global_container_stack.getRawProperty("layer_height", "value", skip_until_container = quality.getId())
            if isinstance(value, SettingFunction):
                value = value(self._global_container_stack)
            return value

        return 0 # No quality profile.

    ##  Get the Material ID associated with the currently active material
    #   \returns MaterialID (string) if found, empty string otherwise
    @pyqtProperty(str, notify=activeQualityChanged)
    def activeQualityMaterialId(self) -> str:
        if self._active_container_stack:
            quality = self._active_container_stack.quality
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
    def activeQualityName(self) -> str:
        if self._active_container_stack and self._global_container_stack:
            quality = self._global_container_stack.qualityChanges
            if quality and not isinstance(quality, type(self._empty_quality_changes_container)):
                return quality.getName()
            quality = self._active_container_stack.quality
            if quality:
                return quality.getName()
        return ""

    @pyqtProperty(str, notify=activeQualityChanged)
    def activeQualityId(self) -> str:
        if self._active_container_stack:
            quality = self._active_container_stack.quality
            if isinstance(quality, type(self._empty_quality_container)):
                return ""
            quality_changes = self._active_container_stack.qualityChanges
            if quality and quality_changes:
                if isinstance(quality_changes, type(self._empty_quality_changes_container)):
                    # It's a built-in profile
                    return quality.getId()
                else:
                    # Custom profile
                    return quality_changes.getId()
        return ""

    @pyqtProperty(str, notify=activeQualityChanged)
    def globalQualityId(self) -> str:
        if self._global_container_stack:
            quality = self._global_container_stack.qualityChanges
            if quality and not isinstance(quality, type(self._empty_quality_changes_container)):
                return quality.getId()
            quality = self._global_container_stack.quality
            if quality:
                return quality.getId()
        return ""

    @pyqtProperty(str, notify=activeVariantChanged)
    def globalVariantId(self) -> str:
        if self._global_container_stack:
            variant = self._global_container_stack.variant
            if variant and not isinstance(variant, type(self._empty_variant_container)):
                return variant.getId()
        return ""

    @pyqtProperty(str, notify = activeQualityChanged)
    def activeQualityType(self) -> str:
        if self._active_container_stack:
            quality = self._active_container_stack.quality
            if quality:
                return quality.getMetaDataEntry("quality_type")
        return ""

    @pyqtProperty(bool, notify = activeQualityChanged)
    def isActiveQualitySupported(self) -> bool:
        if self._active_container_stack:
            quality = self._active_container_stack.quality
            if quality:
                return Util.parseBool(quality.getMetaDataEntry("supported", True))
        return False

    ##  Returns whether there is anything unsupported in the current set-up.
    #
    #   The current set-up signifies the global stack and all extruder stacks,
    #   so this indicates whether there is any container in any of the container
    #   stacks that is not marked as supported.
    @pyqtProperty(bool, notify = activeQualityChanged)
    def isCurrentSetupSupported(self) -> bool:
        if not self._global_container_stack:
            return False
        for stack in [self._global_container_stack] + list(self._global_container_stack.extruders.values()):
            for container in stack.getContainers():
                if not container:
                    return False
                if not Util.parseBool(container.getMetaDataEntry("supported", True)):
                    return False
        return True

    ##  Get the Quality ID associated with the currently active extruder
    #   Note that this only returns the "quality", not the "quality_changes"
    #   \returns QualityID (string) if found, empty string otherwise
    #   \sa activeQualityId()
    #   \todo Ideally, this method would be named activeQualityId(), and the other one
    #         would be named something like activeQualityOrQualityChanges() for consistency
    @pyqtProperty(str, notify = activeQualityChanged)
    def activeQualityContainerId(self) -> str:
        # We're using the active stack instead of the global stack in case the list of qualities differs per extruder
        if self._global_container_stack:
            quality = self._active_container_stack.quality
            if quality:
                return quality.getId()
        return ""

    @pyqtProperty(str, notify = activeQualityChanged)
    def activeQualityChangesId(self) -> str:
        if self._active_container_stack:
            quality_changes = self._active_container_stack.qualityChanges
            if quality_changes and not isinstance(quality_changes, type(self._empty_quality_changes_container)):
                return quality_changes.getId()
        return ""

    ## Check if a container is read_only
    @pyqtSlot(str, result = bool)
    def isReadOnly(self, container_id: str) -> bool:
        return ContainerRegistry.getInstance().isReadOnly(container_id)

    ## Copy the value of the setting of the current extruder to all other extruders as well as the global container.
    @pyqtSlot(str)
    def copyValueToExtruders(self, key: str):
        new_value = self._active_container_stack.getProperty(key, "value")
        extruder_stacks = [stack for stack in ExtruderManager.getInstance().getMachineExtruders(self._global_container_stack.getId())]

        # check in which stack the value has to be replaced
        for extruder_stack in extruder_stacks:
            if extruder_stack != self._active_container_stack and extruder_stack.getProperty(key, "value") != new_value:
                extruder_stack.userChanges.setProperty(key, "value", new_value)  # TODO: nested property access, should be improved

    ## Set the active material by switching out a container
    #  Depending on from/to material+current variant, a quality profile is chosen and set.
    @pyqtSlot(str)
    def setActiveMaterial(self, material_id: str, always_discard_changes = False):
        with postponeSignals(*self._getContainerChangedSignals(), compress = CompressTechnique.CompressPerParameterValue):
            containers = ContainerRegistry.getInstance().findInstanceContainers(id = material_id)
            if not containers or not self._active_container_stack:
                return
            material_container = containers[0]

            Logger.log("d", "Attempting to change the active material to %s", material_id)

            old_material = self._active_container_stack.material
            old_quality = self._active_container_stack.quality
            old_quality_type = None
            if old_quality and old_quality.getId() != self._empty_quality_container.getId():
                old_quality_type = old_quality.getMetaDataEntry("quality_type")
            old_quality_changes = self._active_container_stack.qualityChanges
            if not old_material:
                Logger.log("w", "While trying to set the active material, no material was found to replace it.")
                return

            if old_quality_changes and isinstance(old_quality_changes, type(self._empty_quality_changes_container)):
                old_quality_changes = None

            self.blurSettings.emit()
            old_material.nameChanged.disconnect(self._onMaterialNameChanged)

            self._new_material_container = material_container   # self._active_container_stack will be updated with a delay
            Logger.log("d", "Active material changed")

            material_container.nameChanged.connect(self._onMaterialNameChanged)

            if material_container.getMetaDataEntry("compatible") == False:
                self._material_incompatible_message.show()
            else:
                self._material_incompatible_message.hide()

            quality_type = None
            new_quality_id = None
            if old_quality:
                new_quality_id = old_quality.getId()
                quality_type = old_quality.getMetaDataEntry("quality_type")
            if old_quality_changes:
                quality_type = old_quality_changes.getMetaDataEntry("quality_type")
                new_quality_id = old_quality_changes.getId()

            global_stack = Application.getInstance().getGlobalContainerStack()
            if global_stack:
                quality_manager = QualityManager.getInstance()

                candidate_quality = None
                if quality_type:
                    candidate_quality = quality_manager.findQualityByQualityType(quality_type,
                                            quality_manager.getWholeMachineDefinition(global_stack.definition),
                                            [material_container.getMetaData()])

                if not candidate_quality or candidate_quality.getId() == self._empty_quality_changes_container:
                    Logger.log("d", "Attempting to find fallback quality")
                    # Fall back to a quality (which must be compatible with all other extruders)
                    new_qualities = quality_manager.findAllUsableQualitiesForMachineAndExtruders(
                        self._global_container_stack, ExtruderManager.getInstance().getExtruderStacks())

                    quality_types = sorted([q.getMetaDataEntry("quality_type") for q in new_qualities], reverse = True)
                    quality_type_to_use = None
                    if quality_types:
                        # try to use the same quality as before, otherwise the first one in the quality_types
                        quality_type_to_use = quality_types[0]
                        if old_quality_type is not None and old_quality_type in quality_type_to_use:
                            quality_type_to_use = old_quality_type

                    new_quality = None
                    for q in new_qualities:
                        if quality_type_to_use is not None and q.getMetaDataEntry("quality_type") == quality_type_to_use:
                            new_quality = q
                            break

                    if new_quality is not None:
                        new_quality_id = new_quality.getId()  # Just pick the first available one
                    else:
                        Logger.log("w", "No quality profile found that matches the current machine and extruders.")
                else:
                    if not old_quality_changes:
                        new_quality_id = candidate_quality.getId()

                self.setActiveQuality(new_quality_id, always_discard_changes = always_discard_changes)

    @pyqtSlot(str)
    def setActiveVariant(self, variant_id: str, always_discard_changes = False):
        with postponeSignals(*self._getContainerChangedSignals(), compress = CompressTechnique.CompressPerParameterValue):
            containers = ContainerRegistry.getInstance().findInstanceContainers(id = variant_id)
            if not containers or not self._active_container_stack:
                return
            Logger.log("d", "Attempting to change the active variant to %s", variant_id)
            old_variant = self._active_container_stack.variant
            old_material = self._active_container_stack.material
            if old_variant:
                self.blurSettings.emit()
                self._new_variant_container = containers[0]  # self._active_container_stack will be updated with a delay
                Logger.log("d", "Active variant changed to {active_variant_id}".format(active_variant_id = containers[0].getId()))
                preferred_material_name = None
                if old_material:
                    preferred_material_name = old_material.getName()
                preferred_material_id = self._updateMaterialContainer(self._global_container_stack.definition, self._global_container_stack, containers[0], preferred_material_name).id
                self.setActiveMaterial(preferred_material_id, always_discard_changes = always_discard_changes)
            else:
                Logger.log("w", "While trying to set the active variant, no variant was found to replace.")

    @pyqtSlot(str)
    def setActiveVariantBuildplate(self, variant_buildplate_id: str):
        with postponeSignals(*self._getContainerChangedSignals(), compress = CompressTechnique.CompressPerParameterValue):
            containers = ContainerRegistry.getInstance().findInstanceContainers(id = variant_buildplate_id)
            if not containers or not self._global_container_stack:
                return
            Logger.log("d", "Attempting to change the active buildplate to %s", variant_buildplate_id)
            old_buildplate = self._global_container_stack.variant
            if old_buildplate:
                self.blurSettings.emit()
                self._new_buildplate_container = containers[0]  # self._active_container_stack will be updated with a delay
                Logger.log("d", "Active buildplate changed to {active_variant_buildplate_id}".format(active_variant_buildplate_id = containers[0].getId()))

                # Force set the active quality as it is so the values are updated
                self.setActiveMaterial(self._active_container_stack.material.getId())
            else:
                Logger.log("w", "While trying to set the active buildplate, no buildplate was found to replace.")

    ##  set the active quality
    #   \param quality_id The quality_id of either a quality or a quality_changes
    @pyqtSlot(str)
    def setActiveQuality(self, quality_id: str, always_discard_changes = False):
        with postponeSignals(*self._getContainerChangedSignals(), compress = CompressTechnique.CompressPerParameterValue):
            self.blurSettings.emit()

            Logger.log("d", "Attempting to change the active quality to %s", quality_id)

            containers = ContainerRegistry.getInstance().findInstanceContainersMetadata(id = quality_id)
            if not containers or not self._global_container_stack:
                return

            # Quality profile come in two flavours: type=quality and type=quality_changes
            # If we found a quality_changes profile then look up its parent quality profile.
            container_type = containers[0].get("type")
            quality_name = containers[0]["name"]
            quality_type = containers[0].get("quality_type")

            # Get quality container and optionally the quality_changes container.
            if container_type == "quality":
                new_quality_settings_list = self.determineQualityAndQualityChangesForQualityType(quality_type)
            elif container_type == "quality_changes":
                new_quality_settings_list = self._determineQualityAndQualityChangesForQualityChanges(quality_name)
            else:
                Logger.log("e", "Tried to set quality to a container that is not of the right type: {container_id}".format(container_id = containers[0]["id"]))
                return

            # Check if it was at all possible to find new settings
            if new_quality_settings_list is None:
                return

            # check if any of the stacks have a not supported profile
            # if that is the case, all stacks should have a not supported state (otherwise it will show quality_type normal)
            has_not_supported_quality = False

            # check all stacks for not supported
            for setting_info in new_quality_settings_list:
                if setting_info["quality"].getMetaDataEntry("quality_type") == "not_supported":
                    has_not_supported_quality = True
                    break

            # set all stacks to not supported if that's the case
            if has_not_supported_quality:
                for setting_info in new_quality_settings_list:
                    setting_info["quality"] = self._empty_quality_container

            self._new_quality_containers.clear()

            # store the upcoming quality profile changes per stack for later execution
            # this prevents re-slicing before the user has made a choice in the discard or keep dialog
            # (see _executeDelayedActiveContainerStackChanges)
            for setting_info in new_quality_settings_list:
                stack = setting_info["stack"]
                stack_quality = setting_info["quality"]
                stack_quality_changes = setting_info["quality_changes"]

                self._new_quality_containers.append({
                    "stack": stack,
                    "quality": stack_quality,
                    "quality_changes": stack_quality_changes
                })

            Logger.log("d", "Active quality changed")

            # show the keep/discard dialog after the containers have been switched. Otherwise, the default values on
            # the dialog will be the those before the switching.
            self._executeDelayedActiveContainerStackChanges()

            if self.hasUserSettings and Preferences.getInstance().getValue("cura/active_mode") == 1 and not always_discard_changes:
                Application.getInstance().discardOrKeepProfileChanges()

    ##  Used to update material and variant in the active container stack with a delay.
    #   This delay prevents the stack from triggering a lot of signals (eventually resulting in slicing)
    #   before the user decided to keep or discard any of their changes using the dialog.
    #   The Application.onDiscardOrKeepProfileChangesClosed signal triggers this method.
    def _executeDelayedActiveContainerStackChanges(self):

        Logger.log("d", "Applying configuration changes...")

        if self._new_variant_container is not None:
            self._active_container_stack.variant = self._new_variant_container
            self._new_variant_container = None

        if self._new_buildplate_container is not None:
            self._global_container_stack.variant = self._new_buildplate_container
            self._new_buildplate_container = None

        if self._new_material_container is not None:
            self._active_container_stack.material = self._new_material_container
            self._new_material_container = None

        # apply the new quality to all stacks
        if self._new_quality_containers:
            for new_quality in self._new_quality_containers:
                self._replaceQualityOrQualityChangesInStack(new_quality["stack"], new_quality["quality"], postpone_emit = True)
                self._replaceQualityOrQualityChangesInStack(new_quality["stack"], new_quality["quality_changes"], postpone_emit = True)

            for new_quality in self._new_quality_containers:
                new_quality["stack"].nameChanged.connect(self._onQualityNameChanged)
                new_quality["stack"].sendPostponedEmits() # Send the signals that were postponed in _replaceQualityOrQualityChangesInStack

            self._new_quality_containers.clear()

        Logger.log("d", "New configuration applied")

    ##  Cancel set changes for material and variant in the active container stack.
    #   Used for ignoring any changes when switching between printers (setActiveMachine)
    def _cancelDelayedActiveContainerStackChanges(self):
        self._new_material_container = None
        self._new_buildplate_container = None
        self._new_variant_container = None

    ##  Determine the quality and quality changes settings for the current machine for a quality name.
    #
    #   \param quality_name \type{str} the name of the quality.
    #   \return \type{List[Dict]} with keys "stack", "quality" and "quality_changes".
    @UM.FlameProfiler.profile
    def determineQualityAndQualityChangesForQualityType(self, quality_type: str) -> List[Dict[str, Union["CuraContainerStack", InstanceContainer]]]:
        quality_manager = QualityManager.getInstance()
        result = []
        empty_quality_changes = self._empty_quality_changes_container
        global_container_stack = self._global_container_stack
        if not global_container_stack:
            return []

        global_machine_definition = quality_manager.getParentMachineDefinition(global_container_stack.definition)
        extruder_stacks = ExtruderManager.getInstance().getActiveExtruderStacks()

        # find qualities for extruders
        for extruder_stack in extruder_stacks:
            material_metadata = extruder_stack.material.getMetaData()

            # TODO: fix this
            if self._new_material_container and extruder_stack.getId() == self._active_container_stack.getId():
                material_metadata = self._new_material_container.getMetaData()

            quality = quality_manager.findQualityByQualityType(quality_type, global_machine_definition, [material_metadata])

            if not quality:
                # No quality profile is found for this quality type.
                quality = self._empty_quality_container

            result.append({
                "stack": extruder_stack,
                "quality": quality,
                "quality_changes": empty_quality_changes
            })

        # also find a global quality for the machine
        global_quality = quality_manager.findQualityByQualityType(quality_type, global_machine_definition, [], global_quality = "True")

        # if there is not global quality but we're using a single extrusion machine, copy the quality of the first extruder - CURA-4482
        if not global_quality and len(extruder_stacks) == 1:
            global_quality = result[0]["quality"]

        # if there is still no global quality, set it to empty (not supported)
        if not global_quality:
            global_quality = self._empty_quality_container

        result.append({
            "stack": global_container_stack,
            "quality": global_quality,
            "quality_changes": empty_quality_changes
        })

        return result

    ##  Determine the quality and quality changes settings for the current machine for a quality changes name.
    #
    #   \param quality_changes_name \type{str} the name of the quality changes.
    #   \return \type{List[Dict]} with keys "stack", "quality" and "quality_changes".
    def _determineQualityAndQualityChangesForQualityChanges(self, quality_changes_name: str) -> Optional[List[Dict[str, Union["CuraContainerStack", InstanceContainer]]]]:
        result = []
        quality_manager = QualityManager.getInstance()

        global_container_stack = self._global_container_stack
        global_machine_definition = quality_manager.getParentMachineDefinition(global_container_stack.definition)
        quality_changes_profiles = quality_manager.findQualityChangesByName(quality_changes_name, global_machine_definition)

        global_quality_changes = [qcp for qcp in quality_changes_profiles if qcp.getMetaDataEntry("extruder") is None]
        if global_quality_changes:
            global_quality_changes = global_quality_changes[0]
        else:
            Logger.log("e", "Could not find the global quality changes container with name %s", quality_changes_name)
            return None

        # For the global stack, find a quality which matches the quality_type in
        # the quality changes profile and also satisfies any material constraints.
        quality_type = global_quality_changes.getMetaDataEntry("quality_type")

        extruder_stacks = ExtruderManager.getInstance().getActiveExtruderStacks()

        # append the extruder quality changes
        for extruder_stack in extruder_stacks:
            extruder_definition = quality_manager.getParentMachineDefinition(extruder_stack.definition)

            quality_changes_list = [qcp for qcp in quality_changes_profiles if qcp.getMetaDataEntry("extruder") == extruder_definition.getId()]

            if quality_changes_list:
                quality_changes = quality_changes_list[0]
            else:
                quality_changes = global_quality_changes
            if not quality_changes:
                quality_changes = self._empty_quality_changes_container

            material_metadata = extruder_stack.material.getMetaData()

            if self._new_material_container and self._active_container_stack.getId() == extruder_stack.getId():
                material_metadata = self._new_material_container.getMetaData()

            quality = quality_manager.findQualityByQualityType(quality_type, global_machine_definition, [material_metadata])

            if not quality:
                # No quality profile found for this quality type.
                quality = self._empty_quality_container

            result.append({
                "stack": extruder_stack,
                "quality": quality,
                "quality_changes": quality_changes
            })

        # append the global quality changes
        global_quality = quality_manager.findQualityByQualityType(quality_type, global_machine_definition, global_quality = "True")

        # if there is not global quality but we're using a single extrusion machine, copy the quality of the first extruder - CURA-4482
        if not global_quality and len(extruder_stacks) == 1:
            global_quality = result[0]["quality"]

        # if still no global quality changes are found we set it to empty (not supported)
        if not global_quality:
            global_quality = self._empty_quality_container

        result.append({
            "stack": global_container_stack,
            "quality": global_quality,
            "quality_changes": global_quality_changes
        })

        return result

    def _replaceQualityOrQualityChangesInStack(self, stack: "CuraContainerStack", container: "InstanceContainer", postpone_emit = False):
        # Disconnect the signal handling from the old container.
        container_type = container.getMetaDataEntry("type")
        if container_type == "quality":
            stack.quality.nameChanged.disconnect(self._onQualityNameChanged)
            stack.setQuality(container, postpone_emit = postpone_emit)
            stack.quality.nameChanged.connect(self._onQualityNameChanged)
        elif container_type == "quality_changes" or container_type is None:
            # If the container is an empty container, we need to change the quality_changes.
            # Quality can never be set to empty.
            stack.qualityChanges.nameChanged.disconnect(self._onQualityNameChanged)
            stack.setQualityChanges(container, postpone_emit = postpone_emit)
            stack.qualityChanges.nameChanged.connect(self._onQualityNameChanged)
        self._onQualityNameChanged()

    @pyqtProperty(str, notify = activeVariantChanged)
    def activeVariantName(self) -> str:
        if self._active_container_stack:
            variant = self._active_container_stack.variant
            if variant:
                return variant.getName()

        return ""

    @pyqtProperty(str, notify = activeVariantChanged)
    def activeVariantId(self) -> str:
        if self._active_container_stack:
            variant = self._active_container_stack.variant
            if variant:
                return variant.getId()

        return ""

    @pyqtProperty(str, notify = activeVariantChanged)
    def activeVariantBuildplateName(self) -> str:
        if self._global_container_stack:
            variant = self._global_container_stack.variant
            if variant:
                return variant.getName()

        return ""

    @pyqtProperty(str, notify = globalContainerChanged)
    def activeDefinitionId(self) -> str:
        if self._global_container_stack:
            return self._global_container_stack.definition.id

        return ""

    @pyqtProperty(str, notify=globalContainerChanged)
    def activeDefinitionName(self) -> str:
        if self._global_container_stack:
            return self._global_container_stack.definition.getName()

        return ""

    ##  Get the Definition ID to use to select quality profiles for the currently active machine
    #   \returns DefinitionID (string) if found, empty string otherwise
    #   \sa getQualityDefinitionId
    @pyqtProperty(str, notify = globalContainerChanged)
    def activeQualityDefinitionId(self) -> str:
        if self._global_container_stack:
            return self.getQualityDefinitionId(self._global_container_stack.definition)
        return ""

    ##  Get the Definition ID to use to select quality profiles for machines of the specified definition
    #   This is normally the id of the definition itself, but machines can specify a different definition to inherit qualities from
    #   \param definition (DefinitionContainer) machine definition
    #   \returns DefinitionID (string) if found, empty string otherwise
    def getQualityDefinitionId(self, definition: "DefinitionContainer") -> str:
        return QualityManager.getInstance().getParentMachineDefinition(definition).getId()

    ##  Get the Variant ID to use to select quality profiles for the currently active variant
    #   \returns VariantID (string) if found, empty string otherwise
    #   \sa getQualityVariantId
    @pyqtProperty(str, notify = activeVariantChanged)
    def activeQualityVariantId(self) -> str:
        if self._active_container_stack:
            variant = self._active_container_stack.variant
            if variant:
                return self.getQualityVariantId(self._global_container_stack.definition, variant)
        return ""

    ##  Get the Variant ID to use to select quality profiles for variants of the specified definitions
    #   This is normally the id of the variant itself, but machines can specify a different definition
    #   to inherit qualities from, which has consequences for the variant to use as well
    #   \param definition (DefinitionContainer) machine definition
    #   \param variant (InstanceContainer) variant definition
    #   \returns VariantID (string) if found, empty string otherwise
    def getQualityVariantId(self, definition: "DefinitionContainer", variant: "InstanceContainer") -> str:
        variant_id = variant.getId()
        definition_id = definition.getId()
        quality_definition_id = self.getQualityDefinitionId(definition)

        if definition_id != quality_definition_id:
            variant_id = variant_id.replace(definition_id, quality_definition_id, 1)
        return variant_id

    ##  Gets how the active definition calls variants
    #   Caveat: per-definition-variant-title is currently not translated (though the fallback is)
    @pyqtProperty(str, notify = globalContainerChanged)
    def activeDefinitionVariantsName(self) -> str:
        fallback_title = catalog.i18nc("@label", "Nozzle")
        if self._global_container_stack:
            return self._global_container_stack.definition.getMetaDataEntry("variants_name", fallback_title)

        return fallback_title

    @pyqtSlot(str, str)
    def renameMachine(self, machine_id: str, new_name: str):
        container_registry = ContainerRegistry.getInstance()
        machine_stack = container_registry.findContainerStacks(id = machine_id)
        if machine_stack:
            new_name = container_registry.createUniqueName("machine", machine_stack[0].getName(), new_name, machine_stack[0].definition.getName())
            machine_stack[0].setName(new_name)
            self.globalContainerChanged.emit()

    @pyqtSlot(str)
    def removeMachine(self, machine_id: str):
        # If the machine that is being removed is the currently active machine, set another machine as the active machine.
        activate_new_machine = (self._global_container_stack and self._global_container_stack.getId() == machine_id)

        # activate a new machine before removing a machine because this is safer
        if activate_new_machine:
            machine_stacks = ContainerRegistry.getInstance().findContainerStacksMetadata(type = "machine")
            other_machine_stacks = [s for s in machine_stacks if s["id"] != machine_id]
            if other_machine_stacks:
                self.setActiveMachine(other_machine_stacks[0]["id"])

        ExtruderManager.getInstance().removeMachineExtruders(machine_id)
        containers = ContainerRegistry.getInstance().findInstanceContainersMetadata(type = "user", machine = machine_id)
        for container in containers:
            ContainerRegistry.getInstance().removeContainer(container["id"])
        ContainerRegistry.getInstance().removeContainer(machine_id)

    @pyqtProperty(bool, notify = globalContainerChanged)
    def hasMaterials(self) -> bool:
        if self._global_container_stack:
            return Util.parseBool(self._global_container_stack.getMetaDataEntry("has_materials", False))
        return False

    @pyqtProperty(bool, notify = globalContainerChanged)
    def hasVariants(self) -> bool:
        if self._global_container_stack:
            return Util.parseBool(self._global_container_stack.getMetaDataEntry("has_variants", False))
        return False

    @pyqtProperty(bool, notify = globalContainerChanged)
    def hasVariantBuildplates(self) -> bool:
        if self._global_container_stack:
            return Util.parseBool(self._global_container_stack.getMetaDataEntry("has_variant_buildplates", False))
        return False

    ##  The selected buildplate is compatible if it is compatible with all the materials in all the extruders
    @pyqtProperty(bool, notify = activeMaterialChanged)
    def variantBuildplateCompatible(self) -> bool:
        if not self._global_container_stack:
            return True

        buildplate_compatible = True  # It is compatible by default
        extruder_stacks = self._global_container_stack.extruders.values()
        for stack in extruder_stacks:
            material_container = stack.material
            if material_container == self._empty_material_container:
                continue
            if material_container.getMetaDataEntry("buildplate_compatible"):
                buildplate_compatible = buildplate_compatible and material_container.getMetaDataEntry("buildplate_compatible")[self.activeVariantBuildplateName]

        return buildplate_compatible

    ##  The selected buildplate is usable if it is usable for all materials OR it is compatible for one but not compatible
    #   for the other material but the buildplate is still usable
    @pyqtProperty(bool, notify = activeMaterialChanged)
    def variantBuildplateUsable(self) -> bool:
        if not self._global_container_stack:
            return True

        # Here the next formula is being calculated:
        # result = (not (material_left_compatible and material_right_compatible)) and
        #           (material_left_compatible or material_left_usable) and
        #           (material_right_compatible or material_right_usable)
        result = not self.variantBuildplateCompatible
        extruder_stacks = self._global_container_stack.extruders.values()
        for stack in extruder_stacks:
            material_container = stack.material
            if material_container == self._empty_material_container:
                continue
            buildplate_compatible = material_container.getMetaDataEntry("buildplate_compatible")[self.activeVariantBuildplateName] if material_container.getMetaDataEntry("buildplate_compatible") else True
            buildplate_usable = material_container.getMetaDataEntry("buildplate_recommended")[self.activeVariantBuildplateName] if material_container.getMetaDataEntry("buildplate_recommended") else True

            result = result and (buildplate_compatible or buildplate_usable)

        return result

    ##  Property to indicate if a machine has "specialized" material profiles.
    #   Some machines have their own material profiles that "override" the default catch all profiles.
    @pyqtProperty(bool, notify = globalContainerChanged)
    def filterMaterialsByMachine(self) -> bool:
        if self._global_container_stack:
            return Util.parseBool(self._global_container_stack.getMetaDataEntry("has_machine_materials", False))
        return False

    ##  Property to indicate if a machine has "specialized" quality profiles.
    #   Some machines have their own quality profiles that "override" the default catch all profiles.
    @pyqtProperty(bool, notify = globalContainerChanged)
    def filterQualityByMachine(self) -> bool:
        if self._global_container_stack:
            return Util.parseBool(self._global_container_stack.getMetaDataEntry("has_machine_quality", False))
        return False

    ##  Get the Definition ID of a machine (specified by ID)
    #   \param machine_id string machine id to get the definition ID of
    #   \returns DefinitionID (string) if found, None otherwise
    @pyqtSlot(str, result = str)
    def getDefinitionByMachineId(self, machine_id: str) -> str:
        containers = ContainerRegistry.getInstance().findContainerStacks(id = machine_id)
        if containers:
            return containers[0].definition.getId()

    ##  Set the amount of extruders on the active machine (global stack)
    #   \param extruder_count int the number of extruders to set
    def setActiveMachineExtruderCount(self, extruder_count):
        extruder_manager = Application.getInstance().getExtruderManager()

        definition_changes_container = self._global_container_stack.definitionChanges
        if not self._global_container_stack or definition_changes_container == self._empty_definition_changes_container:
            return

        previous_extruder_count = self._global_container_stack.getProperty("machine_extruder_count", "value")
        if extruder_count == previous_extruder_count:
            return

        # reset all extruder number settings whose value is no longer valid
        for setting_instance in self._global_container_stack.userChanges.findInstances():
            setting_key = setting_instance.definition.key
            if not self._global_container_stack.getProperty(setting_key, "type") in ("extruder", "optional_extruder"):
                continue

            old_value = int(self._global_container_stack.userChanges.getProperty(setting_key, "value"))
            if old_value >= extruder_count:
                self._global_container_stack.userChanges.removeInstance(setting_key)
                Logger.log("d", "Reset [%s] because its old value [%s] is no longer valid ", setting_key, old_value)

        # Check to see if any objects are set to print with an extruder that will no longer exist
        root_node = Application.getInstance().getController().getScene().getRoot()
        for node in DepthFirstIterator(root_node):
            if node.getMeshData():
                extruder_nr = node.callDecoration("getActiveExtruderPosition")

                if extruder_nr is not None and int(extruder_nr) > extruder_count - 1:
                    node.callDecoration("setActiveExtruder", extruder_manager.getExtruderStack(extruder_count - 1).getId())

        definition_changes_container.setProperty("machine_extruder_count", "value", extruder_count)

        # Make sure one of the extruder stacks is active
        extruder_manager.setActiveExtruderIndex(0)

        # Move settable_per_extruder values out of the global container
        # After CURA-4482 this should not be the case anymore, but we still want to support older project files.
        global_user_container = self._global_container_stack.getTop()

        # Make sure extruder_stacks exists
        extruder_stacks = []

        if previous_extruder_count == 1:
            extruder_stacks = ExtruderManager.getInstance().getActiveExtruderStacks()
            global_user_container = self._global_container_stack.getTop()

        for setting_instance in global_user_container.findInstances():
            setting_key = setting_instance.definition.key
            settable_per_extruder = self._global_container_stack.getProperty(setting_key, "settable_per_extruder")

            if settable_per_extruder:
                limit_to_extruder = int(self._global_container_stack.getProperty(setting_key, "limit_to_extruder"))
                extruder_stack = extruder_stacks[max(0, limit_to_extruder)]
                extruder_stack.getTop().setProperty(setting_key, "value", global_user_container.getProperty(setting_key, "value"))
                global_user_container.removeInstance(setting_key)

        # Signal that the global stack has changed
        Application.getInstance().globalContainerStackChanged.emit()

    @staticmethod
    def createMachineManager():
        return MachineManager()

    @deprecated("Use ExtruderStack.material = ... and it won't be necessary", "2.7")
    def _updateMaterialContainer(self, definition: "DefinitionContainer", stack: "ContainerStack", variant_container: Optional["InstanceContainer"] = None, preferred_material_name: Optional[str] = None) -> InstanceContainer:
        if not definition.getMetaDataEntry("has_materials"):
            return self._empty_material_container

        approximate_material_diameter = str(round(stack.getProperty("material_diameter", "value")))
        search_criteria = { "type": "material", "approximate_diameter": approximate_material_diameter }

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

        containers = ContainerRegistry.getInstance().findInstanceContainers(**search_criteria)
        if containers:
            return containers[0]

        if "variant" in search_criteria or "id" in search_criteria:
            # If a material by this name can not be found, try a wider set of search criteria
            search_criteria.pop("variant", None)
            search_criteria.pop("id", None)

            containers = ContainerRegistry.getInstance().findInstanceContainers(**search_criteria)
            if containers:
                return containers[0]
        Logger.log("w", "Unable to find a material container with provided criteria, returning an empty one instead.")
        return self._empty_material_container

    def _onMachineNameChanged(self):
        self.globalContainerChanged.emit()

    def _onMaterialNameChanged(self):
        self.activeMaterialChanged.emit()

    def _onQualityNameChanged(self):
        self.activeQualityChanged.emit()

    def _getContainerChangedSignals(self) -> List[Signal]:
        stacks = ExtruderManager.getInstance().getActiveExtruderStacks()
        stacks.append(self._global_container_stack)
        return [ s.containersChanged for s in stacks ]
