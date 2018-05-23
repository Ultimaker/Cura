# Copyright (c) 2018 fieldOfView
# The Blackbelt plugin is released under the terms of the LGPLv3 or higher.

from UM.Extension import Extension
from UM.Application import Application
from UM.Preferences import Preferences
from UM.PluginRegistry import PluginRegistry
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Logger import Logger
from UM.Version import Version

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("BlackBeltPlugin")

from . import BlackBeltDecorator
from . import BlackBeltSingleton
from . import BuildVolumePatches
from . import CuraEngineBackendPatches
from . import MaterialManagerPatches

from PyQt5.QtQml import qmlRegisterSingletonType

import math
import os.path
import re

class BlackBeltPlugin(Extension):
    def __init__(self):
        super().__init__()
        plugin_path = os.path.dirname(os.path.abspath(__file__))

        self._application = Application.getInstance()

        self._build_volume_patches = None
        self._cura_engine_backend_patches = None
        self._material_manager_patches = None

        self._global_container_stack = None
        self._application.globalContainerStackChanged.connect(self._onGlobalContainerStackChanged)
        self._onGlobalContainerStackChanged()

        self._scene_root = self._application.getController().getScene().getRoot()
        self._scene_root.addDecorator(BlackBeltDecorator.BlackBeltDecorator())

        qmlRegisterSingletonType(BlackBeltSingleton.BlackBeltSingleton, "Cura", 1, 0, "BlackBeltPlugin", BlackBeltSingleton.BlackBeltSingleton.getInstance)
        self._application.getOutputDeviceManager().writeStarted.connect(self._filterGcode)

        self._application.pluginsLoaded.connect(self._onPluginsLoaded)

        self._force_visibility_update = False

        # disable update checker plugin (because it checks the wrong version)
        plugin_registry = PluginRegistry.getInstance()
        if "UpdateChecker" not in plugin_registry._disabled_plugins:
            Logger.log("d", "Disabling Update Checker plugin")
            plugin_registry._disabled_plugins.append("UpdateChecker")

    def _onPluginsLoaded(self):
        # make sure the we connect to engineCreatedSignal later than PrepareStage does, so we can substitute our own sidebar
        self._application.engineCreatedSignal.connect(self._onEngineCreated)

        # Hide nozzle in simulation view
        self._application.getController().activeViewChanged.connect(self._onActiveViewChanged)

        # Handle default setting visibility
        Preferences.getInstance().preferenceChanged.connect(self._onPreferencesChanged)
        if self._application.getVersion() != "master" and Version(Preferences.getInstance().getValue("general/latest_version_changelog_shown")) < Version("3.2.1"):
            self._force_visibility_update = True

        # Disable USB printing output device
        Application.getInstance().getOutputDeviceManager().outputDevicesChanged.connect(self._onOutputDevicesChanged)

    def _onEngineCreated(self):
        self._application.getMachineManager().activeVariantChanged.connect(self._onActiveVariantChanged)

        # Set window title
        self._application._engine.rootObjects()[0].setTitle(i18n_catalog.i18nc("@title:window","BlackBelt Cura"))

        # Substitute our own sidebar
        sidebar_component_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sidebar", "Sidebar.qml")
        prepare_stage = Application.getInstance().getController().getStage("PrepareStage")
        prepare_stage.addDisplayComponent("sidebar", sidebar_component_path)

        # Apply patches
        self._build_volume_patches = BuildVolumePatches.BuildVolumePatches(self._application.getBuildVolume())
        self._cura_engine_backend_patches = CuraEngineBackendPatches.CuraEngineBackendPatches(self._application.getBackend())
        self._material_manager_patches = MaterialManagerPatches.MaterialManagerPatches(self._application.getMaterialManager())

        self._application.getBackend().slicingStarted.connect(self._onSlicingStarted)

        self._fixVisibilityPreferences(forced = self._force_visibility_update)
        self._force_visibility_update = False

    def _onOutputDevicesChanged(self):
        if not self._global_container_stack:
            return

        definition_container = self._global_container_stack.getBottom()
        if definition_container.getId() != "blackbelt":
            return

        # HACK: Remove USB output device for blackbelt printers
        devices_to_remove = []
        output_device_manager = Application.getInstance().getOutputDeviceManager()
        for output_device in output_device_manager.getOutputDevices():
            if "USBPrinterOutputDevice" in str(output_device):
                devices_to_remove.append(output_device.getId())

        for output_device in devices_to_remove:
            Logger.log("d", "Removing USB printer output device %s from printer %s" % (output_device, self._global_container_stack.getId()))
            output_device_manager.removeOutputDevice(output_device)

    def _onGlobalContainerStackChanged(self):
        if self._global_container_stack:
            self._global_container_stack.propertyChanged.disconnect(self._onSettingValueChanged)
        self._global_container_stack = self._application.getGlobalContainerStack()
        if self._global_container_stack:
            self._global_container_stack.propertyChanged.connect(self._onSettingValueChanged)

            # HACK: Move blackbelt_settings to the top of the list of settings
            definition_container = self._global_container_stack.getBottom()
            if definition_container._definitions[len(definition_container._definitions) -1].key == "blackbelt_settings":
                definition_container._definitions.insert(0, definition_container._definitions.pop(len(definition_container._definitions) -1))

            # HOTFIXES for Blackbelt stacks
            if definition_container.getId() == "blackbelt" and self._application._machine_manager:
                extruder_stack = self._application.getMachineManager()._active_container_stack

                if extruder_stack:
                    # Make sure the extruder material diameter matches the global material diameter
                    material_diameter = self._global_container_stack.getProperty("material_diameter", "value")
                    definition_changes_container = extruder_stack.definitionChanges
                    if "material_diameter" not in definition_changes_container.getAllKeys():
                        # Make sure there is a definition_changes container to store the machine settings
                        if definition_changes_container == ContainerRegistry.getInstance().getEmptyInstanceContainer():
                            definition_changes_container = CuraStackBuilder.createDefinitionChangesContainer(
                                extruder_stack, extruder_stack.getId() + "_settings")

                        definition_changes_container.setProperty("material_diameter", "value", material_diameter)

                    # Make sure approximate diameters are in check
                    approximate_diameter = str(round(material_diameter))
                    if extruder_stack.getMetaDataEntry("approximate_diameter") != approximate_diameter:
                        extruder_stack.addMetaDataEntry("approximate_diameter", approximate_diameter)
                    if self._global_container_stack.getMetaDataEntry("approximate_diameter") != approximate_diameter:
                        self._global_container_stack.addMetaDataEntry("approximate_diameter", approximate_diameter)

                    # Make sure the extruder quality is a blackbelt quality profile
                    if extruder_stack.quality.getDefinition().getId() != "blackbelt":
                        blackbelt_normal_quality = ContainerRegistry.getInstance().findContainers(id = "blackbelt_normal")[0]
                        extruder_stack.setQuality(blackbelt_normal_quality)
                        self._global_container_stack.setQuality(blackbelt_normal_quality)

        self._adjustLayerViewNozzle()

    def _onSlicingStarted(self):
        self._scene_root.callDecoration("calculateTransformData")

    def _onActiveVariantChanged(self):
        # HOTFIX: copy extruder variant to global stack
        if not self._global_container_stack:
            return
        extruder_stack = self._application.getMachineManager()._active_container_stack
        if not extruder_stack:
            return

        definition_container = self._global_container_stack.getBottom()
        if definition_container.getId() != "blackbelt":
            return

        if self._global_container_stack.variant != extruder_stack.variant:
            self._global_container_stack.setVariant(extruder_stack.variant)
            pass

    def _onSettingValueChanged(self, key, property_name):
        if property_name != "value" or not self._global_container_stack.hasProperty("blackbelt_gantry_angle", "value"):
            return

        elif key == "blackbelt_gantry_angle":
            # Setting the gantry angle changes the build volume.
            # Force rebuilding the build volume by reloading the global container stack.
            # This is a bit of a hack, but it seems quick enough.
            self._application.globalContainerStackChanged.emit()

    def _onPreferencesChanged(self, preference):
        if preference == "general/visible_settings":
            self._fixVisibilityPreferences()

    def _fixVisibilityPreferences(self, forced = False):
        # Fix setting visibility preferences
        preferences = Preferences.getInstance()
        visible_settings = preferences.getValue("general/visible_settings")
        if not visible_settings:
            # Wait until the default visible settings have been set
            return

        if "blackbelt_settings" in visible_settings and not forced:
            return
        visible_settings_changed = False
        default_visible_settings = [
            "blackbelt_settings", "blackbelt_z_offset_gap", "blackbelt_secondary_fans_enabled", "blackbelt_belt_wall_enabled", "blackbelt_belt_wall_speed", "blackbelt_repetitions", "blackbelt_repetitions_distance",
            "wall_line_count", "top_layers", "bottom_layers", "top_bottom_pattern", "fill_perimeter_gaps", "xy_offset", "z_seam_type", "z_seam_x", "z_seam_y", "z_seam_corner",
            "infill_line_distance", "min_infill_area", "retraction_amount", "retraction_speed", "retraction_extra_prime_amount", "speed_infill", "speed_wall_0", "speed_slowdown_layers",
            "cool_fan_speed", "cool_fan_full_at_height", "cool_fan_full_at_layer", "cool_min_layer_time", "meshfix_union_all", "meshfix_union_all_remove_holes", "meshfix_extensive_stiching",
            "meshfix_keep_open_polygons", "multiple_mesh_overlap", "carve_multiple_volumes", "magic_spiralize", "coasting_enable"
        ]
        for key in default_visible_settings:
            if key not in visible_settings:
                visible_settings += ";%s" % key
                visible_settings_changed = True

        if not visible_settings_changed:
            return

        preferences.setValue("general/visible_settings", visible_settings)


    def _onActiveViewChanged(self):
        self._adjustLayerViewNozzle()

    def _adjustLayerViewNozzle(self):
        global_stack = Application.getInstance().getGlobalContainerStack()
        if not global_stack:
            return

        view = self._application.getController().getActiveView()
        if view and view.getPluginId() == "SimulationView":
            gantry_angle = global_stack.getProperty("blackbelt_gantry_angle", "value")
            if gantry_angle and float(gantry_angle) > 0:
                view.getNozzleNode().setParent(None)
            else:
                view.getNozzleNode().setParent(self._application.getController().getScene().getRoot())


    def _filterGcode(self, output_device):
        global_stack = Application.getInstance().getGlobalContainerStack()

        enable_secondary_fans = global_stack.extruders["0"].getProperty("blackbelt_secondary_fans_enabled", "value")
        repetitions = global_stack.getProperty("blackbelt_repetitions", "value") or 1
        if not (enable_secondary_fans or repetitions > 1):
            return

        repetitions_distance = global_stack.getProperty("blackbelt_repetitions_distance", "value")
        repetitions_gcode = global_stack.getProperty("blackbelt_repetitions_gcode", "value")

        scene = Application.getInstance().getController().getScene()
        gcode_dict = getattr(scene, "gcode_dict", {})
        if not gcode_dict: # this also checks for an empty dict
            Logger.log("w", "Scene has no gcode to process")
            return

        dict_changed = False

        for plate_id in gcode_dict:
            gcode_list = gcode_dict[plate_id]
            if gcode_list:
                if ";BLACKBELTPROCESSED" not in gcode_list[0]:
                    # secondary fans should do the same as print cooling fans
                    if enable_secondary_fans:
                        search_regex = re.compile(r"M106 S(\d*\.?\d*)")
                        replace_pattern = r"M106 P1 S\1\nM106 S\1"

                        for layer_number, layer in enumerate(gcode_list):
                            gcode_list[layer_number] = re.sub(search_regex, replace_pattern, layer) #Replace all.

                    # make repetitions
                    if repetitions > 1 and len(gcode_list) > 2:
                        # gcode_list[0]: curaengine header
                        # gcode_list[1]: start gcode
                        # gcode_list[2] - gcode_list[n-1]: layers
                        # gcode_list[n]: end gcode
                        layers = gcode_list[2:-1]
                        layers.append(repetitions_gcode.replace("{blackbelt_repetitions_distance}", str(repetitions_distance)))
                        gcode_list[2:-1] = (layers * int(repetitions))[0:-1]

                    gcode_list[0] += ";BLACKBELTPROCESSED\n"
                    gcode_dict[plate_id] = gcode_list
                    dict_changed = True
                else:
                    Logger.log("e", "Already post processed")

        if dict_changed:
            setattr(scene, "gcode_dict", gcode_dict)
