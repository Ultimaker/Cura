# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, pyqtSignal
from UM.FlameProfiler import pyqtSlot

from cura.MachineAction import MachineAction

from UM.Application import Application
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Logger import Logger

from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.CuraStackBuilder import CuraStackBuilder

import UM.i18n
catalog = UM.i18n.i18nCatalog("cura")


##  This action allows for certain settings that are "machine only") to be modified.
#   It automatically detects machine definitions that it knows how to change and attaches itself to those.
class MachineSettingsAction(MachineAction):
    def __init__(self, parent = None):
        super().__init__("MachineSettingsAction", catalog.i18nc("@action", "Machine Settings"))
        self._qml_url = "MachineSettingsAction.qml"

        self._global_container_stack = None

        from cura.Settings.CuraContainerStack import _ContainerIndexes
        self._container_index = _ContainerIndexes.DefinitionChanges

        self._container_registry = ContainerRegistry.getInstance()
        self._container_registry.containerAdded.connect(self._onContainerAdded)
        self._container_registry.containerRemoved.connect(self._onContainerRemoved)
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerChanged)

        self._empty_container = self._container_registry.getEmptyInstanceContainer()

        self._backend = Application.getInstance().getBackend()

    def _onContainerAdded(self, container):
        # Add this action as a supported action to all machine definitions
        if isinstance(container, DefinitionContainer) and container.getMetaDataEntry("type") == "machine":
            Application.getInstance().getMachineActionManager().addSupportedAction(container.getId(), self.getKey())

    def _onContainerRemoved(self, container):
        # Remove definition_changes containers when a stack is removed
        if container.getMetaDataEntry("type") in ["machine", "extruder_train"]:
            definition_changes_container = container.definitionChanges
            if definition_changes_container == self._empty_container:
                return

            self._container_registry.removeContainer(definition_changes_container.getId())

    def _reset(self):
        if not self._global_container_stack:
            return

        # Make sure there is a definition_changes container to store the machine settings
        definition_changes_container = self._global_container_stack.definitionChanges
        if definition_changes_container == self._empty_container:
            definition_changes_container = CuraStackBuilder.createDefinitionChangesContainer(
                self._global_container_stack, self._global_container_stack.getName() + "_settings")

        # Notify the UI in which container to store the machine settings data
        from cura.Settings.CuraContainerStack import CuraContainerStack, _ContainerIndexes

        container_index = _ContainerIndexes.DefinitionChanges
        if container_index != self._container_index:
            self._container_index = container_index
            self.containerIndexChanged.emit()

        # Disable auto-slicing while the MachineAction is showing
        if self._backend:  # This sometimes triggers before backend is loaded.
            self._backend.disableTimer()

    @pyqtSlot()
    def onFinishAction(self):
        # Restore autoslicing when the machineaction is dismissed
        if self._backend and self._backend.determineAutoSlicing():
            self._backend.tickle()

    containerIndexChanged = pyqtSignal()

    @pyqtProperty(int, notify = containerIndexChanged)
    def containerIndex(self):
        return self._container_index

    def _onGlobalContainerChanged(self):
        self._global_container_stack = Application.getInstance().getGlobalContainerStack()

        # This additional emit is needed because we cannot connect a UM.Signal directly to a pyqtSignal
        self.globalContainerChanged.emit()

    globalContainerChanged = pyqtSignal()

    @pyqtProperty(int, notify = globalContainerChanged)
    def definedExtruderCount(self):
        if not self._global_container_stack:
            return 0

        return len(self._global_container_stack.getMetaDataEntry("machine_extruder_trains"))

    @pyqtSlot(int)
    def setMachineExtruderCount(self, extruder_count):
        # Note: this method was in this class before, but since it's quite generic and other plugins also need it
        # it was moved to the machine manager instead. Now this method just calls the machine manager.
        Application.getInstance().getMachineManager().setActiveMachineExtruderCount(extruder_count)

    @pyqtSlot()
    def forceUpdate(self):
        # Force rebuilding the build volume by reloading the global container stack.
        # This is a bit of a hack, but it seems quick enough.
        Application.getInstance().globalContainerStackChanged.emit()

    @pyqtSlot()
    def updateHasMaterialsMetadata(self):
        # Updates the has_materials metadata flag after switching gcode flavor
        if not self._global_container_stack:
            return

        definition = self._global_container_stack.getBottom()
        if definition.getProperty("machine_gcode_flavor", "value") != "UltiGCode" or definition.getMetaDataEntry("has_materials", False):
            # In other words: only continue for the UM2 (extended), but not for the UM2+
            return

        stacks = ExtruderManager.getInstance().getExtruderStacks()
        has_materials = self._global_container_stack.getProperty("machine_gcode_flavor", "value") != "UltiGCode"

        if has_materials:
            if "has_materials" in self._global_container_stack.getMetaData():
                self._global_container_stack.setMetaDataEntry("has_materials", True)
            else:
                self._global_container_stack.addMetaDataEntry("has_materials", True)

            # Set the material container for each extruder to a sane default
            for stack in stacks:
                material_container = stack.material
                if material_container == self._empty_container:
                    machine_approximate_diameter = str(round(self._global_container_stack.getProperty("material_diameter", "value")))
                    search_criteria = { "type": "material", "definition": "fdmprinter", "id": self._global_container_stack.getMetaDataEntry("preferred_material"), "approximate_diameter": machine_approximate_diameter}
                    materials = self._container_registry.findInstanceContainers(**search_criteria)
                    if materials:
                        stack.material = materials[0]
        else:
            # The metadata entry is stored in an ini, and ini files are parsed as strings only.
            # Because any non-empty string evaluates to a boolean True, we have to remove the entry to make it False.
            if "has_materials" in self._global_container_stack.getMetaData():
                self._global_container_stack.removeMetaDataEntry("has_materials")

            for stack in stacks:
                stack.material = ContainerRegistry.getInstance().getEmptyInstanceContainer()

        Application.getInstance().globalContainerStackChanged.emit()

    @pyqtSlot(int)
    def updateMaterialForDiameter(self, extruder_position: int):
        # Updates the material container to a material that matches the material diameter set for the printer
        Application.getInstance().getExtruderManager().updateMaterialForDiameter(extruder_position)
