# Copyright (c) 2018 fieldOfView
# The Blackbelt plugin is released under the terms of the LGPLv3 or higher.

from UM.Extension import Extension
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.SettingFunction import SettingFunction
from UM.Logger import Logger
from UM.Version import Version

from cura.Settings.CuraContainerStack import _ContainerIndexes as ContainerIndexes
from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("BlackBeltPlugin")

from . import BlackBeltDecorator
from . import BlackBeltSingleton

from . import CuraApplicationPatches
from . import PatchedCuraActions
from . import BuildVolumePatches
from . import CuraEngineBackendPatches
from . import PrintInformationPatches
from . import PatchedMaterialManager
from . import USBPrinterOutputDevicePatches

from PyQt5.QtQml import qmlRegisterSingletonType

import math
import os.path
import re
import json

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
        preferences = self._application.getPreferences()
        preferences.preferenceChanged.connect(self._onPreferencesChanged)
        if self._configurationNeedsUpdates():
            Logger.log("d", "BlackBelt-specific updates to configuration are needed")
            self._force_visibility_update = True
            preferences.addPreference("general/theme", self._application.default_theme)
            preferences.setValue("general/theme", "blackbelt")
            preferences.addPreference("cura/active_setting_visibility_preset", "basic")
            preferences.setValue("cura/active_setting_visibility_preset", "blackbelt")

        # Disable USB printing output device
        self._application.getOutputDeviceManager().outputDevicesChanged.connect(self._onOutputDevicesChanged)

    def _configurationNeedsUpdates(self):
        preferences = self._application.getPreferences()
        preferences.addPreference("blackbelt/setting_version", "0.0.0")

        # Get version information from plugin.json
        plugin_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugin.json")
        try:
            with open(plugin_file_path) as plugin_file:
                plugin_info = json.load(plugin_file)
                plugin_version = plugin_info["version"]
        except:
            Logger.log("w", "Could not determine BlackBelt plugin version")
            return False

        if Version(preferences.getValue("blackbelt/setting_version")) < Version(plugin_version):
            Logger.log("d", "Setting BlackBelt version nr to %s" % plugin_version)
            preferences.setValue("blackbelt/setting_version", plugin_version)
            return True

        return False


    def _onEngineCreated(self):
        self._application.getMachineManager().activeVariantChanged.connect(self._onActiveVariantChanged)
        self._application.getMachineManager().activeQualityChanged.connect(self._onActiveQualityChanged)

        # Set window title
        self._application._qml_engine.rootObjects()[0].setTitle(i18n_catalog.i18nc("@title:window","BlackBelt Cura"))

        # Substitute our own sidebar
        sidebar_component_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sidebar", "PrepareSidebar.qml")
        prepare_stage = self._application.getController().getStage("PrepareStage")
        prepare_stage.addDisplayComponent("sidebar", sidebar_component_path)

        # Apply patches
        self._cura_application_patches = CuraApplicationPatches.CuraApplicationPatches(self._application)
        self._build_volume_patches = BuildVolumePatches.BuildVolumePatches(self._application.getBuildVolume())
        self._cura_engine_backend_patches = CuraEngineBackendPatches.CuraEngineBackendPatches(self._application.getBackend())
        self._print_information_patches = PrintInformationPatches.PrintInformationPatches(self._application.getPrintInformation())
        self._output_device_patches = {}

        self._application._cura_actions = PatchedCuraActions.PatchedCuraActions()
        self._application._qml_engine.rootContext().setContextProperty("CuraActions", self._application._cura_actions)

        container_registry = ContainerRegistry.getInstance()
        self._application._material_manager = PatchedMaterialManager.PatchedMaterialManager(container_registry, self._application)
        self._application._material_manager.initialize()

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
        output_device_manager = self._application.getOutputDeviceManager()
        for output_device in output_device_manager.getOutputDevices():
            if "USBPrinterOutputDevice" in str(output_device):
                self._output_device_patches[output_device] = USBPrinterOutputDevicePatches.USBPrinterOutputDevicePatches(output_device)

    def _onGlobalContainerStackChanged(self):
        if self._global_container_stack:
            self._global_container_stack.propertyChanged.disconnect(self._onSettingValueChanged)

        self._global_container_stack = self._application.getGlobalContainerStack()

        if self._global_container_stack:
            self._global_container_stack.propertyChanged.connect(self._onSettingValueChanged)

            # HACK: Move blackbelt_settings to the top of the list of settings
            definition_container = self._global_container_stack.getBottom()
            if definition_container._definitions[0].key != "blackbelt_settings":
                for index, definition in enumerate(definition_container._definitions):
                    if definition.key == "blackbelt_settings":
                        definition_container._definitions.insert(0, definition_container._definitions.pop(index))

            # HOTFIXES for Blackbelt stacks
            if definition_container.getId() == "blackbelt" and self._application._machine_manager:
                extruder_stack = self._application.getMachineManager()._active_container_stack

                if extruder_stack:
                    # Make sure the extruder material diameter matches the global material diameter
                    material_diameter = extruder_stack.getProperty("material_diameter", "value")
                    if material_diameter:
                        definition_changes_container = extruder_stack.definitionChanges
                        if "material_diameter" not in definition_changes_container.getAllKeys():
                            # Make sure there is a definition_changes container to store the machine settings
                            if definition_changes_container == ContainerRegistry.getInstance().getEmptyInstanceContainer():
                                definition_changes_container = CuraStackBuilder.createDefinitionChangesContainer(
                                    extruder_stack, extruder_stack.getId() + "_settings")

                            definition_changes_container.setProperty("material_diameter", "value", material_diameter)

                        # Make sure approximate diameters are in check
                        approximate_diameter = str(round(material_diameter))
                        extruder_stack.setMetaDataEntry("approximate_diameter", approximate_diameter)
                        self._global_container_stack.setMetaDataEntry("approximate_diameter", approximate_diameter)

                    # Make sure the extruder quality is a blackbelt quality profile
                    if extruder_stack.quality != self._application.empty_quality_container and extruder_stack.quality.getDefinition().getId() != "blackbelt":
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

    def _onActiveQualityChanged(self):
        # HOTFIX: make sure global quality is correctly set
        if not self._global_container_stack:
            return
        extruder_stack = self._application.getMachineManager()._active_container_stack
        if not extruder_stack:
            return

        definition_container = self._global_container_stack.getBottom()
        if definition_container.getId() != "blackbelt":
            return

        if extruder_stack.quality.getMetaDataEntry("global_quality", False) or not self._global_container_stack.quality.getMetaDataEntry("global_quality", False):
            blackbelt_global_quality = ContainerRegistry.getInstance().findContainers(id = "blackbelt_global_normal")[0]
            self._global_container_stack.setQuality(blackbelt_global_quality)

            blackbelt_quality = ContainerRegistry.getInstance().findContainers(id = "blackbelt_normal")[0]
            extruder_stack.setQuality(blackbelt_quality)

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
        preferences = self._application.getPreferences()
        visible_settings = preferences.getValue("general/visible_settings")
        if not visible_settings:
            # Wait until the default visible settings have been set
            return

        if "blackbelt_settings" in visible_settings and not forced:
            return

        if self._application.getSettingVisibilityPresetsModel():
            self._application.getSettingVisibilityPresetsModel().setActivePreset("blackbelt")

        visible_settings_changed = False
        default_visible_settings = [
            "blackbelt_settings", "blackbelt_repetitions"
        ]
        for key in default_visible_settings:
            if key not in visible_settings:
                visible_settings += ";%s" % key
                visible_settings_changed = True

        if visible_settings_changed:
            preferences.setValue("general/visible_settings", visible_settings)


    def _onActiveViewChanged(self):
        self._adjustLayerViewNozzle()

    def _adjustLayerViewNozzle(self):
        global_stack = self._application.getGlobalContainerStack()
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
        global_stack = self._application.getGlobalContainerStack()

        definition_container = self._global_container_stack.getBottom()
        if definition_container.getId() != "blackbelt":
            return

        scene = self._application.getController().getScene()
        gcode_dict = getattr(scene, "gcode_dict", {})
        if not gcode_dict: # this also checks for an empty dict
            Logger.log("w", "Scene has no gcode to process")
            return
        dict_changed = False

        enable_secondary_fans = global_stack.extruders["0"].getProperty("blackbelt_secondary_fans_enabled", "value")
        if enable_secondary_fans:
            secondary_fans_speed = global_stack.extruders["0"].getProperty("blackbelt_secondary_fans_speed", "value") / 100

        enable_belt_wall = global_stack.getProperty("blackbelt_belt_wall_enabled", "value")
        if enable_belt_wall:
            belt_wall_flow = global_stack.getProperty("blackbelt_belt_wall_flow", "value") / 100
            belt_wall_speed = global_stack.getProperty("blackbelt_belt_wall_speed", "value") * 60
            minimum_y = global_stack.extruders["0"].getProperty("wall_line_width_0", "value") / 2

        repetitions = global_stack.getProperty("blackbelt_repetitions", "value") or 1
        if repetitions > 1:
            repetitions_distance = global_stack.getProperty("blackbelt_repetitions_distance", "value")
            repetitions_gcode = global_stack.getProperty("blackbelt_repetitions_gcode", "value")

        for plate_id in gcode_dict:
            gcode_list = gcode_dict[plate_id]
            if not gcode_list:
                continue

            if ";BLACKBELTPROCESSED" in gcode_list[0]:
                Logger.log("e", "Already post processed")
                continue

            # put a print settings summary at the top
            # note: this simplified view is only valid for single extrusion printers
            setting_values = {}
            setting_summary = ";Setting summary:\n"
            for stack in [global_stack.extruders["0"], global_stack]:
                for index, container in enumerate(stack.getContainers()):
                    if index == ContainerIndexes.Definition:
                        continue
                    for key in container.getAllKeys():
                        if key not in setting_values:
                            value = container.getProperty(key, "value")
                            if not global_stack.getProperty(key, "settable_per_extruder"):
                                value = global_stack.getProperty(key, "value")
                            if isinstance(value, SettingFunction):
                                value = value(stack)
                            definition = container.getInstance(key).definition
                            if definition.type == "str":
                                value = value.replace("\n", "\\n")
                                if len(value) > 40:
                                    value = "[not shown for brevity]"
                            setting_values[key] = value

            for definition in global_stack.getBottom().findDefinitions():
                if definition.type == "category":
                    setting_summary += ";  CATEGORY: %s\n" % definition.label
                elif definition.key in setting_values:
                    setting_summary += ";    %s: %s\n" % (definition.label, setting_values[definition.key])
            gcode_list[0] += setting_summary

            # secondary fans should similar things as print cooling fans
            if enable_secondary_fans:
                search_regex = re.compile(r"M106 S(\d*\.?\d*)")

                for layer_number, layer in enumerate(gcode_list):
                    gcode_list[layer_number] = re.sub(search_regex, lambda m: "M106 P1 S%d\nM106 S%s" % (int(min(255, float(m.group(1)) * secondary_fans_speed)), m.group(1)), layer) #Replace all.

            # adjust walls that touch the belt
            if enable_belt_wall:
                #wall_line_width_0
                y = None
                last_y = None
                e = None
                last_e = None
                f = None

                speed_regex = re.compile(r" F\d*\.?\d*")
                extrude_regex = re.compile(r" E-?\d*\.?\d*")
                move_parameters_regex = re.compile(r"([YEF]-?\d*\.?\d+)")

                for layer_number, layer in enumerate(gcode_list):
                    if layer_number < 2 or layer_number > len(gcode_list) - 1:
                        # gcode_list[0]: curaengine header
                        # gcode_list[1]: start gcode
                        # gcode_list[2] - gcode_list[n-1]: layers
                        # gcode_list[n]: end gcode
                        continue

                    lines = layer.splitlines()
                    for line_number, line in enumerate(lines):
                        line_has_e = False
                        line_has_axis = False

                        gcode_command = line.split(' ', 1)[0]
                        if gcode_command not in ["G0", "G1", "G92"]:
                            continue

                        result = re.findall(move_parameters_regex, line)
                        if not result:
                            continue

                        for match in result:
                            parameter = match[:1]
                            value = float(match[1:])
                            if parameter == "Y":
                                y = value
                                line_has_axis = True
                            elif parameter == "E":
                                e = value
                                line_has_e = True
                            elif parameter == "F":
                                f = value
                            elif parameter in "XZ":
                                line_has_axis = True

                        if gcode_command != "G92" and line_has_axis and line_has_e and f is not None and y is not None and y <= minimum_y and last_y is not None and last_y <= minimum_y:
                            if f > belt_wall_speed:
                                # Remove pre-existing move speed and add our own
                                line = re.sub(speed_regex, r"", line)

                            if belt_wall_flow != 1.0 and last_y is not None:
                                new_e = last_e + (e - last_e) * belt_wall_flow
                                line = re.sub(extrude_regex, " E%f" % new_e, line)
                                line += " ; Adjusted E for belt wall\nG92 E%f ; Reset E to pre-compensated value" % e

                            if f > belt_wall_speed:
                                g_type = int(line[1:2])
                                line = "G%d F%d ; Belt wall speed\n%s\nG%d F%d ; Restored speed" % (g_type, belt_wall_speed, line, g_type, f)

                            lines[line_number] = line

                        last_y = y
                        last_e = e

                    edited_layer = "\n".join(lines) + "\n"
                    gcode_list[layer_number] = edited_layer

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

        if dict_changed:
            setattr(scene, "gcode_dict", gcode_dict)
