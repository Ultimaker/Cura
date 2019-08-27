# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING, Optional, Dict, List

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from UM.Logger import Logger
from UM.Util import parseBool
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Decorators import deprecated

import cura.CuraApplication
from cura.Settings.ExtruderStack import ExtruderStack

from cura.Machines.ContainerTree import ContainerTree  # The implementation that replaces this manager, to keep the deprecated interface working.
from .QualityChangesGroup import QualityChangesGroup
from .QualityGroup import QualityGroup
from .QualityNode import QualityNode

if TYPE_CHECKING:
    from UM.Settings.Interfaces import DefinitionContainerInterface
    from cura.Settings.GlobalStack import GlobalStack
    from .QualityChangesGroup import QualityChangesGroup


#
# Similar to MaterialManager, QualityManager maintains a number of maps and trees for quality profile lookup.
# The models GUI and QML use are now only dependent on the QualityManager. That means as long as the data in
# QualityManager gets updated correctly, the GUI models should be updated correctly too, and the same goes for GUI.
#
# For now, updating the lookup maps and trees here is very simple: we discard the old data completely and recreate them
# again. This means the update is exactly the same as initialization. There are performance concerns about this approach
# but so far the creation of the tables and maps is very fast and there is no noticeable slowness, we keep it like this
# because it's simple.
#
class QualityManager(QObject):
    __instance = None

    @classmethod
    @deprecated("Use the ContainerTree structure instead.", since = "4.3")
    def getInstance(cls) -> "QualityManager":
        if cls.__instance is None:
            cls.__instance = QualityManager()
        return cls.__instance

    qualitiesUpdated = pyqtSignal()

    def __init__(self, parent = None) -> None:
        super().__init__(parent)
        application = cura.CuraApplication.CuraApplication.getInstance()
        self._material_manager = application.getMaterialManager()
        self._container_registry = application.getContainerRegistry()

        self._empty_quality_container = application.empty_quality_container
        self._empty_quality_changes_container = application.empty_quality_changes_container

        # For quality lookup
        self._machine_nozzle_buildplate_material_quality_type_to_quality_dict = {}  # type: Dict[str, QualityNode]

        # For quality_changes lookup
        self._machine_quality_type_to_quality_changes_dict = {}  # type: Dict[str, QualityNode]

        self._default_machine_definition_id = "fdmprinter"

        self._container_registry.containerMetaDataChanged.connect(self._onContainerMetadataChanged)
        self._container_registry.containerAdded.connect(self._onContainerMetadataChanged)
        self._container_registry.containerRemoved.connect(self._onContainerMetadataChanged)

    def _onContainerMetadataChanged(self, container: InstanceContainer) -> None:
        self._onContainerChanged(container)

    def _onContainerChanged(self, container: InstanceContainer) -> None:
        container_type = container.getMetaDataEntry("type")
        if container_type not in ("quality", "quality_changes"):
            return

    # Returns a dict of "custom profile name" -> QualityChangesGroup
    def getQualityChangesGroups(self, machine: "GlobalStack") -> List[QualityChangesGroup]:
        variant_names = [extruder.variant.getName() for extruder in machine.extruders.values()]
        material_bases = [extruder.material.getMetaDataEntry("base_file") for extruder in machine.extruders.values()]
        extruder_enabled = [extruder.isEnabled for extruder in machine.extruders.values()]
        machine_node = ContainerTree.getInstance().machines[machine.definition.getId()]
        return machine_node.getQualityChangesGroups(variant_names, material_bases, extruder_enabled)

    ##  Gets the quality groups for the current printer.
    #
    #   Both available and unavailable quality groups will be included. Whether
    #   a quality group is available can be known via the field
    #   ``QualityGroup.is_available``. For more details, see QualityGroup.
    #   \return A dictionary with quality types as keys and the quality groups
    #   for those types as values.
    def getQualityGroups(self, global_stack: "GlobalStack") -> Dict[str, QualityGroup]:
        # Gather up the variant names and material base files for each extruder.
        variant_names = [extruder.variant.getName() for extruder in global_stack.extruders.values()]
        material_bases = [extruder.material.getMetaDataEntry("base_file") for extruder in global_stack.extruders.values()]
        extruder_enabled = [extruder.isEnabled for extruder in global_stack.extruders.values()]
        definition_id = global_stack.definition.getId()
        return ContainerTree.getInstance().machines[definition_id].getQualityGroups(variant_names, material_bases, extruder_enabled)

    def getQualityGroupsForMachineDefinition(self, machine: "GlobalStack") -> Dict[str, QualityGroup]:
        machine_definition_id = getMachineDefinitionIDForQualitySearch(machine.definition)

        # To find the quality container for the GlobalStack, check in the following fall-back manner:
        #   (1) the machine-specific node
        #   (2) the generic node
        machine_node = self._machine_nozzle_buildplate_material_quality_type_to_quality_dict.get(machine_definition_id)
        default_machine_node = self._machine_nozzle_buildplate_material_quality_type_to_quality_dict.get(
            self._default_machine_definition_id)
        nodes_to_check = [machine_node, default_machine_node]

        # Iterate over all quality_types in the machine node
        quality_group_dict = dict()
        for node in nodes_to_check:
            if node and node.quality_type:
                quality_group = QualityGroup(node.getMetaDataEntry("name", ""), node.quality_type)
                quality_group.setGlobalNode(node)
                quality_group_dict[node.quality_type] = quality_group

        return quality_group_dict

    ##  Get the quality group for the preferred quality type for a certain
    #   global stack.
    #
    #   If the preferred quality type is not available, ``None`` will be
    #   returned.
    #   \param machine The global stack of the machine to get the preferred
    #   quality group for.
    #   \return The preferred quality group, or ``None`` if that is not
    #   available.
    def getDefaultQualityType(self, machine: "GlobalStack") -> Optional[QualityGroup]:
        machine_node = ContainerTree.getInstance().machines[machine.definition.getId()]
        quality_groups = self.getQualityGroups(machine)
        result = quality_groups.get(machine_node.preferred_quality_type)
        if result is not None and result.is_available:
            return result
        return None  # If preferred quality type is not available, leave it up for the caller.


    #
    # Methods for GUI
    #

    #
    # Remove the given quality changes group.
    #
    @pyqtSlot(QObject)
    def removeQualityChangesGroup(self, quality_changes_group: "QualityChangesGroup") -> None:
        Logger.log("i", "Removing quality changes group [%s]", quality_changes_group.name)
        removed_quality_changes_ids = set()
        for node in quality_changes_group.getAllNodes():
            container_id = node.container_id
            self._container_registry.removeContainer(container_id)
            removed_quality_changes_ids.add(container_id)

        # Reset all machines that have activated this quality changes to empty.
        for global_stack in self._container_registry.findContainerStacks(type = "machine"):
            if global_stack.qualityChanges.getId() in removed_quality_changes_ids:
                global_stack.qualityChanges = self._empty_quality_changes_container
        for extruder_stack in self._container_registry.findContainerStacks(type = "extruder_train"):
            if extruder_stack.qualityChanges.getId() in removed_quality_changes_ids:
                extruder_stack.qualityChanges = self._empty_quality_changes_container

    #
    # Rename a set of quality changes containers. Returns the new name.
    #
    @pyqtSlot(QObject, str, result = str)
    def renameQualityChangesGroup(self, quality_changes_group: "QualityChangesGroup", new_name: str) -> str:
        Logger.log("i", "Renaming QualityChangesGroup[%s] to [%s]", quality_changes_group.name, new_name)
        if new_name == quality_changes_group.name:
            Logger.log("i", "QualityChangesGroup name [%s] unchanged.", quality_changes_group.name)
            return new_name

        new_name = self._container_registry.uniqueName(new_name)
        for node in quality_changes_group.getAllNodes():
            container = node.container
            if container:
                container.setName(new_name)

        quality_changes_group.name = new_name

        application = cura.CuraApplication.CuraApplication.getInstance()
        application.getMachineManager().activeQualityChanged.emit()
        application.getMachineManager().activeQualityGroupChanged.emit()

        return new_name

    #
    # Duplicates the given quality.
    #
    @pyqtSlot(str, "QVariantMap")
    def duplicateQualityChanges(self, quality_changes_name: str, quality_model_item) -> None:
        global_stack = cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack()
        if not global_stack:
            Logger.log("i", "No active global stack, cannot duplicate quality changes.")
            return

        quality_group = quality_model_item["quality_group"]
        quality_changes_group = quality_model_item["quality_changes_group"]
        if quality_changes_group is None:
            # create global quality changes only
            new_name = self._container_registry.uniqueName(quality_changes_name)
            new_quality_changes = self._createQualityChanges(quality_group.quality_type, new_name,
                                                             global_stack, None)
            self._container_registry.addContainer(new_quality_changes)
        else:
            new_name = self._container_registry.uniqueName(quality_changes_name)
            for node in quality_changes_group.getAllNodes():
                container = node.container
                if not container:
                    continue
                new_id = self._container_registry.uniqueName(container.getId())
                self._container_registry.addContainer(container.duplicate(new_id, new_name))

    ##  Create quality changes containers from the user containers in the active stacks.
    #
    #   This will go through the global and extruder stacks and create quality_changes containers from
    #   the user containers in each stack. These then replace the quality_changes containers in the
    #   stack and clear the user settings.
    @pyqtSlot(str)
    def createQualityChanges(self, base_name: str) -> None:
        machine_manager = cura.CuraApplication.CuraApplication.getInstance().getMachineManager()

        global_stack = machine_manager.activeMachine
        if not global_stack:
            return

        active_quality_name = machine_manager.activeQualityOrQualityChangesName
        if active_quality_name == "":
            Logger.log("w", "No quality container found in stack %s, cannot create profile", global_stack.getId())
            return

        machine_manager.blurSettings.emit()
        if base_name is None or base_name == "":
            base_name = active_quality_name
        unique_name = self._container_registry.uniqueName(base_name)

        # Go through the active stacks and create quality_changes containers from the user containers.
        stack_list = [global_stack] + list(global_stack.extruders.values())
        for stack in stack_list:
            user_container = stack.userChanges
            quality_container = stack.quality
            quality_changes_container = stack.qualityChanges
            if not quality_container or not quality_changes_container:
                Logger.log("w", "No quality or quality changes container found in stack %s, ignoring it", stack.getId())
                continue

            quality_type = quality_container.getMetaDataEntry("quality_type")
            extruder_stack = None
            if isinstance(stack, ExtruderStack):
                extruder_stack = stack
            new_changes = self._createQualityChanges(quality_type, unique_name, global_stack, extruder_stack)
            from cura.Settings.ContainerManager import ContainerManager
            ContainerManager.getInstance()._performMerge(new_changes, quality_changes_container, clear_settings = False)
            ContainerManager.getInstance()._performMerge(new_changes, user_container)

            self._container_registry.addContainer(new_changes)

    #
    # Create a quality changes container with the given setup.
    #
    def _createQualityChanges(self, quality_type: str, new_name: str, machine: "GlobalStack",
                              extruder_stack: Optional["ExtruderStack"]) -> "InstanceContainer":
        base_id = machine.definition.getId() if extruder_stack is None else extruder_stack.getId()
        new_id = base_id + "_" + new_name
        new_id = new_id.lower().replace(" ", "_")
        new_id = self._container_registry.uniqueName(new_id)

        # Create a new quality_changes container for the quality.
        quality_changes = InstanceContainer(new_id)
        quality_changes.setName(new_name)
        quality_changes.setMetaDataEntry("type", "quality_changes")
        quality_changes.setMetaDataEntry("quality_type", quality_type)

        # If we are creating a container for an extruder, ensure we add that to the container
        if extruder_stack is not None:
            quality_changes.setMetaDataEntry("position", extruder_stack.getMetaDataEntry("position"))

        # If the machine specifies qualities should be filtered, ensure we match the current criteria.
        machine_definition_id = getMachineDefinitionIDForQualitySearch(machine.definition)
        quality_changes.setDefinition(machine_definition_id)

        quality_changes.setMetaDataEntry("setting_version", cura.CuraApplication.CuraApplication.getInstance().SettingVersion)
        return quality_changes


