# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import json
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from PyQt6.QtCore import pyqtProperty, pyqtSignal, QTimer

import UM.i18n
from UM.FlameProfiler import pyqtSlot
from UM.Logger import Logger
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.Interfaces import PropertyEvaluationContext
from UM.Settings.SettingDefinition import SettingDefinition
from UM.Settings.SettingFunction import SettingFunction
from UM.Util import parseBool

import cura.CuraApplication  # Imported like this to prevent circular dependencies.
from cura.MachineAction import MachineAction
from cura.Machines.ContainerTree import ContainerTree  # To re-build the machine node when hasMaterials changes.
from cura.Settings.CuraStackBuilder import CuraStackBuilder
from cura.Settings.cura_empty_instance_containers import isEmptyContainer

if TYPE_CHECKING:
    from PyQt6.QtCore import QObject

catalog = UM.i18n.i18nCatalog("cura")


class MachineSettingsAction(MachineAction):
    """This action allows for certain settings that are "machine only") to be modified.

    It automatically detects machine definitions that it knows how to change and attaches itself to those.
    """

    pendingChangesChanged = pyqtSignal()

    def __init__(self, parent: Optional["QObject"] = None) -> None:
        super().__init__("MachineSettingsAction", catalog.i18nc("@action", "Machine Settings"))
        self._qml_url = "MachineSettingsAction.qml"

        from cura.CuraApplication import CuraApplication
        self._application = CuraApplication.getInstance()

        from cura.Settings.CuraContainerStack import _ContainerIndexes
        self._store_container_index = _ContainerIndexes.DefinitionChanges

        self._container_registry = ContainerRegistry.getInstance()
        self._container_registry.containerAdded.connect(self._onContainerAdded)

        # The machine settings dialog blocks auto-slicing when it's shown, and re-enables it when it's finished.
        self._backend = self._application.getBackend()
        self.onFinished.connect(self._onFinished)

        # If the g-code flavour changes between UltiGCode and another flavour, we need to update the container tree.
        self._application.globalContainerStackChanged.connect(self._updateHasMaterialsInContainerTree)

        # Staged edits that are not written to the stacks until they are applied.
        self._pending_changes: Dict[Tuple[str, str], Any] = {}
        self._pending_revision = 0

    # Which container index in a stack to store machine setting changes.
    @pyqtProperty(int, constant = True)
    def storeContainerIndex(self) -> int:
        return self._store_container_index

    def _onContainerAdded(self, container):
        # Add this action as a supported action to all machine definitions
        if isinstance(container, DefinitionContainer) and container.getMetaDataEntry("type") == "machine":
            self._application.getMachineActionManager().addSupportedAction(container.getId(), self.getKey())

    def _updateHasMaterialsInContainerTree(self) -> None:
        """Triggered when the global container stack changes or when the g-code

        flavour setting is changed.
        """
        global_stack = cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack()
        if global_stack is None:
            return
        machine_node = ContainerTree.getInstance().machines[global_stack.definition.getId()]

        if machine_node.has_materials != parseBool(global_stack.getMetaDataEntry("has_materials")):  # May have changed due to the g-code flavour.
            machine_node.has_materials = parseBool(global_stack.getMetaDataEntry("has_materials"))
            machine_node._loadAll()

    def _reset(self):
        self.discardPendingChanges()

        global_stack = self._application.getMachineManager().activeMachine
        if not global_stack:
            return

        # Make sure there is a definition_changes container to store the machine settings
        definition_changes_id = global_stack.definitionChanges.getId()
        if isEmptyContainer(definition_changes_id):
            CuraStackBuilder.createDefinitionChangesContainer(global_stack,
                                                              global_stack.getName() + "_settings")

        # Disable auto-slicing while the MachineAction is showing
        if self._backend:  # This sometimes triggers before backend is loaded.
            self._backend.disableTimer()

    def _onFinished(self):
        # Restore auto-slicing when the machine action is dismissed
        if self._backend and self._backend.determineAutoSlicing():
            self._backend.enableTimer()
            self._backend.tickle()

    @pyqtSlot()
    def setFinished(self) -> None:
        # When the action is used as a page of the first-start wizard there is no Save button: continuing saves.
        self.applyPendingChanges()
        super().setFinished()

    @pyqtSlot()
    def updateHasMaterialsMetadata(self) -> None:
        global_stack = self._application.getMachineManager().activeMachine

        # Updates the has_materials metadata flag after switching gcode flavor
        if not global_stack:
            return

        definition = global_stack.getDefinition()
        if definition.getProperty("machine_gcode_flavor", "value") != "UltiGCode" or parseBool(definition.getMetaDataEntry("has_materials", False)):
            # In other words: only continue for the UM2 (extended), but not for the UM2+
            return

        machine_manager = self._application.getMachineManager()
        has_materials = global_stack.getProperty("machine_gcode_flavor", "value") != "UltiGCode"

        if has_materials:
            global_stack.setMetaDataEntry("has_materials", True)
        else:
            # The metadata entry is stored in an ini, and ini files are parsed as strings only.
            # Because any non-empty string evaluates to a boolean True, we have to remove the entry to make it False.
            if "has_materials" in global_stack.getMetaData():
                global_stack.removeMetaDataEntry("has_materials")

        self._updateHasMaterialsInContainerTree()

        # set materials
        machine_node = ContainerTree.getInstance().machines[global_stack.definition.getId()]
        for position, extruder in enumerate(global_stack.extruderList):
            #Find out what material we need to default to.
            approximate_diameter = round(extruder.getProperty("material_diameter", "value"))
            material_node = machine_node.variants[extruder.variant.getName()].preferredMaterial(approximate_diameter)
            machine_manager.setMaterial(str(position), material_node)

        self._application.globalContainerStackChanged.emit()

    @pyqtSlot(int)
    def updateMaterialForDiameter(self, extruder_position: int) -> None:
        # Updates the material container to a material that matches the material diameter set for the printer
        self._application.getMachineManager().updateMaterialWithVariant(str(extruder_position))

    @pyqtProperty(bool, notify = pendingChangesChanged)
    def hasPendingChanges(self) -> bool:
        return len(self._pending_changes) > 0

    @pyqtProperty(int, notify = pendingChangesChanged)
    def pendingRevision(self) -> int:
        """Increases whenever the staged edits change. Bindings in QML read this to know when to re-evaluate."""
        return self._pending_revision

    def _notifyPendingChanged(self) -> None:
        self._pending_revision += 1
        self.pendingChangesChanged.emit()

    @pyqtSlot(str, str, result = bool)
    def hasPendingValue(self, stack_id: str, key: str) -> bool:
        return (stack_id, key) in self._pending_changes

    @pyqtSlot(str, str, result = "QVariant")
    def pendingValue(self, stack_id: str, key: str) -> Any:
        return self._pending_changes.get((stack_id, key))

    @pyqtSlot(str, str, "QVariant")
    def setPendingValue(self, stack_id: str, key: str, value: Any) -> None:
        if self._stageValue(stack_id, key, value):
            self._notifyPendingChanged()

    @pyqtSlot()
    def discardPendingChanges(self) -> None:
        if self._pending_changes:
            self._pending_changes = {}
            self._notifyPendingChanged()

    @pyqtSlot("QVariantList")
    def restoreDefaults(self, settings: List[Dict[str, str]]) -> None:
        """Stage the definition's default for the given settings, as dictionaries with a "stackId" and a "key"."""
        changed = False
        for setting in settings:
            stack_id, key = setting["stackId"], setting["key"]
            stack = self._findStack(stack_id)
            if stack is None:
                continue

            container = stack.getContainer(self._store_container_index)
            default_value = self._getDefaultValue(stack, key)
            if default_value is not None and not isEmptyContainer(container.getId()) and container.hasProperty(key, "value"):
                changed = self._stageValue(stack_id, key, default_value) or changed
            else:
                # Nothing is overridden for this setting, so it already has its default. Only drop what was staged.
                changed = self._pending_changes.pop((stack_id, key), None) is not None or changed
        if changed:
            self._notifyPendingChanged()

    def _stageValue(self, stack_id: str, key: str, value: Any) -> bool:
        stack = self._findStack(stack_id)
        if stack is None:
            return False

        pending_key = (stack_id, key)
        if self._valuesEqual(value, self._getStoredValue(stack, key)):
            # Back at the stored value: nothing left to save for this setting.
            return self._pending_changes.pop(pending_key, None) is not None
        if pending_key in self._pending_changes and self._pending_changes[pending_key] == value:
            return False
        self._pending_changes[pending_key] = value
        return True

    def _findStack(self, stack_id: str):
        stacks = self._container_registry.findContainerStacks(id = stack_id)
        return stacks[0] if stacks else None

    def _getStoredValue(self, stack, key: str) -> str:
        context = PropertyEvaluationContext(stack)
        context.context["evaluate_from_container_index"] = self._store_container_index
        value = stack.getProperty(key, "value", context = context)
        if isinstance(value, SettingFunction):
            value = value(stack)
        setting_type = stack.getProperty(key, "type")
        if setting_type is None or value is None:
            return ""
        return SettingDefinition.settingValueToString(setting_type, value)

    @staticmethod
    def _getDefaultValue(stack, key: str) -> Optional[str]:
        definition = stack.definition
        value = definition.getProperty(key, "value")
        setting_type = definition.getProperty(key, "type")
        if value is None or setting_type is None:
            return None
        if isinstance(value, SettingFunction):
            value = value(stack)
        return SettingDefinition.settingValueToString(setting_type, value)

    @staticmethod
    def _valuesEqual(first: Any, second: Any) -> bool:
        """Compare two values that may be formatted differently, like "1" and "1.0", or "true" and True."""
        first, second = str(first), str(second)
        if first == second:
            return True
        if first.lower() in ("true", "false") and second.lower() in ("true", "false"):
            return first.lower() == second.lower()
        try:
            return float(first.replace(",", ".")) == float(second.replace(",", "."))
        except ValueError:
            pass
        try:
            return json.loads(first) == json.loads(second)  # Polygons.
        except ValueError:
            return False

    @pyqtSlot()
    def applyPendingChanges(self) -> None:
        """Write all staged edits to the stacks in one go.

        Everything that is expensive is done at most once for the whole batch, instead of once per edited field:
        - Auto-slicing is paused until the batch is done.
        - The stacks are refreshed once, after the current event has been handled so that the dialog can close first.
        - Only the containers that were actually changed are written to disk, instead of every dirty container.
        """
        if not self._pending_changes:
            return

        changes = self._pending_changes
        machine_manager = self._application.getMachineManager()
        if machine_manager.activeMachine is None:
            self.discardPendingChanges()
            return

        backend = self._application.getBackend()
        if backend:
            backend.disableTimer()

        touched = []  # type: List[Any]
        needs_refresh = False
        refresh_all_settings = False
        try:
            needs_refresh, refresh_all_settings = self._writeChanges(changes, touched)
        except Exception:
            Logger.logException("e", "Unable to save all of the machine settings.")
        finally:
            self._pending_changes = {}
            self._notifyPendingChanged()
            QTimer.singleShot(0, lambda: self._finishApplying(needs_refresh, refresh_all_settings, touched))

    def _writeChanges(self, changes: Dict[Tuple[str, str], Any], touched: List[Any]) -> Tuple[bool, bool]:
        """Write the changes to the stacks and add every changed container and stack to `touched`.

        :return: Whether the stacks need to be refreshed, and whether all settings need to be updated for that.
        """
        machine_manager = self._application.getMachineManager()
        global_stack = machine_manager.activeMachine
        needs_refresh = False
        update_has_materials = False
        new_extruder_count = None  # type: Optional[int]
        diameter_positions = []  # type: List[str]

        def addTouched(item) -> None:
            if not any(item is other for other in touched):
                touched.append(item)

        for (stack_id, key), value in changes.items():
            stack = self._findStack(stack_id)
            if stack is None:
                continue

            if key == "machine_extruder_count":
                new_extruder_count = int(float(value))  # This has its own logic, so do it after the other changes.
                continue

            container = stack.getContainer(self._store_container_index)
            if container is None or isEmptyContainer(container.getId()):
                container = CuraStackBuilder.createDefinitionChangesContainer(stack, stack.getName() + "_settings")
                addTouched(stack)
            addTouched(container)

            default_value = self._getDefaultValue(stack, key)
            if default_value is not None and self._valuesEqual(value, default_value):
                container.removeInstance(key)
            else:
                container.setProperty(key, "value", value)

            # Settings that hold text (like the start g-code) only change the text that ends up in the g-code, so there
            # is nothing else to refresh for them.
            if stack.getProperty(key, "type") != "str":
                needs_refresh = True
            if key == "machine_gcode_flavor":
                update_has_materials = True
            if key == "material_diameter":
                diameter_positions.append(str(stack.getMetaDataEntry("position", "0")))

        refresh_all_settings = needs_refresh
        if new_extruder_count is not None:
            if new_extruder_count != int(global_stack.getProperty("machine_extruder_count", "value")):
                # Changing the number of extruders updates all settings by itself.
                machine_manager.setActiveMachineExtruderCount(new_extruder_count)
                needs_refresh = True
                refresh_all_settings = False
            update_has_materials = True
            addTouched(global_stack.definitionChanges)

        if update_has_materials:
            self.updateHasMaterialsMetadata()
        for position in diameter_positions:
            self.updateMaterialForDiameter(int(position))

        return needs_refresh, refresh_all_settings

    def _finishApplying(self, needs_refresh: bool, refresh_all_settings: bool, touched: List[Any]) -> None:
        machine_manager = self._application.getMachineManager()
        if needs_refresh:
            # Force rebuilding the build volume by reloading the global container stack.
            machine_manager.globalContainerChanged.emit()
            if refresh_all_settings:
                machine_manager.forceUpdateAllSettings()

        # Only write what we changed. The regular saving of all dirty containers will pick up the rest later.
        for item in touched:
            self._application.saveStack(item)

        self._onFinished()  # Resume auto-slicing.
