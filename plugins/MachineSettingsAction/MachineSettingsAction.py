# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, pyqtSignal
from UM.FlameProfiler import pyqtSlot

from cura.MachineAction import MachineAction

from UM.Application import Application
from UM.Preferences import Preferences
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Logger import Logger

from cura.CuraApplication import CuraApplication
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
        self._container_index = 0

        self._container_registry = ContainerRegistry.getInstance()
        self._container_registry.containerAdded.connect(self._onContainerAdded)
        self._container_registry.containerRemoved.connect(self._onContainerRemoved)
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerChanged)
        ExtruderManager.getInstance().activeExtruderChanged.connect(self._onActiveExtruderStackChanged)

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
        container_index = self._global_container_stack.getContainerIndex(definition_changes_container)
        if container_index != self._container_index:
            self._container_index = container_index
            self.containerIndexChanged.emit()

        # Disable auto-slicing while the MachineAction is showing
        if self._backend:  # This sometimes triggers before backend is loaded.
            self._backend.disableTimer()

    @pyqtSlot()
    def onFinishAction(self):
        # Restore autoslicing when the machineaction is dismissed
        if self._backend.determineAutoSlicing():
            self._backend.tickle()

    def _onActiveExtruderStackChanged(self):
        extruder_container_stack = ExtruderManager.getInstance().getActiveExtruderStack()
        if not self._global_container_stack or not extruder_container_stack:
            return

        # Make sure there is a definition_changes container to store the machine settings
        definition_changes_container = extruder_container_stack.definitionChanges
        if definition_changes_container == self._empty_container:
            definition_changes_container = CuraStackBuilder.createDefinitionChangesContainer(
                extruder_container_stack, extruder_container_stack.getId() + "_settings")

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
        machine_manager = Application.getInstance().getMachineManager()
        extruder_manager = ExtruderManager.getInstance()

        definition_changes_container = self._global_container_stack.definitionChanges
        if not self._global_container_stack or definition_changes_container == self._empty_container:
            return

        previous_extruder_count = self._global_container_stack.getProperty("machine_extruder_count", "value")
        if extruder_count == previous_extruder_count:
            return

        extruder_material_id = None
        extruder_variant_id = None
        if extruder_count == 1:
            # Get the material and variant of the first extruder before setting the number extruders to 1
            if machine_manager.hasMaterials:
                extruder_material_id = machine_manager.allActiveMaterialIds[extruder_manager.extruderIds["0"]]
            if machine_manager.hasVariants:
                extruder_variant_id = machine_manager.allActiveVariantIds[extruder_manager.extruderIds["0"]]

            # Copy any settable_per_extruder setting value from the extruders to the global stack
            extruder_stacks = ExtruderManager.getInstance().getActiveExtruderStacks()
            extruder_stacks.reverse() # make sure the first extruder is done last, so its settings override any higher extruder settings

            global_user_container = self._global_container_stack.getTop()
            for extruder_stack in extruder_stacks:
                extruder_index = extruder_stack.getMetaDataEntry("position")
                extruder_user_container = extruder_stack.getTop()
                for setting_instance in extruder_user_container.findInstances():
                    setting_key = setting_instance.definition.key
                    settable_per_extruder = self._global_container_stack.getProperty(setting_key, "settable_per_extruder")
                    if settable_per_extruder:
                        limit_to_extruder = self._global_container_stack.getProperty(setting_key, "limit_to_extruder")

                        if limit_to_extruder == "-1" or limit_to_extruder == extruder_index:
                            global_user_container.setProperty(setting_key, "value", extruder_user_container.getProperty(setting_key, "value"))
                            extruder_user_container.removeInstance(setting_key)

        # Check to see if any features are set to print with an extruder that will no longer exist
        for setting_key in ["adhesion_extruder_nr", "support_extruder_nr", "support_extruder_nr_layer_0", "support_infill_extruder_nr", "support_interface_extruder_nr"]:
            if int(self._global_container_stack.getProperty(setting_key, "value")) > extruder_count - 1:
                Logger.log("i", "Lowering %s setting to match number of extruders", setting_key)
                self._global_container_stack.getTop().setProperty(setting_key, "value", extruder_count - 1)

        # Check to see if any objects are set to print with an extruder that will no longer exist
        root_node = Application.getInstance().getController().getScene().getRoot()
        for node in DepthFirstIterator(root_node):
            if node.getMeshData():
                extruder_nr = node.callDecoration("getActiveExtruderPosition")

                if extruder_nr is not None and int(extruder_nr) > extruder_count - 1:
                    node.callDecoration("setActiveExtruder", extruder_manager.getExtruderStack(extruder_count - 1).getId())

        definition_changes_container.setProperty("machine_extruder_count", "value", extruder_count)

        if extruder_count > 1:
            # Multiextrusion

            # Make sure one of the extruder stacks is active
            if extruder_manager.activeExtruderIndex == -1:
                extruder_manager.setActiveExtruderIndex(0)

            # Move settable_per_extruder values out of the global container
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
        else:
            # Single extrusion

            # Make sure the machine stack is active
            if extruder_manager.activeExtruderIndex > -1:
                extruder_manager.setActiveExtruderIndex(-1)

            # Restore material and variant on global stack
            # MachineManager._onGlobalContainerChanged removes the global material and variant of multiextruder machines
            if extruder_material_id or extruder_variant_id:
                # Prevent the DiscardOrKeepProfileChangesDialog from popping up (twice) if there are user changes
                # The dialog is not relevant here, since we're restoring the previous situation as good as possible
                preferences = Preferences.getInstance()
                choice_on_profile_override = preferences.getValue("cura/choice_on_profile_override")
                preferences.setValue("cura/choice_on_profile_override", "always_keep")

                if extruder_material_id:
                    machine_manager.setActiveMaterial(extruder_material_id)
                if extruder_variant_id:
                    machine_manager.setActiveVariant(extruder_variant_id)

                preferences.setValue("cura/choice_on_profile_override", choice_on_profile_override)

        self.forceUpdate()


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

        has_materials = self._global_container_stack.getProperty("machine_gcode_flavor", "value") != "UltiGCode"

        material_container = self._global_container_stack.material

        if has_materials:
            if "has_materials" in self._global_container_stack.getMetaData():
                self._global_container_stack.setMetaDataEntry("has_materials", True)
            else:
                self._global_container_stack.addMetaDataEntry("has_materials", True)

            # Set the material container to a sane default
            if material_container == self._empty_container:
                search_criteria = { "type": "material", "definition": "fdmprinter", "id": self._global_container_stack.getMetaDataEntry("preferred_material")}
                materials = self._container_registry.findInstanceContainers(**search_criteria)
                if materials:
                    self._global_container_stack.material = materials[0]
        else:
            # The metadata entry is stored in an ini, and ini files are parsed as strings only.
            # Because any non-empty string evaluates to a boolean True, we have to remove the entry to make it False.
            if "has_materials" in self._global_container_stack.getMetaData():
                self._global_container_stack.removeMetaDataEntry("has_materials")

            self._global_container_stack.material = ContainerRegistry.getInstance().getEmptyInstanceContainer()

        Application.getInstance().globalContainerStackChanged.emit()

    @pyqtSlot()
    def updateMaterialForDiameter(self):
        # Updates the material container to a material that matches the material diameter set for the printer
        if not self._global_container_stack:
            return

        if not self._global_container_stack.getMetaDataEntry("has_materials", False):
            return

        machine_extruder_count = self._global_container_stack.getProperty("machine_extruder_count", "value")
        if machine_extruder_count > 1:
            material = ExtruderManager.getInstance().getActiveExtruderStack().material
        else:
            material = self._global_container_stack.material
        material_diameter = material.getProperty("material_diameter", "value")
        if not material_diameter: # in case of "empty" material
            material_diameter = 0
        material_approximate_diameter = str(round(material_diameter))

        definition_changes = self._global_container_stack.definitionChanges
        machine_diameter = definition_changes.getProperty("material_diameter", "value")
        if not machine_diameter:
            machine_diameter = self._global_container_stack.definition.getProperty("material_diameter", "value")
        machine_approximate_diameter = str(round(machine_diameter))

        if material_approximate_diameter != machine_approximate_diameter:
            Logger.log("i", "The the currently active material(s) do not match the diameter set for the printer. Finding alternatives.")

            if machine_extruder_count > 1:
                stacks = ExtruderManager.getInstance().getExtruderStacks()
            else:
                stacks = [self._global_container_stack]

            if self._global_container_stack.getMetaDataEntry("has_machine_materials", False):
                materials_definition = self._global_container_stack.definition.getId()
                has_material_variants = self._global_container_stack.getMetaDataEntry("has_variants", False)
            else:
                materials_definition = "fdmprinter"
                has_material_variants = False

            for stack in stacks:
                old_material = stack.material
                search_criteria = {
                    "type": "material",
                    "approximate_diameter": machine_approximate_diameter,
                    "material": old_material.getMetaDataEntry("material", "value"),
                    "supplier": old_material.getMetaDataEntry("supplier", "value"),
                    "color_name": old_material.getMetaDataEntry("color_name", "value"),
                    "definition": materials_definition
                }
                if has_material_variants:
                    search_criteria["variant"] = stack.variant.getId()

                if old_material == self._empty_container:
                    search_criteria.pop("material", None)
                    search_criteria.pop("supplier", None)
                    search_criteria.pop("definition", None)
                    search_criteria["id"] = stack.getMetaDataEntry("preferred_material")

                materials = self._container_registry.findInstanceContainers(**search_criteria)
                if not materials:
                    # Same material with new diameter is not found, search for generic version of the same material type
                    search_criteria.pop("supplier", None)
                    search_criteria["color_name"] = "Generic"
                    materials = self._container_registry.findInstanceContainers(**search_criteria)
                if not materials:
                    # Generic material with new diameter is not found, search for preferred material
                    search_criteria.pop("color_name", None)
                    search_criteria.pop("material", None)
                    search_criteria["id"] = stack.getMetaDataEntry("preferred_material")
                    materials = self._container_registry.findInstanceContainers(**search_criteria)
                if not materials:
                    # Preferrd material with new diameter is not found, search for any material
                    search_criteria.pop("id", None)
                    materials = self._container_registry.findInstanceContainers(**search_criteria)
                if not materials:
                    # Just use empty material as a final fallback
                    materials = [self._empty_container]

                Logger.log("i", "Selecting new material: %s" % materials[0].getId())

                stack.material = materials[0]