#
# Gets the machine definition ID that can be used to search for Quality containers that are suitable for the given
# machine. The rule is as follows:
#   1. By default, the machine definition ID for quality container search will be "fdmprinter", which is the generic
#      machine.
#   2. If a machine has its own machine quality (with "has_machine_quality = True"), we should use the given machine's
#      own machine definition ID for quality search.
#      Example: for an Ultimaker 3, the definition ID should be "ultimaker3".
#   3. When condition (2) is met, AND the machine has "quality_definition" defined in its definition file, then the
#      definition ID specified in "quality_definition" should be used.
#      Example: for an Ultimaker 3 Extended, it has "quality_definition = ultimaker3". This means Ultimaker 3 Extended
#               shares the same set of qualities profiles as Ultimaker 3.
#
def getMachineDefinitionIDForQualitySearch(machine_definition: "DefinitionContainerInterface",
                                           default_definition_id: str = "fdmprinter") -> str:
    machine_definition_id = default_definition_id
    if parseBool(machine_definition.getMetaDataEntry("has_machine_quality", False)):
        # Only use the machine's own quality definition ID if this machine has machine quality.
        machine_definition_id = machine_definition.getMetaDataEntry("quality_definition")
        if machine_definition_id is None:
            machine_definition_id = machine_definition.getId()

    return machine_definition_id
