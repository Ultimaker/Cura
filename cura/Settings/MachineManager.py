# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import time
import re
import unicodedata
from typing import Any, List, Dict, TYPE_CHECKING, Optional, cast, Set

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, QTimer

from UM.ConfigurationErrorMessage import ConfigurationErrorMessage
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.Interfaces import ContainerInterface
from UM.Signal import Signal
from UM.FlameProfiler import pyqtSlot
from UM import Util
from UM.Logger import Logger
from UM.Message import Message

from UM.Settings.SettingFunction import SettingFunction
from UM.Signal import postponeSignals, CompressTechnique

import cura.CuraApplication  # Imported like this to prevent circular references.
from UM.Util import parseBool

from cura.Machines.ContainerNode import ContainerNode
from cura.Machines.ContainerTree import ContainerTree
from cura.Machines.Models.IntentCategoryModel import IntentCategoryModel

from cura.PrinterOutput.PrinterOutputDevice import PrinterOutputDevice, ConnectionType
from cura.PrinterOutput.Models.PrinterConfigurationModel import PrinterConfigurationModel
from cura.PrinterOutput.Models.ExtruderConfigurationModel import ExtruderConfigurationModel
from cura.PrinterOutput.Models.MaterialOutputModel import MaterialOutputModel
from cura.Settings.CuraContainerRegistry import CuraContainerRegistry
from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.ExtruderStack import ExtruderStack
from cura.Settings.cura_empty_instance_containers import (empty_definition_changes_container, empty_variant_container,
                                                          empty_material_container, empty_quality_container,
                                                          empty_quality_changes_container, empty_intent_container)
from cura.UltimakerCloud.UltimakerCloudConstants import META_UM_LINKED_TO_ACCOUNT

from .CuraStackBuilder import CuraStackBuilder

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")
from cura.Settings.GlobalStack import GlobalStack
if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication
    from cura.Machines.MaterialNode import MaterialNode
    from cura.Machines.QualityChangesGroup import QualityChangesGroup
    from cura.Machines.QualityGroup import QualityGroup
    from cura.Machines.VariantNode import VariantNode


