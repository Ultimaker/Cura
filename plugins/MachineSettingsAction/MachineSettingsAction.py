# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, TYPE_CHECKING

from PyQt5.QtCore import pyqtProperty

import UM.i18n
from UM.FlameProfiler import pyqtSlot
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Util import parseBool

from cura.MachineAction import MachineAction
from cura.Settings.CuraStackBuilder import CuraStackBuilder
from cura.Settings.cura_empty_instance_containers import isEmptyContainer

if TYPE_CHECKING:
    from PyQt5.QtCore import QObject

catalog = UM.i18n.i18nCatalog("cura")


##  This action allows for certain settings that are "machine only") to be modified.
#   It automatically detects machine definitions that it knows how to change and attaches itself to those.
class MachineSettingsAction(MachineAction):
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

    # Which container index in a stack to store machine setting changes.
    @pyqtProperty(int, constant = True)
    def storeContainerIndex(self) -> int:
        return self._store_container_index

    def _onContainerAdded(self, container):
        # Add this action as a supported action to all machine definitions
        if isinstance(container, DefinitionContainer) and container.getMetaDataEntry("type") == "machine":
            self._application.getMachineActionManager().addSupportedAction(container.getId(), self.getKey())

    def _reset(self):
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

    @pyqtSlot(int)
    def setMachineExtruderCount(self, extruder_count: int) -> None:
        # Note: this method was in this class before, but since it's quite generic and other plugins also need it
        # it was moved to the machine manager instead. Now this method just calls the machine manager.
        self._application.getMachineManager().setActiveMachineExtruderCount(extruder_count)

    @pyqtSlot()
    def forceUpdate(self) -> None:
        # Force rebuilding the build volume by reloading the global container stack.
        # This is a bit of a hack, but it seems quick enough.
        self._application.getMachineManager().globalContainerChanged.emit()

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
        material_manager = self._application.getMaterialManager()
        extruder_positions = list(global_stack.extruders.keys())
        has_materials = global_stack.getProperty("machine_gcode_flavor", "value") != "UltiGCode"

        material_node = None
        if has_materials:
            global_stack.setMetaDataEntry("has_materials", True)
        else:
            # The metadata entry is stored in an ini, and ini files are parsed as strings only.
            # Because any non-empty string evaluates to a boolean True, we have to remove the entry to make it False.
            if "has_materials" in global_stack.getMetaData():
                global_stack.removeMetaDataEntry("has_materials")

        # set materials
        for position in extruder_positions:
            if has_materials:
                material_node = material_manager.getDefaultMaterial(global_stack, position, None)
            machine_manager.setMaterial(position, material_node)

        self._application.globalContainerStackChanged.emit()

    @pyqtSlot(int)
    def updateMaterialForDiameter(self, extruder_position: int) -> None:
        # Updates the material container to a material that matches the material diameter set for the printer
        self._application.getMachineManager().updateMaterialWithVariant(str(extruder_position))
