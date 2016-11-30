# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot

from cura.MachineAction import MachineAction

import UM.Application
import UM.Settings.InstanceContainer
import UM.Settings.DefinitionContainer
import UM.Settings.ContainerRegistry
import UM.Logger

import UM.i18n
catalog = UM.i18n.i18nCatalog("cura")

class MachineSettingsAction(MachineAction):
    def __init__(self, parent = None):
        super().__init__("MachineSettingsAction", catalog.i18nc("@action", "Machine Settings"))
        self._qml_url = "MachineSettingsAction.qml"

        self._container_index = 0

        self._container_registry = UM.Settings.ContainerRegistry.getInstance()
        self._container_registry.containerAdded.connect(self._onContainerAdded)

    def _reset(self):
        global_container_stack = UM.Application.getInstance().getGlobalContainerStack()
        if not global_container_stack:
            return

        # Make sure there is a definition_changes container to store the machine settings
        definition_changes_container = global_container_stack.findContainer({"type": "definition_changes"})
        if not definition_changes_container:
            definition_changes_container = self._createDefinitionChangesContainer(global_container_stack)

        # Notify the UI in which container to store the machine settings data
        container_index = global_container_stack.getContainerIndex(definition_changes_container)
        if container_index != self._container_index:
            self._container_index = container_index
            self.containerIndexChanged.emit()

    def _createDefinitionChangesContainer(self, global_container_stack, container_index = None):
        definition_changes_container = UM.Settings.InstanceContainer(global_container_stack.getName() + "_settings")
        definition = global_container_stack.getBottom()
        definition_changes_container.setDefinition(definition)
        definition_changes_container.addMetaDataEntry("type", "definition_changes")

        self._container_registry.addContainer(definition_changes_container)
        # Insert definition_changes between the definition and the variant
        global_container_stack.insertContainer(-1, definition_changes_container)

        return definition_changes_container

    containerIndexChanged = pyqtSignal()

    @pyqtProperty(int, notify = containerIndexChanged)
    def containerIndex(self):
        return self._container_index

    def _onContainerAdded(self, container):
        # Add this action as a supported action to all machine definitions
        if isinstance(container, UM.Settings.DefinitionContainer) and container.getMetaDataEntry("type") == "machine":
            if container.getProperty("machine_extruder_count", "value") > 1:
                # Multiextruder printers are not currently supported
                UM.Logger.log("d", "Not attaching MachineSettingsAction to %s; Multi-extrusion printers are not supported", container.getId())
                return

            UM.Application.getInstance().getMachineActionManager().addSupportedAction(container.getId(), self.getKey())

    @pyqtSlot()
    def forceUpdate(self):
        # Force rebuilding the build volume by reloading the global container stack.
        # This is a bit of a hack, but it seems quick enough.
        UM.Application.getInstance().globalContainerStackChanged.emit()

    @pyqtSlot()
    def updateHasMaterialsMetadata(self):
        # Updates the has_materials metadata flag after switching gcode flavor
        global_container_stack = UM.Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            definition = global_container_stack.getBottom()
            if definition.getProperty("machine_gcode_flavor", "value") == "UltiGCode" and not definition.getMetaDataEntry("has_materials", False):
                has_materials = global_container_stack.getProperty("machine_gcode_flavor", "value") != "UltiGCode"

                material_container = global_container_stack.findContainer({"type": "material"})
                material_index = global_container_stack.getContainerIndex(material_container)

                if has_materials:
                    if "has_materials" in global_container_stack.getMetaData():
                        global_container_stack.setMetaDataEntry("has_materials", True)
                    else:
                        global_container_stack.addMetaDataEntry("has_materials", True)

                    # Set the material container to a sane default
                    if material_container.getId() == "empty_material":
                        search_criteria = { "type": "material", "definition": "fdmprinter", "id": "*pla*" }
                        containers = self._container_registry.findInstanceContainers(**search_criteria)
                        if containers:
                            global_container_stack.replaceContainer(material_index, containers[0])
                else:
                    # The metadata entry is stored in an ini, and ini files are parsed as strings only.
                    # Because any non-empty string evaluates to a boolean True, we have to remove the entry to make it False.
                    if "has_materials" in global_container_stack.getMetaData():
                        global_container_stack.removeMetaDataEntry("has_materials")

                    empty_material = self._container_registry.findInstanceContainers(id = "empty_material")[0]
                    global_container_stack.replaceContainer(material_index, empty_material)

                UM.Application.getInstance().globalContainerStackChanged.emit()