class MachineManager(QObject):
    def __init__(self, application: "CuraApplication", parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)

        self._active_container_stack = None     # type: Optional[ExtruderStack]
        self._global_container_stack = None     # type: Optional[GlobalStack]

        self._current_root_material_id = {}  # type: Dict[str, str]

        self._default_extruder_position = "0"  # to be updated when extruders are switched on and off

        self._instance_container_timer = QTimer()  # type: QTimer
        self._instance_container_timer.setInterval(250)
        self._instance_container_timer.setSingleShot(True)
        self._instance_container_timer.timeout.connect(self.__emitChangedSignals)

        self._application = application
        self._container_registry = self._application.getContainerRegistry()
        self._application.globalContainerStackChanged.connect(self._onGlobalContainerChanged)
        self._container_registry.containerLoadComplete.connect(self._onContainersChanged)

        #  When the global container is changed, active material probably needs to be updated.
        self.globalContainerChanged.connect(self.activeMaterialChanged)
        self.globalContainerChanged.connect(self.activeVariantChanged)
        self.globalContainerChanged.connect(self.activeQualityChanged)

        self.globalContainerChanged.connect(self.activeQualityChangesGroupChanged)
        self.globalContainerChanged.connect(self.activeQualityGroupChanged)

        self._stacks_have_errors = None  # type: Optional[bool]

        extruder_manager = self._application.getExtruderManager()

        extruder_manager.activeExtruderChanged.connect(self._onActiveExtruderStackChanged)
        extruder_manager.activeExtruderChanged.connect(self.activeMaterialChanged)
        extruder_manager.activeExtruderChanged.connect(self.activeVariantChanged)
        extruder_manager.activeExtruderChanged.connect(self.activeQualityChanged)

        self.globalContainerChanged.connect(self.activeStackChanged)
        ExtruderManager.getInstance().activeExtruderChanged.connect(self.activeStackChanged)
        self.activeStackChanged.connect(self.activeStackValueChanged)

        self._application.getPreferences().addPreference("cura/active_machine", "")

        self._printer_output_devices = []  # type: List[PrinterOutputDevice]
        self._application.getOutputDeviceManager().outputDevicesChanged.connect(self._onOutputDevicesChanged)
        # There might already be some output devices by the time the signal is connected
        self._onOutputDevicesChanged()

        self._current_printer_configuration = PrinterConfigurationModel()   # Indicates the current configuration setup in this printer
        self.activeMaterialChanged.connect(self._onCurrentConfigurationChanged)
        self.activeVariantChanged.connect(self._onCurrentConfigurationChanged)
        # Force to compute the current configuration
        self._onCurrentConfigurationChanged()

        self._application.callLater(self.setInitialActiveMachine)

        containers = CuraContainerRegistry.getInstance().findInstanceContainers(id = self.activeMaterialId)  # type: List[InstanceContainer]
        if containers:
            containers[0].nameChanged.connect(self._onMaterialNameChanged)

        self.rootMaterialChanged.connect(self._onRootMaterialChanged)

        # Emit the printerConnectedStatusChanged when either globalContainerChanged or outputDevicesChanged are emitted
        self.globalContainerChanged.connect(self.printerConnectedStatusChanged)
        self.outputDevicesChanged.connect(self.printerConnectedStatusChanged)

        # For updating active quality display name
        self.activeQualityChanged.connect(self.activeQualityDisplayNameChanged)
        self.activeIntentChanged.connect(self.activeQualityDisplayNameChanged)
        self.activeQualityGroupChanged.connect(self.activeQualityDisplayNameChanged)
        self.activeQualityChangesGroupChanged.connect(self.activeQualityDisplayNameChanged)

    activeQualityDisplayNameChanged = pyqtSignal()

    activeQualityGroupChanged = pyqtSignal()
    activeQualityChangesGroupChanged = pyqtSignal()

    globalContainerChanged = pyqtSignal()  # Emitted whenever the global stack is changed (ie: when changing between printers, changing a global profile, but not when changing a value)
    activeMaterialChanged = pyqtSignal()
    activeVariantChanged = pyqtSignal()
    activeQualityChanged = pyqtSignal()
    activeIntentChanged = pyqtSignal()
    activeStackChanged = pyqtSignal()  # Emitted whenever the active extruder stack is changed (ie: when switching the active extruder tab or changing between printers)
    extruderChanged = pyqtSignal()  # Emitted whenever an extruder is activated or deactivated or the default extruder changes.

    activeStackValueChanged = pyqtSignal()  # Emitted whenever a value inside the active stack is changed.
    activeStackValidationChanged = pyqtSignal()  # Emitted whenever a validation inside active container is changed
    stacksValidationChanged = pyqtSignal()  # Emitted whenever a validation is changed
    numberExtrudersEnabledChanged = pyqtSignal()  # Emitted when the number of extruders that are enabled changed

    blurSettings = pyqtSignal()  # Emitted to force fields in the advanced sidebar to un-focus, so they update properly

    outputDevicesChanged = pyqtSignal()
    currentConfigurationChanged = pyqtSignal()  # Emitted every time the current configurations of the machine changes
    printerConnectedStatusChanged = pyqtSignal() # Emitted every time the active machine change or the outputdevices change

    rootMaterialChanged = pyqtSignal()

    def setInitialActiveMachine(self) -> None:
        active_machine_id = self._application.getPreferences().getValue("cura/active_machine")
        if active_machine_id != "" and CuraContainerRegistry.getInstance().findContainerStacksMetadata(id = active_machine_id):
            # An active machine was saved, so restore it.
            self.setActiveMachine(active_machine_id)

    def _onOutputDevicesChanged(self) -> None:
        self._printer_output_devices = []
        for printer_output_device in self._application.getOutputDeviceManager().getOutputDevices():
            if isinstance(printer_output_device, PrinterOutputDevice):
                self._printer_output_devices.append(printer_output_device)

        self.outputDevicesChanged.emit()

    @pyqtProperty(QObject, notify = currentConfigurationChanged)
    def currentConfiguration(self) -> PrinterConfigurationModel:
        return self._current_printer_configuration

    def _onCurrentConfigurationChanged(self) -> None:
        if not self._global_container_stack:
            return

        # Create the configuration model with the current data in Cura
        self._current_printer_configuration.printerType = self._global_container_stack.definition.getName()

        if len(self._current_printer_configuration.extruderConfigurations) != len(self._global_container_stack.extruderList):
            self._current_printer_configuration.extruderConfigurations = [ExtruderConfigurationModel() for extruder in self._global_container_stack.extruderList]

        for extruder, extruder_configuration in zip(self._global_container_stack.extruderList, self._current_printer_configuration.extruderConfigurations):
            # For compare just the GUID is needed at this moment
            mat_type = extruder.material.getMetaDataEntry("material") if extruder.material != empty_material_container else None
            mat_guid = extruder.material.getMetaDataEntry("GUID") if extruder.material != empty_material_container else None
            mat_color = extruder.material.getMetaDataEntry("color_name") if extruder.material != empty_material_container else None
            mat_brand = extruder.material.getMetaDataEntry("brand") if extruder.material != empty_material_container else None
            mat_name = extruder.material.getMetaDataEntry("name") if extruder.material != empty_material_container else None
            material_model = MaterialOutputModel(mat_guid, mat_type, mat_color, mat_brand, mat_name)

            extruder_configuration.position = int(extruder.getMetaDataEntry("position"))
            extruder_configuration.material = material_model
            extruder_configuration.hotendID = extruder.variant.getName() if extruder.variant != empty_variant_container else None

        # An empty build plate configuration from the network printer is presented as an empty string, so use "" for an
        # empty build plate.
        self._current_printer_configuration.buildplateConfiguration = self._global_container_stack.getProperty("machine_buildplate_type", "value")\
            if self._global_container_stack.variant != empty_variant_container else self._global_container_stack.getProperty("machine_buildplate_type", "default_value")
        self.currentConfigurationChanged.emit()

    @pyqtSlot(QObject, result = bool)
    def matchesConfiguration(self, configuration: PrinterConfigurationModel) -> bool:
        return self._current_printer_configuration == configuration

    @pyqtProperty("QVariantList", notify = outputDevicesChanged)
    def printerOutputDevices(self) -> List[PrinterOutputDevice]:
        return self._printer_output_devices

    @pyqtProperty(int, constant=True)
    def totalNumberOfSettings(self) -> int:
        return len(self.getAllSettingKeys())

    def getAllSettingKeys(self) -> Set[str]:
        general_definition_containers = CuraContainerRegistry.getInstance().findDefinitionContainers(id="fdmprinter")
        if not general_definition_containers:
            return set()
        return general_definition_containers[0].getAllKeys()

    def _onGlobalContainerChanged(self) -> None:
        """Triggered when the global container stack is changed in CuraApplication."""

        if self._global_container_stack:
            try:
                self._global_container_stack.containersChanged.disconnect(self._onContainersChanged)
            except TypeError:
                pass
            try:
                self._global_container_stack.propertyChanged.disconnect(self._onPropertyChanged)
            except TypeError:
                pass

            for extruder_stack in self._global_container_stack.extruderList:
                extruder_stack.propertyChanged.disconnect(self._onPropertyChanged)
                extruder_stack.containersChanged.disconnect(self._onContainersChanged)

        # Update the local global container stack reference
        self._global_container_stack = self._application.getGlobalContainerStack()
        if self._global_container_stack:
            self.updateDefaultExtruder()
            self.updateNumberExtrudersEnabled()
        self.globalContainerChanged.emit()

        # After switching the global stack we reconnect all the signals and set the variant and material references
        if self._global_container_stack:
            self._application.getPreferences().setValue("cura/active_machine", self._global_container_stack.getId())

            self._global_container_stack.containersChanged.connect(self._onContainersChanged)
            self._global_container_stack.propertyChanged.connect(self._onPropertyChanged)

            # Global stack can have only a variant if it is a buildplate
            global_variant = self._global_container_stack.variant
            if global_variant != empty_variant_container:
                if global_variant.getMetaDataEntry("hardware_type") != "buildplate":
                    self._global_container_stack.setVariant(empty_variant_container)

            # Set the global material to empty as we now use the extruder stack at all times - CURA-4482
            global_material = self._global_container_stack.material
            if global_material != empty_material_container:
                self._global_container_stack.setMaterial(empty_material_container)

            # Listen for changes on all extruder stacks
            for extruder_stack in self._global_container_stack.extruderList:
                extruder_stack.propertyChanged.connect(self._onPropertyChanged)
                extruder_stack.containersChanged.connect(self._onContainersChanged)

            self._onRootMaterialChanged()

        self.activeQualityGroupChanged.emit()

    def _onActiveExtruderStackChanged(self) -> None:
        self.blurSettings.emit()  # Ensure no-one has focus.
        self._active_container_stack = ExtruderManager.getInstance().getActiveExtruderStack()

    def __emitChangedSignals(self) -> None:
        self.activeQualityChanged.emit()
        self.activeVariantChanged.emit()
        self.activeMaterialChanged.emit()
        self.activeIntentChanged.emit()

        self.rootMaterialChanged.emit()
        self.numberExtrudersEnabledChanged.emit()

    def _onContainersChanged(self, container: ContainerInterface) -> None:
        self._instance_container_timer.start()

    def _onPropertyChanged(self, key: str, property_name: str) -> None:
        if property_name == "value":
            # Notify UI items, such as the "changed" star in profile pull down menu.
            self.activeStackValueChanged.emit()

    @pyqtSlot(str)
    def setActiveMachine(self, stack_id: Optional[str]) -> None:
        self.blurSettings.emit()  # Ensure no-one has focus.

        if not stack_id:
            self._application.setGlobalContainerStack(None)
            self.globalContainerChanged.emit()
            self._application.showAddPrintersUncancellableDialog.emit()
            return

        container_registry = CuraContainerRegistry.getInstance()
        containers = container_registry.findContainerStacks(id = stack_id)
        if not containers:
            return

        global_stack = cast(GlobalStack, containers[0])

        # Make sure that the default machine actions for this machine have been added
        self._application.getMachineActionManager().addDefaultMachineActions(global_stack)

        extruder_manager = ExtruderManager.getInstance()
        extruder_manager.fixSingleExtrusionMachineExtruderDefinition(global_stack)
        if not global_stack.isValid():
            # Mark global stack as invalid
            ConfigurationErrorMessage.getInstance().addFaultyContainers(global_stack.getId())
            return  # We're done here

        self._global_container_stack = global_stack
        extruder_manager.addMachineExtruders(global_stack)
        self._application.setGlobalContainerStack(global_stack)

        # Switch to the first enabled extruder
        self.updateDefaultExtruder()
        default_extruder_position = int(self.defaultExtruderPosition)
        old_active_extruder_index = extruder_manager.activeExtruderIndex
        extruder_manager.setActiveExtruderIndex(default_extruder_position)
        if old_active_extruder_index == default_extruder_position:
            # This signal might not have been emitted yet (if it didn't change) but we still want the models to update that depend on it because we changed the contents of the containers too.
            extruder_manager.activeExtruderChanged.emit()

        self._validateVariantsAndMaterials(global_stack)

    def _validateVariantsAndMaterials(self, global_stack) -> None:
        # Validate if the machine has the correct variants and materials.
        # It can happen that a variant or material is empty, even though the machine has them. This will ensure that
        # that situation will be fixed (and not occur again, since it switches it out to the preferred variant or
        # variant instead!)
        machine_node = ContainerTree.getInstance().machines[global_stack.definition.getId()]
        if not self._global_container_stack:
            return
        for extruder in self._global_container_stack.extruderList:
            variant_name = extruder.variant.getName()
            variant_node = machine_node.variants.get(variant_name)
            if variant_node is None:
                Logger.log("w", "An extruder has an unknown variant, switching it to the preferred variant")
                self.setVariantByName(extruder.getMetaDataEntry("position"), machine_node.preferred_variant_name)
                variant_node = machine_node.variants.get(machine_node.preferred_variant_name)

            material_node = variant_node.materials.get(extruder.material.getMetaDataEntry("base_file"))
            if material_node is None:
                Logger.log("w", "An extruder has an unknown material, switching it to the preferred material")
                self.setMaterialById(extruder.getMetaDataEntry("position"), machine_node.preferred_material)


    @staticmethod
    def getMachine(definition_id: str, metadata_filter: Optional[Dict[str, str]] = None) -> Optional["GlobalStack"]:
        """Given a definition id, return the machine with this id.

        Optional: add a list of keys and values to filter the list of machines with the given definition id
        :param definition_id: :type{str} definition id that needs to look for
        :param metadata_filter: :type{dict} list of metadata keys and values used for filtering
        """

        if metadata_filter is None:
            metadata_filter = {}
        machines = CuraContainerRegistry.getInstance().findContainerStacks(type = "machine", **metadata_filter)
        for machine in machines:
            if machine.definition.getId() == definition_id:
                return cast(GlobalStack, machine)
        return None

    @pyqtSlot(str, result=bool)
    @pyqtSlot(str, str, result = bool)
    def addMachine(self, definition_id: str, name: Optional[str] = None) -> bool:
        Logger.log("i", "Trying to add a machine with the definition id [%s]", definition_id)
        if name is None:
            definitions = CuraContainerRegistry.getInstance().findDefinitionContainers(id = definition_id)
            if definitions:
                name = definitions[0].getName()
            else:
                name = definition_id

        new_stack = CuraStackBuilder.createMachine(cast(str, name), definition_id)
        if new_stack:
            # Instead of setting the global container stack here, we set the active machine and so the signals are emitted
            self.setActiveMachine(new_stack.getId())
        else:
            Logger.log("w", "Failed creating a new machine!")
            return False
        return True

    def _checkStacksHaveErrors(self) -> bool:
        time_start = time.time()
        if self._global_container_stack is None: #No active machine.
            return False

        if self._global_container_stack.hasErrors():
            Logger.log("d", "Checking global stack for errors took %0.2f s and we found an error" % (time.time() - time_start))
            return True

        # Not a very pretty solution, but the extruder manager doesn't really know how many extruders there are
        machine_extruder_count = self._global_container_stack.getProperty("machine_extruder_count", "value")
        extruder_stacks = self._global_container_stack.extruderList
        count = 1  # We start with the global stack
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

    @pyqtProperty(bool, notify = activeStackValueChanged)
    def hasUserSettings(self) -> bool:
        """Check if the global_container has instances in the user container"""

        if not self._global_container_stack:
            return False

        if self._global_container_stack.getTop().getNumInstances() != 0:
            return True

        for stack in self._global_container_stack.extruderList:
            if stack.getTop().getNumInstances() != 0:
                return True

        return False

    @pyqtProperty(int, notify = activeStackValueChanged)
    def numUserSettings(self) -> int:
        if not self._global_container_stack:
            return 0
        num_user_settings = self._global_container_stack.getTop().getNumInstances()
        stacks = self._global_container_stack.extruderList
        for stack in stacks:
            num_user_settings += stack.getTop().getNumInstances()
        return num_user_settings

    @pyqtSlot(str)
    def clearUserSettingAllCurrentStacks(self, key: str) -> None:
        """Delete a user setting from the global stack and all extruder stacks.

        :param key: :type{str} the name of the key to delete
        """
        Logger.log("i", "Clearing the setting [%s] from all stacks", key)
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
            stacks = self._global_container_stack.extruderList

        for stack in stacks:
            if stack is not None:
                container = stack.getTop()
                container.removeInstance(key, postpone_emit=True)
                send_emits_containers.append(container)

        for container in send_emits_containers:
            container.sendPostponedEmits()

    @pyqtProperty(bool, notify = stacksValidationChanged)
    def stacksHaveErrors(self) -> bool:
        """Check if none of the stacks contain error states

        Note that the _stacks_have_errors is cached due to performance issues
        Calling _checkStack(s)ForErrors on every change is simply too expensive
        """
        return bool(self._stacks_have_errors)

    @pyqtProperty(str, notify = globalContainerChanged)
    def activeMachineFirmwareVersion(self) -> str:
        if not self._printer_output_devices:
            return ""
        return self._printer_output_devices[0].firmwareVersion

    @pyqtProperty(str, notify = globalContainerChanged)
    def activeMachineAddress(self) -> str:
        if not self._printer_output_devices:
            return ""
        return self._printer_output_devices[0].address

    @pyqtProperty(bool, notify = printerConnectedStatusChanged)
    def printerConnected(self) -> bool:
        return bool(self._printer_output_devices)

    @pyqtProperty(bool, notify = printerConnectedStatusChanged)
    def activeMachineIsGroup(self) -> bool:
        if self.activeMachine is None:
            return False

        group_size = int(self.activeMachine.getMetaDataEntry("group_size", "-1"))
        return group_size > 1

    @pyqtProperty(bool, notify = printerConnectedStatusChanged)
    def activeMachineIsLinkedToCurrentAccount(self) -> bool:
        return parseBool(self.activeMachine.getMetaDataEntry(META_UM_LINKED_TO_ACCOUNT, "True"))

    @pyqtProperty(bool, notify = printerConnectedStatusChanged)
    def activeMachineHasNetworkConnection(self) -> bool:
        # A network connection is only available if any output device is actually a network connected device.
        return any(d.connectionType == ConnectionType.NetworkConnection for d in self._printer_output_devices)

    @pyqtProperty(bool, notify = printerConnectedStatusChanged)
    def activeMachineHasCloudConnection(self) -> bool:
        # A cloud connection is only available if any output device actually is a cloud connected device.
        return any(d.connectionType == ConnectionType.CloudConnection for d in self._printer_output_devices)

    @pyqtProperty(bool, notify = printerConnectedStatusChanged)
    def activeMachineHasCloudRegistration(self) -> bool:
        return self.activeMachine is not None and ConnectionType.CloudConnection in self.activeMachine.configuredConnectionTypes

    @pyqtProperty(bool, notify = printerConnectedStatusChanged)
    def activeMachineIsUsingCloudConnection(self) -> bool:
        return self.activeMachineHasCloudConnection and not self.activeMachineHasNetworkConnection

    def activeMachineNetworkKey(self) -> str:
        if self._global_container_stack:
            return self._global_container_stack.getMetaDataEntry("um_network_key", "")
        return ""

    @pyqtProperty(str, notify = printerConnectedStatusChanged)
    def activeMachineNetworkGroupName(self) -> str:
        if self._global_container_stack:
            return self._global_container_stack.getMetaDataEntry("group_name", "")
        return ""

    @pyqtProperty(QObject, notify = globalContainerChanged)
    def activeMachine(self) -> Optional["GlobalStack"]:
        return self._global_container_stack

    @pyqtProperty(str, notify = activeStackChanged)
    def activeStackId(self) -> str:
        if self._active_container_stack:
            return self._active_container_stack.getId()
        return ""

    @pyqtProperty(QObject, notify = activeStackChanged)
    def activeStack(self) -> Optional["ExtruderStack"]:
        return self._active_container_stack

    @pyqtProperty(str, notify = activeMaterialChanged)
    def activeMaterialId(self) -> str:
        if self._active_container_stack:
            material = self._active_container_stack.material
            if material:
                return material.getId()
        return ""

    @pyqtProperty(float, notify = activeQualityGroupChanged)
    def activeQualityLayerHeight(self) -> float:
        """Gets the layer height of the currently active quality profile.

        This is indicated together with the name of the active quality profile.

        :return: The layer height of the currently active quality profile. If
        there is no quality profile, this returns the default layer height.
        """

        if not self._global_container_stack:
            return 0
        value = self._global_container_stack.getRawProperty("layer_height", "value", skip_until_container = self._global_container_stack.qualityChanges.getId())
        if isinstance(value, SettingFunction):
            value = value(self._global_container_stack)
        return value

    @pyqtProperty(str, notify = activeVariantChanged)
    def globalVariantName(self) -> str:
        if self._global_container_stack:
            variant = self._global_container_stack.variant
            if variant and not isinstance(variant, type(empty_variant_container)):
                return variant.getName()
        return ""

    @pyqtProperty(str, notify = activeQualityGroupChanged)
    def activeQualityType(self) -> str:
        global_stack = self._application.getGlobalContainerStack()
        if not global_stack:
            return ""
        return global_stack.quality.getMetaDataEntry("quality_type")

    @pyqtProperty(bool, notify = activeQualityGroupChanged)
    def isActiveQualitySupported(self) -> bool:
        global_container_stack = self._application.getGlobalContainerStack()
        if not global_container_stack:
            return False
        active_quality_group = self.activeQualityGroup()
        if active_quality_group is None:
            return False
        return active_quality_group.is_available


    @pyqtProperty(bool, notify = activeQualityGroupChanged)
    def isActiveQualityExperimental(self) -> bool:
        global_container_stack = self._application.getGlobalContainerStack()
        if not global_container_stack:
            return False
        active_quality_group = self.activeQualityGroup()
        if active_quality_group is None:
            return False
        return active_quality_group.is_experimental

    @pyqtProperty(str, notify = activeIntentChanged)
    def activeIntentCategory(self) -> str:
        global_container_stack = self._application.getGlobalContainerStack()

        if not global_container_stack:
            return ""
        return global_container_stack.getIntentCategory()

    # Provies a list of extruder positions that have a different intent from the active one.
    @pyqtProperty("QStringList", notify=activeIntentChanged)
    def extruderPositionsWithNonActiveIntent(self):
        global_container_stack = _application.getGlobalContainerStack()

        if not global_container_stack:
            return []

        active_intent_category = self.activeIntentCategory
        result = []
        for extruder in global_container_stack.extruderList:
            if not extruder.isEnabled:
                continue
            category = extruder.intent.getMetaDataEntry("intent_category", "default")
            if category != active_intent_category:
                result.append(str(int(extruder.getMetaDataEntry("position")) + 1))

        return result

    @pyqtProperty(bool, notify = activeQualityChanged)
    def isCurrentSetupSupported(self) -> bool:
        """Returns whether there is anything unsupported in the current set-up.

        The current set-up signifies the global stack and all extruder stacks,
        so this indicates whether there is any container in any of the container
        stacks that is not marked as supported.
        """

        if not self._global_container_stack:
            return False
        for stack in [self._global_container_stack] + self._global_container_stack.extruderList:
            for container in stack.getContainers():
                if not container:
                    return False
                if not Util.parseBool(container.getMetaDataEntry("supported", True)):
                    return False
        return True

    @pyqtSlot(str)
    def copyValueToExtruders(self, key: str) -> None:
        """Copy the value of the setting of the current extruder to all other extruders as well as the global container."""

        if self._active_container_stack is None or self._global_container_stack is None:
            return
        new_value = self._active_container_stack.getProperty(key, "value")

        # Check in which stack the value has to be replaced
        for extruder_stack in self._global_container_stack.extruderList:
            if extruder_stack != self._active_container_stack and extruder_stack.getProperty(key, "value") != new_value:
                extruder_stack.userChanges.setProperty(key, "value", new_value)  # TODO: nested property access, should be improved

    @pyqtSlot()
    def copyAllValuesToExtruders(self) -> None:
        """Copy the value of all manually changed settings of the current extruder to all other extruders."""

        if self._active_container_stack is None or self._global_container_stack is None:
            return

        for extruder_stack in self._global_container_stack.extruderList:
            if extruder_stack != self._active_container_stack:
                for key in self._active_container_stack.userChanges.getAllKeys():
                    new_value = self._active_container_stack.getProperty(key, "value")

                    # Check if the value has to be replaced
                    extruder_stack.userChanges.setProperty(key, "value", new_value)

    @pyqtProperty(str, notify = globalContainerChanged)
    def activeQualityDefinitionId(self) -> str:
        """Get the Definition ID to use to select quality profiles for the currently active machine

        :returns: DefinitionID (string) if found, empty string otherwise
        """
        global_stack = self._application.getGlobalContainerStack()
        if not global_stack:
            return ""
        return ContainerTree.getInstance().machines[global_stack.definition.getId()].quality_definition

    @pyqtProperty(str, notify = globalContainerChanged)
    def activeDefinitionVariantsName(self) -> str:
        """Gets how the active definition calls variants

        Caveat: per-definition-variant-title is currently not translated (though the fallback is)
        """
        fallback_title = catalog.i18nc("@label", "Nozzle")
        if self._global_container_stack:
            return self._global_container_stack.definition.getMetaDataEntry("variants_name", fallback_title)

        return fallback_title

    @pyqtSlot(str, str)
    def renameMachine(self, machine_id: str, new_name: str) -> None:
        container_registry = CuraContainerRegistry.getInstance()
        machine_stack = container_registry.findContainerStacks(id = machine_id)
        if machine_stack:
            new_name = container_registry.createUniqueName("machine", machine_stack[0].getName(), new_name, machine_stack[0].definition.getName())
            machine_stack[0].setName(new_name)
            self.globalContainerChanged.emit()

    @pyqtSlot(str)
    def removeMachine(self, machine_id: str) -> None:
        Logger.log("i", "Attempting to remove a machine with the id [%s]", machine_id)
        # If the machine that is being removed is the currently active machine, set another machine as the active machine.
        activate_new_machine = (self._global_container_stack and self._global_container_stack.getId() == machine_id)

        # Activate a new machine before removing a machine because this is safer
        if activate_new_machine:
            machine_stacks = CuraContainerRegistry.getInstance().findContainerStacksMetadata(type = "machine")
            other_machine_stacks = [s for s in machine_stacks if s["id"] != machine_id]
            if other_machine_stacks:
                self.setActiveMachine(other_machine_stacks[0]["id"])
            else:
                self.setActiveMachine(None)

        metadatas = CuraContainerRegistry.getInstance().findContainerStacksMetadata(id = machine_id)
        if not metadatas:
            return  # machine_id doesn't exist. Nothing to remove.
        metadata = metadatas[0]
        ExtruderManager.getInstance().removeMachineExtruders(machine_id)
        containers = CuraContainerRegistry.getInstance().findInstanceContainersMetadata(type = "user", machine = machine_id)
        for container in containers:
            CuraContainerRegistry.getInstance().removeContainer(container["id"])
        machine_stacks = CuraContainerRegistry.getInstance().findContainerStacks(type = "machine", name = machine_id)
        if machine_stacks:
            CuraContainerRegistry.getInstance().removeContainer(machine_stacks[0].definitionChanges.getId())
        CuraContainerRegistry.getInstance().removeContainer(machine_id)

        # If the printer that is being removed is a network printer, the hidden printers have to be also removed
        group_id = metadata.get("group_id", None)
        if group_id:
            metadata_filter = {"group_id": group_id, "hidden": True}
            hidden_containers = CuraContainerRegistry.getInstance().findContainerStacks(type = "machine", **metadata_filter)
            if hidden_containers:
                # This reuses the method and remove all printers recursively
                self.removeMachine(hidden_containers[0].getId())

    @pyqtProperty(bool, notify = activeMaterialChanged)
    def variantBuildplateCompatible(self) -> bool:
        """The selected buildplate is compatible if it is compatible with all the materials in all the extruders"""

        if not self._global_container_stack:
            return True

        buildplate_compatible = True  # It is compatible by default
        for stack in self._global_container_stack.extruderList:
            if not stack.isEnabled:
                continue
            material_container = stack.material
            if material_container == empty_material_container:
                continue
            if material_container.getMetaDataEntry("buildplate_compatible"):
                active_buildplate_name = self.activeMachine.variant.name
                buildplate_compatible = buildplate_compatible and material_container.getMetaDataEntry("buildplate_compatible")[active_buildplate_name]

        return buildplate_compatible

    @pyqtProperty(bool, notify = activeMaterialChanged)
    def variantBuildplateUsable(self) -> bool:
        """The selected buildplate is usable if it is usable for all materials OR it is compatible for one but not compatible

        for the other material but the buildplate is still usable
        """
        if not self._global_container_stack:
            return True

        # Here the next formula is being calculated:
        # result = (not (material_left_compatible and material_right_compatible)) and
        #           (material_left_compatible or material_left_usable) and
        #           (material_right_compatible or material_right_usable)
        result = not self.variantBuildplateCompatible

        for stack in self._global_container_stack.extruderList:
            material_container = stack.material
            if material_container == empty_material_container:
                continue
            buildplate_compatible = material_container.getMetaDataEntry("buildplate_compatible")[self.activeVariantBuildplateName] if material_container.getMetaDataEntry("buildplate_compatible") else True
            buildplate_usable = material_container.getMetaDataEntry("buildplate_recommended")[self.activeVariantBuildplateName] if material_container.getMetaDataEntry("buildplate_recommended") else True

            result = result and (buildplate_compatible or buildplate_usable)

        return result

    @pyqtSlot(str, result = str)
    def getDefinitionByMachineId(self, machine_id: str) -> Optional[str]:
        """Get the Definition ID of a machine (specified by ID)

        :param machine_id: string machine id to get the definition ID of
        :returns: DefinitionID if found, None otherwise
        """
        containers = CuraContainerRegistry.getInstance().findContainerStacks(id = machine_id)
        if containers:
            return containers[0].definition.getId()
        return None

    def getIncompatibleSettingsOnEnabledExtruders(self, container: InstanceContainer) -> List[str]:
        if self._global_container_stack is None:
            return []
        extruder_count = self._global_container_stack.getProperty("machine_extruder_count", "value")
        result = []  # type: List[str]
        for setting_instance in container.findInstances():
            setting_key = setting_instance.definition.key
            if setting_key == "print_sequence":
                old_value = container.getProperty(setting_key, "value")
                Logger.log("d", "Reset setting [%s] in [%s] because its old value [%s] is no longer valid", setting_key, container, old_value)
                result.append(setting_key)
                continue
            if not self._global_container_stack.getProperty(setting_key, "type") in ("extruder", "optional_extruder"):
                continue

            old_value = container.getProperty(setting_key, "value")
            if isinstance(old_value, SettingFunction):
                old_value = old_value(self._global_container_stack)
            if int(old_value) < 0:
                continue
            if int(old_value) >= extruder_count or not self._global_container_stack.extruderList[int(old_value)].isEnabled:
                result.append(setting_key)
                Logger.log("d", "Reset setting [%s] in [%s] because its old value [%s] is no longer valid", setting_key, container, old_value)
        return result

    def correctExtruderSettings(self) -> None:
        """Update extruder number to a valid value when the number of extruders are changed, or when an extruder is changed"""

        if self._global_container_stack is None:
            return
        for setting_key in self.getIncompatibleSettingsOnEnabledExtruders(self._global_container_stack.userChanges):
            self._global_container_stack.userChanges.removeInstance(setting_key)
        add_user_changes = self.getIncompatibleSettingsOnEnabledExtruders(self._global_container_stack.qualityChanges)
        for setting_key in add_user_changes:
            # Apply quality changes that are incompatible to user changes, so we do not change the quality changes itself.
            self._global_container_stack.userChanges.setProperty(setting_key, "value", self._default_extruder_position)
        if add_user_changes:
            caution_message = Message(
                catalog.i18nc("@info:message Followed by a list of settings.", "Settings have been changed to match the current availability of extruders:") + " [{settings_list}]".format(settings_list = ", ".join(add_user_changes)),
                lifetime = 0,
                title = catalog.i18nc("@info:title", "Settings updated"))
            caution_message.show()

    def setActiveMachineExtruderCount(self, extruder_count: int) -> None:
        """Set the amount of extruders on the active machine (global stack)

        :param extruder_count: int the number of extruders to set
        """
        if self._global_container_stack is None:
            return
        extruder_manager = self._application.getExtruderManager()

        definition_changes_container = self._global_container_stack.definitionChanges
        if not self._global_container_stack or definition_changes_container == empty_definition_changes_container:
            return

        previous_extruder_count = self._global_container_stack.getProperty("machine_extruder_count", "value")
        if extruder_count == previous_extruder_count:
            return

        definition_changes_container.setProperty("machine_extruder_count", "value", extruder_count)

        self.updateDefaultExtruder()
        self.numberExtrudersEnabledChanged.emit()
        self.correctExtruderSettings()

        # Check to see if any objects are set to print with an extruder that will no longer exist
        root_node = self._application.getController().getScene().getRoot()
        for node in DepthFirstIterator(root_node):
            if node.getMeshData():
                extruder_nr = node.callDecoration("getActiveExtruderPosition")

                if extruder_nr is not None and int(extruder_nr) > extruder_count - 1:
                    extruder = extruder_manager.getExtruderStack(extruder_count - 1)
                    if extruder is not None:
                        node.callDecoration("setActiveExtruder", extruder.getId())
                    else:
                        Logger.log("w", "Could not find extruder to set active.")

        # Make sure one of the extruder stacks is active
        extruder_manager.setActiveExtruderIndex(0)

        # Move settable_per_extruder values out of the global container
        # After CURA-4482 this should not be the case anymore, but we still want to support older project files.
        global_user_container = self._global_container_stack.userChanges

        for setting_instance in global_user_container.findInstances():
            setting_key = setting_instance.definition.key
            settable_per_extruder = self._global_container_stack.getProperty(setting_key, "settable_per_extruder")

            if settable_per_extruder:
                limit_to_extruder = int(self._global_container_stack.getProperty(setting_key, "limit_to_extruder"))
                extruder_position = max(0, limit_to_extruder)
                extruder_stack = self._global_container_stack.extruderList[extruder_position]
                if extruder_stack:
                    extruder_stack.userChanges.setProperty(setting_key, "value", global_user_container.getProperty(setting_key, "value"))
                else:
                    Logger.log("e", "Unable to find extruder on position %s", extruder_position)
                global_user_container.removeInstance(setting_key)

        # Signal that the global stack has changed
        self._application.globalContainerStackChanged.emit()
        self.forceUpdateAllSettings()

    def updateDefaultExtruder(self) -> None:
        if self._global_container_stack is None:
            return

        old_position = self._default_extruder_position
        new_default_position = "0"
        for extruder in self._global_container_stack.extruderList:
            if extruder.isEnabled:
                new_default_position = extruder.getMetaDataEntry("position", "0")
                break
        if new_default_position != old_position:
            self._default_extruder_position = new_default_position
            self.extruderChanged.emit()

    def updateNumberExtrudersEnabled(self) -> None:
        if self._global_container_stack is None:
            return
        definition_changes_container = self._global_container_stack.definitionChanges
        machine_extruder_count = self._global_container_stack.getProperty("machine_extruder_count", "value")
        extruder_count = 0
        for position, extruder in enumerate(self._global_container_stack.extruderList):
            if extruder.isEnabled and int(position) < machine_extruder_count:
                extruder_count += 1
        if self.numberExtrudersEnabled != extruder_count:
            definition_changes_container.setProperty("extruders_enabled_count", "value", extruder_count)
            self.numberExtrudersEnabledChanged.emit()

    @pyqtProperty(int, notify = numberExtrudersEnabledChanged)
    def numberExtrudersEnabled(self) -> int:
        if self._global_container_stack is None:
            return 1
        extruders_enabled_count = self._global_container_stack.definitionChanges.getProperty("extruders_enabled_count", "value")
        if extruders_enabled_count is None:
            extruders_enabled_count = len(self._global_container_stack.extruderList)
        return extruders_enabled_count

    @pyqtProperty(str, notify = extruderChanged)
    def defaultExtruderPosition(self) -> str:
        return self._default_extruder_position

    @pyqtSlot()
    def forceUpdateAllSettings(self) -> None:
        """This will fire the propertiesChanged for all settings so they will be updated in the front-end"""

        if self._global_container_stack is None:
            return
        with postponeSignals(*self._getContainerChangedSignals(), compress = CompressTechnique.CompressPerParameterValue):
            property_names = ["value", "resolve", "validationState"]
            for container in [self._global_container_stack] + self._global_container_stack.extruderList:
                for setting_key in container.getAllKeys():
                    container.propertiesChanged.emit(setting_key, property_names)

    @pyqtSlot(int, bool)
    def setExtruderEnabled(self, position: int, enabled: bool) -> None:
        if self._global_container_stack is None or position >= len(self._global_container_stack.extruderList):
            Logger.log("w", "Could not find extruder on position %s.", position)
            return
        extruder = self._global_container_stack.extruderList[position]

        extruder.setEnabled(enabled)
        self.updateDefaultExtruder()
        self.updateNumberExtrudersEnabled()
        self.correctExtruderSettings()

        # In case this extruder is being disabled and it's the currently selected one, switch to the default extruder
        if not enabled and position == ExtruderManager.getInstance().activeExtruderIndex:
            ExtruderManager.getInstance().setActiveExtruderIndex(int(self._default_extruder_position))

        # Ensure that the quality profile is compatible with current combination, or choose a compatible one if available
        self._updateQualityWithMaterial()
        self.extruderChanged.emit()
        # Update material compatibility color
        self.activeQualityGroupChanged.emit()
        # Update items in SettingExtruder
        ExtruderManager.getInstance().extrudersChanged.emit(self._global_container_stack.getId())
        # Make sure the front end reflects changes
        self.forceUpdateAllSettings()
        # Also trigger the build plate compatibility to update
        self.activeMaterialChanged.emit()
        self.activeIntentChanged.emit()

    def _onMaterialNameChanged(self) -> None:
        self.activeMaterialChanged.emit()

    def _getContainerChangedSignals(self) -> List[Signal]:
        """Get the signals that signal that the containers changed for all stacks.

        This includes the global stack and all extruder stacks. So if any
        container changed anywhere.
        """

        if self._global_container_stack is None:
            return []
        return [s.containersChanged for s in self._global_container_stack.extruderList + [self._global_container_stack]]

    @pyqtSlot(str, str, str)
    def setSettingForAllExtruders(self, setting_name: str, property_name: str, property_value: str) -> None:
        if self._global_container_stack is None:
            return
        for extruder in self._global_container_stack.extruderList:
            container = extruder.userChanges
            container.setProperty(setting_name, property_name, property_value)

    @pyqtSlot(str)
    def resetSettingForAllExtruders(self, setting_name: str) -> None:
        """Reset all setting properties of a setting for all extruders.

        :param setting_name: The ID of the setting to reset.
        """
        if self._global_container_stack is None:
            return
        for extruder in self._global_container_stack.extruderList:
            container = extruder.userChanges
            container.removeInstance(setting_name)

    def _onRootMaterialChanged(self) -> None:
        """Update _current_root_material_id when the current root material was changed."""

        self._current_root_material_id = {}

        changed = False

        if self._global_container_stack:
            for extruder in self._global_container_stack.extruderList:
                material_id = extruder.material.getMetaDataEntry("base_file")
                position = extruder.getMetaDataEntry("position")
                if position not in self._current_root_material_id or material_id != self._current_root_material_id[position]:
                    changed = True
                    self._current_root_material_id[position] = material_id

        if changed:
            self.activeMaterialChanged.emit()

    @pyqtProperty("QVariant", notify = rootMaterialChanged)
    def currentRootMaterialId(self) -> Dict[str, str]:
        return self._current_root_material_id

    # Sets all quality and quality_changes containers to empty_quality and empty_quality_changes containers
    # for all stacks in the currently active machine.
    #
    def _setEmptyQuality(self) -> None:
        if self._global_container_stack is None:
            return
        self._global_container_stack.quality = empty_quality_container
        self._global_container_stack.qualityChanges = empty_quality_changes_container
        for extruder in self._global_container_stack.extruderList:
            extruder.quality = empty_quality_container
            extruder.qualityChanges = empty_quality_changes_container

        self.activeQualityGroupChanged.emit()
        self.activeQualityChangesGroupChanged.emit()
        self._updateIntentWithQuality()

    def _setQualityGroup(self, quality_group: Optional["QualityGroup"], empty_quality_changes: bool = True) -> None:
        if self._global_container_stack is None:
            return
        if quality_group is None:
            self._setEmptyQuality()
            return

        if quality_group.node_for_global is None or quality_group.node_for_global.container is None:
            return
        for node in quality_group.nodes_for_extruders.values():
            if node.container is None:
                return

        # Set quality and quality_changes for the GlobalStack
        self._global_container_stack.quality = quality_group.node_for_global.container
        if empty_quality_changes:
            self._global_container_stack.qualityChanges = empty_quality_changes_container

        # Set quality and quality_changes for each ExtruderStack
        for position, node in quality_group.nodes_for_extruders.items():
            self._global_container_stack.extruderList[position].quality = node.container
            if empty_quality_changes:
                self._global_container_stack.extruderList[position].qualityChanges = empty_quality_changes_container

        self.activeQualityGroupChanged.emit()
        self.activeQualityChangesGroupChanged.emit()
        self._updateIntentWithQuality()

    def _fixQualityChangesGroupToNotSupported(self, quality_changes_group: "QualityChangesGroup") -> None:
        metadatas = [quality_changes_group.metadata_for_global] + list(quality_changes_group.metadata_per_extruder.values())
        for metadata in metadatas:
            metadata["quality_type"] = "not_supported"  # This actually changes the metadata of the container since they are stored by reference!
        quality_changes_group.quality_type = "not_supported"
        quality_changes_group.intent_category = "default"

    def _setQualityChangesGroup(self, quality_changes_group: "QualityChangesGroup") -> None:
        if self._global_container_stack is None:
            return  # Can't change that.
        quality_type = quality_changes_group.quality_type
        # A custom quality can be created based on "not supported".
        # In that case, do not set quality containers to empty.
        quality_group = None
        if quality_type != "not_supported":  # Find the quality group that the quality changes was based on.
            quality_group = ContainerTree.getInstance().getCurrentQualityGroups().get(quality_type)
            if quality_group is None:
                self._fixQualityChangesGroupToNotSupported(quality_changes_group)

        container_registry = self._application.getContainerRegistry()
        quality_changes_container = empty_quality_changes_container
        quality_container = empty_quality_container  # type: InstanceContainer
        if quality_changes_group.metadata_for_global:
            global_containers = container_registry.findContainers(id = quality_changes_group.metadata_for_global["id"])
            if global_containers:
                quality_changes_container = global_containers[0]
        if quality_changes_group.metadata_for_global:
            containers = container_registry.findContainers(id = quality_changes_group.metadata_for_global["id"])
            if containers:
                quality_changes_container = cast(InstanceContainer, containers[0])
        if quality_group is not None and quality_group.node_for_global and quality_group.node_for_global.container:
            quality_container = quality_group.node_for_global.container

        self._global_container_stack.quality = quality_container
        self._global_container_stack.qualityChanges = quality_changes_container

        for position, extruder in enumerate(self._global_container_stack.extruderList):
            quality_node = None
            if quality_group is not None:
                quality_node = quality_group.nodes_for_extruders.get(position)

            quality_changes_container = empty_quality_changes_container
            quality_container = empty_quality_container
            quality_changes_metadata = quality_changes_group.metadata_per_extruder.get(position)
            if quality_changes_metadata:
                containers = container_registry.findContainers(id = quality_changes_metadata["id"])
                if containers:
                    quality_changes_container = cast(InstanceContainer, containers[0])
            if quality_node and quality_node.container:
                quality_container = quality_node.container

            extruder.quality = quality_container
            extruder.qualityChanges = quality_changes_container

        self.setIntentByCategory(quality_changes_group.intent_category)

        self.activeQualityGroupChanged.emit()
        self.activeQualityChangesGroupChanged.emit()

    def _setVariantNode(self, position: str, variant_node: "VariantNode") -> None:
        if self._global_container_stack is None:
            return
        self._global_container_stack.extruderList[int(position)].variant = variant_node.container
        self.activeVariantChanged.emit()

    def _setGlobalVariant(self, container_node: "ContainerNode") -> None:
        if self._global_container_stack is None:
            return
        self._global_container_stack.variant = container_node.container
        if not self._global_container_stack.variant:
            self._global_container_stack.variant = self._application.empty_variant_container

    def _setMaterial(self, position: str, material_node: Optional["MaterialNode"] = None) -> None:
        if self._global_container_stack is None:
            return
        if material_node and material_node.container:
            material_container = material_node.container
            self._global_container_stack.extruderList[int(position)].material = material_container
            root_material_id = material_container.getMetaDataEntry("base_file", None)
        else:
            self._global_container_stack.extruderList[int(position)].material = empty_material_container
            root_material_id = None
        # The _current_root_material_id is used in the MaterialMenu to see which material is selected
        if position not in self._current_root_material_id or root_material_id != self._current_root_material_id[position]:
            self._current_root_material_id[position] = root_material_id
            self.rootMaterialChanged.emit()

    def activeMaterialsCompatible(self) -> bool:
        # Check material - variant compatibility
        if self._global_container_stack is not None:
            if Util.parseBool(self._global_container_stack.getMetaDataEntry("has_materials", False)):
                for extruder in self._global_container_stack.extruderList:
                    if not extruder.isEnabled:
                        continue
                    if not extruder.material.getMetaDataEntry("compatible"):
                        return False
        return True

    def _updateQualityWithMaterial(self, *args: Any) -> None:
        """Update current quality type and machine after setting material"""

        global_stack = self._application.getGlobalContainerStack()
        if global_stack is None:
            return
        Logger.log("d", "Updating quality/quality_changes due to material change")
        current_quality_type = global_stack.quality.getMetaDataEntry("quality_type")
        candidate_quality_groups = ContainerTree.getInstance().getCurrentQualityGroups()
        available_quality_types = {qt for qt, g in candidate_quality_groups.items() if g.is_available}

        Logger.log("d", "Current quality type = [%s]", current_quality_type)
        if not self.activeMaterialsCompatible():
            if current_quality_type is not None:
                Logger.log("i", "Active materials are not compatible, setting all qualities to empty (Not Supported).")
                self._setEmptyQuality()
            return

        if not available_quality_types:
            Logger.log("i", "No available quality types found, setting all qualities to empty (Not Supported).")
            self._setEmptyQuality()
            return

        if current_quality_type in available_quality_types:
            Logger.log("i", "Current available quality type [%s] is available, applying changes.", current_quality_type)
            self._setQualityGroup(candidate_quality_groups[current_quality_type], empty_quality_changes = False)
            return

        # The current quality type is not available so we use the preferred quality type if it's available,
        # otherwise use one of the available quality types.
        quality_type = sorted(list(available_quality_types))[0]
        if self._global_container_stack is None:
            Logger.log("e", "Global stack not present!")
            return
        preferred_quality_type = self._global_container_stack.getMetaDataEntry("preferred_quality_type")
        if preferred_quality_type in available_quality_types:
            quality_type = preferred_quality_type

        Logger.log("i", "The current quality type [%s] is not available, switching to [%s] instead",
                   current_quality_type, quality_type)
        self._setQualityGroup(candidate_quality_groups[quality_type], empty_quality_changes = True)

    def _updateIntentWithQuality(self):
        """Update the current intent after the quality changed"""

        global_stack = self._application.getGlobalContainerStack()
        if global_stack is None:
            return
        Logger.log("d", "Updating intent due to quality change")

        category = "default"

        for extruder in global_stack.extruderList:
            if not extruder.isEnabled:
                continue
            current_category = extruder.intent.getMetaDataEntry("intent_category", "default")
            if current_category != "default" and current_category != category:
                category = current_category
                continue
            # It's also possible that the qualityChanges has an opinion about the intent_category.
            # This is in the case that a QC was made on an intent, but none of the materials have that intent.
            # If the user switches back, we do want the intent to be selected again.
            #
            # Do not ask empty quality changes for intent category.
            if extruder.qualityChanges.getId() == empty_quality_changes_container.getId():
                continue
            current_category = extruder.qualityChanges.getMetaDataEntry("intent_category", "default")
            if current_category != "default" and current_category != category:
                category = current_category
        self.setIntentByCategory(category)

    @pyqtSlot()
    def updateMaterialWithVariant(self, position: Optional[str] = None) -> None:
        """Update the material profile in the current stacks when the variant is

        changed.
        :param position: The extruder stack to update. If provided with None, all
        extruder stacks will be updated.
        """
        if self._global_container_stack is None:
            return
        if position is None:
            position_list = [str(position) for position in range(len(self._global_container_stack.extruderList))]
        else:
            position_list = [position]

        for position_item in position_list:
            try:
                extruder = self._global_container_stack.extruderList[int(position_item)]
            except IndexError:
                continue

            current_material_base_name = extruder.material.getMetaDataEntry("base_file")
            current_nozzle_name = extruder.variant.getMetaDataEntry("name")

            # If we can keep the current material after the switch, try to do so.
            nozzle_node = ContainerTree.getInstance().machines[self._global_container_stack.definition.getId()].variants[current_nozzle_name]
            candidate_materials = nozzle_node.materials
            old_approximate_material_diameter = int(extruder.material.getMetaDataEntry("approximate_diameter", default = 3))
            new_approximate_material_diameter = int(self._global_container_stack.extruderList[int(position_item)].getApproximateMaterialDiameter())

            # Only switch to the old candidate material if the approximate material diameter of the extruder stays the
            # same.
            if new_approximate_material_diameter == old_approximate_material_diameter and \
                    current_material_base_name in candidate_materials:  # The current material is also available after the switch. Retain it.
                new_material = candidate_materials[current_material_base_name]
                self._setMaterial(position_item, new_material)
            else:
                # The current material is not available, find the preferred one.
                approximate_material_diameter = int(self._global_container_stack.extruderList[int(position_item)].getApproximateMaterialDiameter())
                material_node = nozzle_node.preferredMaterial(approximate_material_diameter)
                self._setMaterial(position_item, material_node)

    @pyqtSlot(str)
    def switchPrinterType(self, machine_name: str) -> None:
        """Given a printer definition name, select the right machine instance. In case it doesn't exist, create a new

        instance with the same network key.
        """
        # Don't switch if the user tries to change to the same type of printer
        if self._global_container_stack is None or self._global_container_stack.definition.name == machine_name:
            return
        Logger.log("i", "Attempting to switch the printer type to [%s]", machine_name)
        # Get the definition id corresponding to this machine name
        definitions = CuraContainerRegistry.getInstance().findDefinitionContainers(name=machine_name)
        if not definitions:
            Logger.log("e", "Unable to switch printer type since it could not be found!")
            return
        machine_definition_id = definitions[0].getId()
        # Try to find a machine with the same network key
        metadata_filter = {"group_id": self._global_container_stack.getMetaDataEntry("group_id")}
        new_machine = self.getMachine(machine_definition_id, metadata_filter = metadata_filter)
        # If there is no machine, then create a new one and set it to the non-hidden instance
        if not new_machine:
            new_machine = CuraStackBuilder.createMachine(machine_definition_id + "_sync", machine_definition_id)
            if not new_machine:
                Logger.log("e", "Failed to create new machine when switching configuration.")
                return

            for metadata_key in self._global_container_stack.getMetaData():
                if metadata_key in new_machine.getMetaData():
                    continue  # Don't copy the already preset stuff.
                new_machine.setMetaDataEntry(metadata_key, self._global_container_stack.getMetaDataEntry(metadata_key))
            # Special case, group_id should be overwritten!
            new_machine.setMetaDataEntry("group_id", self._global_container_stack.getMetaDataEntry("group_id"))
        else:
            Logger.log("i", "Found a %s with the key %s. Let's use it!", machine_name, self.activeMachineNetworkKey())

        # Set the current printer instance to hidden (the metadata entry must exist)
        new_machine.setMetaDataEntry("hidden", False)
        self._global_container_stack.setMetaDataEntry("hidden", True)

        # The new_machine does not contain user changes (global or per-extruder user changes).
        # Keep a temporary copy of the global and per-extruder user changes and transfer them to the user changes
        # of the new machine after the new_machine becomes active.
        global_user_changes = self._global_container_stack.userChanges
        per_extruder_user_changes = [extruder_stack.userChanges for extruder_stack in self._global_container_stack.extruderList]

        self.setActiveMachine(new_machine.getId())

        # Apply the global and per-extruder userChanges to the new_machine (which is of different type than the
        # previous one).
        self._global_container_stack.setUserChanges(global_user_changes)
        for i, user_changes in enumerate(per_extruder_user_changes):
            self._global_container_stack.extruderList[i].setUserChanges(per_extruder_user_changes[i])

    @pyqtSlot(QObject)
    def applyRemoteConfiguration(self, configuration: PrinterConfigurationModel) -> None:
        if self._global_container_stack is None:
            return
        self.blurSettings.emit()
        container_registry = CuraContainerRegistry.getInstance()
        with postponeSignals(*self._getContainerChangedSignals(), compress = CompressTechnique.CompressPerParameterValue):
            self.switchPrinterType(configuration.printerType)

            extruders_to_disable = set()

            # If an extruder that's currently used to print a model gets disabled due to the syncing, we need to show
            # a message explaining why.
            need_to_show_message = False

            for extruder_configuration in configuration.extruderConfigurations:
                # We support "" or None, since the cloud uses None instead of empty strings
                extruder_has_hotend = extruder_configuration.hotendID not in ["", None]
                extruder_has_material = extruder_configuration.material.guid not in [None, "", "00000000-0000-0000-0000-000000000000"]

                # If the machine doesn't have a hotend or material, disable this extruder
                if not extruder_has_hotend or not extruder_has_material:
                    extruders_to_disable.add(extruder_configuration.position)

            # If there's no material and/or nozzle on the printer, enable the first extruder and disable the rest.
            if len(extruders_to_disable) == len(self._global_container_stack.extruderList):
                extruders_to_disable.remove(min(extruders_to_disable))

            for extruder_configuration in configuration.extruderConfigurations:
                position = str(extruder_configuration.position)

                # If the machine doesn't have a hotend or material, disable this extruder
                if int(position) in extruders_to_disable:
                    self._global_container_stack.extruderList[int(position)].setEnabled(False)

                    need_to_show_message = True

                else:
                    machine_node = ContainerTree.getInstance().machines.get(self._global_container_stack.definition.getId())
                    variant_node = machine_node.variants.get(extruder_configuration.hotendID)
                    if variant_node is None:
                        continue
                    self._setVariantNode(position, variant_node)

                    # Find the material profile that the printer has stored.
                    # This might find one of the duplicates if the user duplicated the material to sync with. But that's okay; both have this GUID so both are correct.
                    approximate_diameter = int(self._global_container_stack.extruderList[int(position)].getApproximateMaterialDiameter())
                    materials_with_guid = container_registry.findInstanceContainersMetadata(GUID = extruder_configuration.material.guid, approximate_diameter = str(approximate_diameter), ignore_case = True)
                    material_container_node = variant_node.preferredMaterial(approximate_diameter)
                    if materials_with_guid:  # We also have the material profile that the printer wants to share.
                        base_file = materials_with_guid[0]["base_file"]
                        material_container_node = variant_node.materials.get(base_file, material_container_node)

                    self._setMaterial(position, material_container_node)
                    self._global_container_stack.extruderList[int(position)].setEnabled(True)
                    self.updateMaterialWithVariant(position)

            self.updateDefaultExtruder()
            self.updateNumberExtrudersEnabled()
            self._updateQualityWithMaterial()

            if need_to_show_message:
                msg_str = "{extruders} is disabled because there is no material loaded. Please load a material or use custom configurations."

                # Show human-readable extruder names such as "Extruder Left", "Extruder Front" instead of "Extruder 1, 2, 3".
                extruder_names = []
                for extruder_position in sorted(extruders_to_disable):
                    extruder_stack = self._global_container_stack.extruderList[int(extruder_position)]
                    extruder_name = extruder_stack.definition.getName()
                    extruder_names.append(extruder_name)
                extruders_str = ", ".join(extruder_names)
                msg_str = msg_str.format(extruders = extruders_str)
                message = Message(catalog.i18nc("@info:status", msg_str),
                                  title = catalog.i18nc("@info:title", "Extruder(s) Disabled"))
                message.show()

        # See if we need to show the Discard or Keep changes screen
        if self.hasUserSettings and self._application.getPreferences().getValue("cura/active_mode") == 1:
            self._application.discardOrKeepProfileChanges()

    @pyqtSlot("QVariant")
    def setGlobalVariant(self, container_node: "ContainerNode") -> None:
        self.blurSettings.emit()
        with postponeSignals(*self._getContainerChangedSignals(), compress = CompressTechnique.CompressPerParameterValue):
            self._setGlobalVariant(container_node)
            self.updateMaterialWithVariant(None)  # Update all materials
            self._updateQualityWithMaterial()

    @pyqtSlot(str, str)
    def setMaterialById(self, position: str, root_material_id: str) -> None:
        if self._global_container_stack is None:
            return

        machine_definition_id = self._global_container_stack.definition.id
        position = str(position)
        extruder_stack = self._global_container_stack.extruderList[int(position)]
        nozzle_name = extruder_stack.variant.getName()
        material_node = ContainerTree.getInstance().machines[machine_definition_id].variants[nozzle_name].materials[root_material_id]
        self.setMaterial(position, material_node)

    @pyqtSlot(str, "QVariant")
    def setMaterial(self, position: str, container_node, global_stack: Optional["GlobalStack"] = None) -> None:
        """Global_stack: if you want to provide your own global_stack instead of the current active one

        if you update an active machine, special measures have to be taken.
        """
        if global_stack is not None and global_stack != self._global_container_stack:
            global_stack.extruderList[int(position)].material = container_node.container
            return
        position = str(position)
        self.blurSettings.emit()
        with postponeSignals(*self._getContainerChangedSignals(), compress = CompressTechnique.CompressPerParameterValue):
            self._setMaterial(position, container_node)
            self._updateQualityWithMaterial()

        # See if we need to show the Discard or Keep changes screen
        if self.hasUserSettings and self._application.getPreferences().getValue("cura/active_mode") == 1:
            self._application.discardOrKeepProfileChanges()

    @pyqtSlot(str, str)
    def setVariantByName(self, position: str, variant_name: str) -> None:
        if self._global_container_stack is None:
            return
        machine_definition_id = self._global_container_stack.definition.id
        machine_node = ContainerTree.getInstance().machines.get(machine_definition_id)
        variant_node = machine_node.variants.get(variant_name)
        if variant_node is None:
            Logger.error("There is no variant with the name {variant_name}.")
            return
        self.setVariant(position, variant_node)

    @pyqtSlot(str, "QVariant")
    def setVariant(self, position: str, variant_node: "VariantNode") -> None:
        position = str(position)
        self.blurSettings.emit()
        with postponeSignals(*self._getContainerChangedSignals(), compress = CompressTechnique.CompressPerParameterValue):
            self._setVariantNode(position, variant_node)
            self.updateMaterialWithVariant(position)
            self._updateQualityWithMaterial()

        # See if we need to show the Discard or Keep changes screen
        if self.hasUserSettings and self._application.getPreferences().getValue("cura/active_mode") == 1:
            self._application.discardOrKeepProfileChanges()

    @pyqtSlot(str)
    def setQualityGroupByQualityType(self, quality_type: str) -> None:
        if self._global_container_stack is None:
            return
        # Get all the quality groups for this global stack and filter out by quality_type
        self.setQualityGroup(ContainerTree.getInstance().getCurrentQualityGroups()[quality_type])

    @pyqtSlot(QObject)
    def setQualityGroup(self, quality_group: "QualityGroup", no_dialog: bool = False, global_stack: Optional["GlobalStack"] = None) -> None:
        """Optionally provide global_stack if you want to use your own

        The active global_stack is treated differently.
        """
        if global_stack is not None and global_stack != self._global_container_stack:
            if quality_group is None:
                Logger.log("e", "Could not set quality group because quality group is None")
                return
            if quality_group.node_for_global is None:
                Logger.log("e", "Could not set quality group [%s] because it has no node_for_global", str(quality_group))
                return
            # This is not changing the quality for the active machine !!!!!!!!
            global_stack.quality = quality_group.node_for_global.container
            for extruder_nr, extruder_stack in enumerate(global_stack.extruderList):
                quality_container = empty_quality_container
                if extruder_nr in quality_group.nodes_for_extruders:
                    container = quality_group.nodes_for_extruders[extruder_nr].container
                    quality_container = container if container is not None else quality_container
                extruder_stack.quality = quality_container
            return

        self.blurSettings.emit()
        with postponeSignals(*self._getContainerChangedSignals(), compress = CompressTechnique.CompressPerParameterValue):
            self._setQualityGroup(quality_group)

        # See if we need to show the Discard or Keep changes screen
        if not no_dialog and self.hasUserSettings and self._application.getPreferences().getValue("cura/active_mode") == 1:
            self._application.discardOrKeepProfileChanges()

    # The display name map of currently active quality.
    # The display name has 2 parts, a main part and a suffix part.
    # This display name is:
    #  - For built-in qualities (quality/intent): the quality type name, such as "Fine", "Normal", etc.
    #  - For custom qualities: <custom_quality_name> - <intent_name> - <quality_type_name>
    #        Examples:
    #          - "my_profile - Fine" (only based on a default quality, no intent involved)
    #          - "my_profile - Engineering - Fine" (based on an intent)
    @pyqtProperty("QVariantMap", notify = activeQualityDisplayNameChanged)
    def activeQualityDisplayNameMap(self) -> Dict[str, str]:
        global_stack = self._application.getGlobalContainerStack()
        if global_stack is None:
            return {"main": "",
                    "suffix": ""}

        display_name = global_stack.quality.getName()

        intent_category = self.activeIntentCategory
        if intent_category != "default":
            intent_display_name = IntentCategoryModel.translation(intent_category,
                                                                  "name",
                                                                  catalog.i18nc("@label", "Unknown"))
            display_name = "{intent_name} - {the_rest}".format(intent_name = intent_display_name,
                                                               the_rest = display_name)

        main_part = display_name
        suffix_part = ""

        # Not a custom quality
        if global_stack.qualityChanges != empty_quality_changes_container:
            main_part = self.activeQualityOrQualityChangesName
            suffix_part = display_name

        return {"main": main_part,
                "suffix": suffix_part}

    @pyqtSlot(str)
    def setIntentByCategory(self, intent_category: str) -> None:
        """Change the intent category of the current printer.

        All extruders can change their profiles. If an intent profile is
        available with the desired intent category, that one will get chosen.
        Otherwise the intent profile will be left to the empty profile, which
        represents the "default" intent category.
        :param intent_category: The intent category to change to.
        """

        global_stack = self._application.getGlobalContainerStack()
        if global_stack is None:
            return
        container_tree = ContainerTree.getInstance()
        for extruder in global_stack.extruderList:
            definition_id = global_stack.definition.getId()
            variant_name = extruder.variant.getName()
            material_base_file = extruder.material.getMetaDataEntry("base_file")
            quality_id = extruder.quality.getId()
            if quality_id == empty_quality_container.getId():
                extruder.intent = empty_intent_container
                continue

            # Yes, we can find this in a single line of code. This makes it easier to read and it has the benefit
            # that it doesn't lump key errors together for the crashlogs
            try:
                machine_node = container_tree.machines[definition_id]
                variant_node = machine_node.variants[variant_name]
                material_node = variant_node.materials[material_base_file]
                quality_node = material_node.qualities[quality_id]
            except KeyError as e:
                Logger.error("Can't set the intent category '{category}' since the profile '{profile}' in the stack is not supported according to the container tree.".format(category = intent_category, profile = e))
                continue

            for intent_node in quality_node.intents.values():
                if intent_node.intent_category == intent_category:  # Found an intent with the correct category.
                    extruder.intent = intent_node.container
                    break
            else:  # No intent had the correct category.
                extruder.intent = empty_intent_container

    def activeQualityGroup(self) -> Optional["QualityGroup"]:
        """Get the currently activated quality group.

        If no printer is added yet or the printer doesn't have quality profiles,
        this returns ``None``.
        :return: The currently active quality group.
        """

        global_stack = self._application.getGlobalContainerStack()
        if not global_stack or global_stack.quality == empty_quality_container:
            return None
        return ContainerTree.getInstance().getCurrentQualityGroups().get(self.activeQualityType)

    @pyqtProperty(str, notify = activeQualityGroupChanged)
    def activeQualityGroupName(self) -> str:
        """Get the name of the active quality group.

        :return: The name of the active quality group.
        """
        quality_group = self.activeQualityGroup()
        if quality_group is None:
            return ""
        return quality_group.getName()

    @pyqtSlot(QObject)
    def setQualityChangesGroup(self, quality_changes_group: "QualityChangesGroup", no_dialog: bool = False) -> None:
        self.blurSettings.emit()
        with postponeSignals(*self._getContainerChangedSignals(), compress = CompressTechnique.CompressPerParameterValue):
            self._setQualityChangesGroup(quality_changes_group)

        # See if we need to show the Discard or Keep changes screen
        if not no_dialog and self.hasUserSettings and self._application.getPreferences().getValue("cura/active_mode") == 1:
            self._application.discardOrKeepProfileChanges()

    @pyqtSlot()
    def resetToUseDefaultQuality(self) -> None:
        if self._global_container_stack is None:
            return
        with postponeSignals(*self._getContainerChangedSignals(), compress = CompressTechnique.CompressPerParameterValue):
            self._setQualityGroup(self.activeQualityGroup())
            for stack in [self._global_container_stack] + self._global_container_stack.extruderList:
                stack.userChanges.clear()

    @pyqtProperty(QObject, fset = setQualityChangesGroup, notify = activeQualityChangesGroupChanged)
    def activeQualityChangesGroup(self) -> Optional["QualityChangesGroup"]:
        global_stack = self._application.getGlobalContainerStack()
        if global_stack is None or global_stack.qualityChanges == empty_quality_changes_container:
            return None

        all_group_list = ContainerTree.getInstance().getCurrentQualityChangesGroups()
        the_group = None
        for group in all_group_list:  # Match on the container ID of the global stack to find the quality changes group belonging to the active configuration.
            if group.metadata_for_global and group.metadata_for_global["id"] == global_stack.qualityChanges.getId():
                the_group = group
                break

        return the_group

    @pyqtProperty(bool, notify = activeQualityChangesGroupChanged)
    def hasCustomQuality(self) -> bool:
        global_stack = self._application.getGlobalContainerStack()
        return global_stack is None or global_stack.qualityChanges != empty_quality_changes_container

    @pyqtProperty(str, notify = activeQualityGroupChanged)
    def activeQualityOrQualityChangesName(self) -> str:
        global_container_stack = self._application.getGlobalContainerStack()
        if not global_container_stack:
            return empty_quality_container.getName()
        if global_container_stack.qualityChanges != empty_quality_changes_container:
            return global_container_stack.qualityChanges.getName()
        return global_container_stack.quality.getName()

    @pyqtProperty(bool, notify = activeQualityGroupChanged)
    def hasNotSupportedQuality(self) -> bool:
        global_container_stack = self._application.getGlobalContainerStack()
        return (not global_container_stack is None) and global_container_stack.quality == empty_quality_container and global_container_stack.qualityChanges == empty_quality_changes_container

    @pyqtProperty(bool, notify = activeQualityGroupChanged)
    def isActiveQualityCustom(self) -> bool:
        global_stack = self._application.getGlobalContainerStack()
        if global_stack is None:
            return False
        return global_stack.qualityChanges != empty_quality_changes_container

    def updateUponMaterialMetadataChange(self) -> None:
        if self._global_container_stack is None:
            return
        with postponeSignals(*self._getContainerChangedSignals(), compress = CompressTechnique.CompressPerParameterValue):
            self.updateMaterialWithVariant(None)
            self._updateQualityWithMaterial()

    @pyqtSlot(str, result = str)
    def getAbbreviatedMachineName(self, machine_type_name: str) -> str:
        """This function will translate any printer type name to an abbreviated printer type name"""

        abbr_machine = ""
        for word in re.findall(r"[\w']+", machine_type_name):
            if word.lower() == "ultimaker":
                abbr_machine += "UM"
            elif word.isdigit():
                abbr_machine += word
            else:
                stripped_word = "".join(char for char in unicodedata.normalize("NFD", word.upper()) if unicodedata.category(char) != "Mn")
                # - use only the first character if the word is too long (> 3 characters)
                # - use the whole word if it's not too long (<= 3 characters)
                if len(stripped_word) > 3:
                    stripped_word = stripped_word[0]
                abbr_machine += stripped_word

        return abbr_machine
