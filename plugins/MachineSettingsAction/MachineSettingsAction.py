# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import pyqtSlot

from cura.MachineAction import MachineAction
import cura.Settings.CuraContainerRegistry

import UM.Application
import UM.Settings.InstanceContainer
import UM.Settings.DefinitionContainer
import UM.Logger

import UM.i18n
catalog = UM.i18n.i18nCatalog("cura")

class MachineSettingsAction(MachineAction):
    def __init__(self, parent = None):
        super().__init__("MachineSettingsAction", catalog.i18nc("@action", "Machine Settings"))
        self._qml_url = "MachineSettingsAction.qml"

        cura.Settings.CuraContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

    def _reset(self):
        global_container_stack = UM.Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            variant = global_container_stack.findContainer({"type": "variant"})
            if variant and variant.getId() == "empty_variant":
                variant_index = global_container_stack.getContainerIndex(variant)
                self._createVariant(global_container_stack, variant_index)

    def _createVariant(self, global_container_stack, variant_index):
        # Create and switch to a variant to store the settings in
        new_variant = UM.Settings.InstanceContainer(global_container_stack.getName() + "_variant")
        new_variant.addMetaDataEntry("type", "variant")
        new_variant.setDefinition(global_container_stack.getBottom())
        UM.Settings.ContainerRegistry.getInstance().addContainer(new_variant)
        global_container_stack.replaceContainer(variant_index, new_variant)

    def _onContainerAdded(self, container):
        # Add this action as a supported action to all machine definitions
        if isinstance(container, UM.Settings.DefinitionContainer) and container.getMetaDataEntry("type") == "machine":
            if container.getProperty("machine_extruder_count", "value") > 1:
                # Multiextruder printers are not currently supported
                UM.Logger.log("d", "Not attaching MachineSettingsAction to %s; Multi-extrusion printers are not supported", container.getId())
                return
            if container.getMetaDataEntry("has_variants", False):
                # Machines that use variants are not currently supported
                UM.Logger.log("d", "Not attaching MachineSettingsAction to %s; Machines that use variants are not supported", container.getId())
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
                        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(**search_criteria)
                        if containers:
                            global_container_stack.replaceContainer(material_index, containers[0])
                else:
                    # The metadata entry is stored in an ini, and ini files are parsed as strings only.
                    # Because any non-empty string evaluates to a boolean True, we have to remove the entry to make it False.
                    if "has_materials" in global_container_stack.getMetaData():
                        global_container_stack.removeMetaDataEntry("has_materials")

                    empty_material = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = "empty_material")[0]
                    global_container_stack.replaceContainer(material_index, empty_material)

                UM.Application.getInstance().globalContainerStackChanged.emit()