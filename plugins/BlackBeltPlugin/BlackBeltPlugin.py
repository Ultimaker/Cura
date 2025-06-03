# Copyright (c) 2018 fieldOfView
# The Blackbelt plugin is released under the terms of the LGPLv3 or higher.

from UM.Extension import Extension
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.SettingFunction import SettingFunction
from UM.Logger import Logger
from UM.Version import Version
from UM.Message import Message

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
from . import FlavorParserPatches

from PyQt5.QtQml import qmlRegisterSingletonType

import math
import os.path
import re
import json
from hashlib import md5

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

        self._startend_gcode_message = Message(
            i18n_catalog.i18nc("@info:status", "Your configuration is not using the recommended start and end gcode scripts.\nDo you want to reset the start and end scripts to their defaults or keep using the custom scripts?"),
            lifetime=0, dismissable=True, use_inactivity_timer=False
        )
        self._startend_gcode_message.addAction(
            "reset", i18n_catalog.i18nc("@action:button", "Use default scripts"), "",
            i18n_catalog.i18nc("@action:tooltip", "Reset the start and end gcode scripts to the recommended defaults."),
            button_style=Message.ActionButtonStyle.DEFAULT
        )
        self._startend_gcode_message.addAction(
            "custom", i18n_catalog.i18nc("@action:button", "Use custom scripts"), "",
            i18n_catalog.i18nc("@action:tooltip", "Keep using the customised start and end gcode scripts."),
            button_style=Message.ActionButtonStyle.DEFAULT
        )
        self._startend_gcode_message.actionTriggered.connect(self._onStartEndGcodeMessageActionTriggered)

    def _onPluginsLoaded(self):
        # make sure the we connect to engineCreatedSignal later than PrepareStage does, so we can substitute our own sidebar
        self._application.engineCreatedSignal.connect(self._onEngineCreated)

        # Hide nozzle in simulation view
        self._application.getController().activeViewChanged.connect(self._onActiveViewChanged)

        # Disable USB printing output device
        self._application.getOutputDeviceManager().outputDevicesChanged.connect(self._onOutputDevicesChanged)

        # Update preference defaults
        preferences = self._application.getPreferences()
        preferences.preferenceChanged.connect(self._onPreferencesChanged)

        preferences.addPreference("blackbelt/setting_version", "0.0.0")
        plugin_version = self._getPluginVersion()
        if Version(preferences.getValue("blackbelt/setting_version")) < Version(plugin_version):
            Logger.log("d", "BlackBelt-specific updates to configuration are needed")
            self._force_visibility_update = True

            preferences.addPreference("general/theme", self._application.default_theme)
            preferences.setValue("general/theme", "blackbelt")
            preferences.addPreference("cura/active_setting_visibility_preset", "basic")
            preferences.setValue("cura/active_setting_visibility_preset", "blackbelt")

            self._fixMaterialProperties()

    def _fixMaterialProperties(self):
        # Update preference defaults
        preferences = self._application.getPreferences()
        preferences.preferenceChanged.connect(self._onPreferencesChanged)

        add_pricing = True
        preferences.addPreference("cura/currency", "€")
        if preferences.getValue("cura/currency") != "€":
            add_pricing = False
        preferences.addPreference("cura/favorite_materials", "")
        preferences.addPreference("cura/material_settings", "{}")
        try:
            material_settings = json.loads(preferences.getValue("cura/material_settings"))
        except json.decoder.JSONDecodeError:
            Logger.log("e", "Unable to parse material settings: %s" % preferences.getValue("cura/material_settings"))
            material_settings = {}

        material_favorites = set()
        for item in preferences.getValue("cura/favorite_materials").split(";"):
            material_favorites.add(item)

        # Get default material pricing from json file
        material_defaults = {}
        defaults_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "material_settings.json")
        try:
            with open(defaults_file_path) as defaults_file:
                material_defaults = json.load(defaults_file)
        except:
            Logger.log("w", "Could not load default material pricing")

        for material_id in material_defaults:
            material_favorites.add(material_id)
            guid = material_defaults[material_id].get("guid", None)
            if not guid:
                continue
            # remove because of pricing updates
            #if material_settings.get(guid, None):
                #continue
            settings = { "spool_weight": material_defaults[material_id].get("spool_weight", 750) }
            Logger.log("w", "Pricing changed")
            if add_pricing:
                settings["spool_cost"] = material_defaults[material_id].get("spool_cost", 0)
            material_settings[guid] = settings

        preferences.setValue("cura/material_settings", json.dumps(material_settings))
        preferences.setValue("cura/favorite_materials", ";".join(list(material_favorites)))


    def _getPluginVersion(self):
        # Get version information from plugin.json
        plugin_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugin.json")
        plugin_version = "0.0.0"
        try:
            with open(plugin_file_path) as plugin_file:
                plugin_info = json.load(plugin_file)
                plugin_version = plugin_info["version"]
        except:
            Logger.log("w", "Could not determine BlackBelt plugin version")

        return plugin_version


    def _onEngineCreated(self):
        # for some reason, setting this preference value does not "take" if we do it sooner
        plugin_version = self._getPluginVersion()
        Logger.log("d", "Setting BlackBelt version nr to %s" % plugin_version)
        self._application.getPreferences().setValue("blackbelt/setting_version", plugin_version)

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
        self._application.getQualityManager()._material_manager = self._application.getMaterialManager()
        self._application._material_manager.initialize()

        self._application.getBackend().slicingStarted.connect(self._onSlicingStarted)

        gcode_reader_plugin = PluginRegistry.getInstance().getPluginObject("GCodeReader")
        self._flavor_parser_patches = {}
        if gcode_reader_plugin:
            for (parser_name, parser_object) in gcode_reader_plugin._flavor_readers_dict.items():
                self._flavor_parser_patches[parser_name] = FlavorParserPatches.FlavorParserPatches(parser_object)

        self._fixVisibilityPreferences(forced = self._force_visibility_update)
        self._force_visibility_update = False

        # Run material settings again
        self._fixMaterialProperties()

    def _onOutputDevicesChanged(self):
        if not self._global_container_stack:
            return

        definition_container = self._global_container_stack.getBottom()
        if definition_container.getId() not in ["blackbelt", "blackbeltvd"]:
            return

        # HACK: Remove USB output device for blackbelt printers
        output_device_manager = self._application.getOutputDeviceManager()
        for output_device in output_device_manager.getOutputDevices():
            if "USBPrinterOutputDevice" in str(output_device):
                self._output_device_patches[output_device] = USBPrinterOutputDevicePatches.USBPrinterOutputDevicePatches(output_device)

    def _onGlobalContainerStackChanged(self):
        if self._global_container_stack:
            self._global_container_stack.propertyChanged.disconnect(self._onSettingValueChanged)
            self._startend_gcode_message.hide()

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
            if definition_container.getId() in ["blackbelt", "blackbeltvd"] and self._application._machine_manager:
                self._onSettingValueChanged("machine_start_gcode", "value") # check if start/end gcode scripts are default

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
                    if extruder_stack.quality != self._application.empty_quality_container and extruder_stack.quality.getDefinition().getId() not in ["blackbelt", "blackbeltvd"]:
                        blackbelt_normal_quality = ContainerRegistry.getInstance().findContainers(id = str(definition_container.getId())+"_normal")[0]
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
        if definition_container.getId() not in ["blackbelt", "blackbeltvd"]:
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
        if definition_container.getId() not in ["blackbelt", "blackbeltvd"]:
            return

        if extruder_stack.quality.getMetaDataEntry("global_quality", False) or not self._global_container_stack.quality.getMetaDataEntry("global_quality", False):
            blackbelt_global_quality = ContainerRegistry.getInstance().findContainers(id = str(definition_container.getId())+"_global_normal")[0]
            self._global_container_stack.setQuality(blackbelt_global_quality)

            blackbelt_quality = ContainerRegistry.getInstance().findContainers(id = str(definition_container.getId())+"_normal")[0]
            extruder_stack.setQuality(blackbelt_quality)

    def _onSettingValueChanged(self, key, property_name):
        if property_name != "value" or not self._global_container_stack.hasProperty("blackbelt_gantry_angle", "value"):
            return

        if key == "blackbelt_gantry_angle":
            # Setting the gantry angle changes the build volume.
            # Force rebuilding the build volume by reloading the global container stack.
            # This is a bit of a hack, but it seems quick enough.
            self._application.globalContainerStackChanged.emit()

        if key in ["machine_start_gcode", "machine_end_gcode"]:
            definition_changes_container = self._global_container_stack.definitionChanges
            if definition_changes_container.hasProperty("machine_start_gcode", "value") or definition_changes_container.hasProperty("machine_end_gcode", "value"):
                startend_gcode_hash = md5(
                    (self._global_container_stack.getProperty("machine_start_gcode", "value") + self._global_container_stack.getProperty("machine_end_gcode", "value")).encode()
                ).hexdigest()

                if startend_gcode_hash != self._global_container_stack.getMetaDataEntry("blackbelt_accepted_startend_gcode_hash", ""):
                    self._startend_gcode_message.show()

    def _onStartEndGcodeMessageActionTriggered(self, message, action):
        self._startend_gcode_message.hide()
        definition_changes_container = self._global_container_stack.definitionChanges
        if action == "reset":
            definition_changes_container.removeInstance("machine_start_gcode", postpone_emit = True)
            definition_changes_container.removeInstance("machine_end_gcode", postpone_emit = False)
            self._global_container_stack.setMetaDataEntry("blackbelt_accepted_startend_gcode_hash", "")
            self._application.globalContainerStackChanged.emit()
        elif action == "custom":
            startend_gcode_hash = md5(
                (self._global_container_stack.getProperty("machine_start_gcode", "value") + self._global_container_stack.getProperty("machine_end_gcode", "value")).encode()
            ).hexdigest()

            self._global_container_stack.setMetaDataEntry("blackbelt_accepted_startend_gcode_hash", startend_gcode_hash)

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
        if definition_container.getId() not in ["blackbelt", "blackbeltvd"]:
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
            minimum_y = global_stack.extruders["0"].getProperty("wall_line_width_0", "value") * 0.6 #  0.5 would be non-tolerant

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

            # HOTFIX: remove finalize bits before end gcode
            end_gcode = gcode_list[len(gcode_list)-1]
            end_gcode = end_gcode.replace("M140 S0\nM203 Z5\nM107", "") # TODO: regex magic
            gcode_list[len(gcode_list)-1] = end_gcode

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
