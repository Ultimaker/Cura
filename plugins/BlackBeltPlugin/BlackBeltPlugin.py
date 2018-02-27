# Copyright (c) 2018 fieldOfView
# The Blackbelt plugin is released under the terms of the LGPLv3 or higher.

from UM.Extension import Extension
from UM.Application import Application
from UM.Preferences import Preferences
from UM.Settings.ContainerRegistry import ContainerRegistry

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("BlackBeltPlugin")

from . import BlackBeltDecorator
from . import BlackBeltSingleton
from . import BuildVolumePatches
from . import CuraEngineBackendPatches

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
        self._cura_engine_backend_patched = None

        self._global_container_stack = None
        self._application.globalContainerStackChanged.connect(self._onGlobalContainerStackChanged)
        self._onGlobalContainerStackChanged()

        self._scene_root = self._application.getController().getScene().getRoot()
        self._scene_root.addDecorator(BlackBeltDecorator.BlackBeltDecorator())

        qmlRegisterSingletonType(BlackBeltSingleton.BlackBeltSingleton, "Cura", 1, 0, "BlackBeltPlugin", BlackBeltSingleton.BlackBeltSingleton.getInstance)
        self._application.getOutputDeviceManager().writeStarted.connect(self._filterGcode)

        self._application.pluginsLoaded.connect(self._onPluginsLoaded)

    def _onPluginsLoaded(self):
        # make sure the we connect to engineCreatedSignal later than PrepareStage does, so we can substitute our own sidebar
        self._application.engineCreatedSignal.connect(self._onEngineCreated)

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

            # HOTFIX: Make sure the BlackBelt printer has the right quality profile
            if definition_container.getId() == "blackbelt":
                quality_container = self._global_container_stack.quality
                if quality_container.getDefinition().getId() != "blackbelt":
                    containers = ContainerRegistry.getInstance().findContainers(id="blackbelt_normal")
                    if containers:
                        self._global_container_stack.quality = containers[0]

    def _onSlicingStarted(self):
        self._scene_root.callDecoration("calculateTransformData")

    def _onSettingValueChanged(self, key, property_name):
        if property_name != "value" or not self._global_container_stack.hasProperty("blackbelt_gantry_angle", "value"):
            return

        elif key == "blackbelt_gantry_angle":
            # Setting the gantry angle changes the build volume.
            # Force rebuilding the build volume by reloading the global container stack.
            # This is a bit of a hack, but it seems quick enough.
            self._application.globalContainerStackChanged.emit()

    def _onEngineCreated(self):
        # Set window title
        self._application._engine.rootObjects()[0].setTitle(i18n_catalog.i18nc("@title:window","BlackBelt Cura"))

        # Substitute our own sidebar
        sidebar_component_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sidebar", "Sidebar.qml")
        prepare_stage = Application.getInstance().getController().getStage("PrepareStage")
        prepare_stage.addDisplayComponent("sidebar", sidebar_component_path)

        # Apply patches
        self._build_volume_patches = BuildVolumePatches.BuildVolumePatches(self._application.getBuildVolume())
        self._cura_engine_backend_patched = CuraEngineBackendPatches.CuraEngineBackendPatches(self._application.getBackend())

        self._application.getBackend().slicingStarted.connect(self._onSlicingStarted)

        # Fix preferences
        preferences = Preferences.getInstance()
        visible_settings = preferences.getValue("general/visible_settings")
        if not visible_settings:
            # Wait until the default visible settings have been set
            return

        visible_settings_changed = False
        for key in ["blackbelt_settings"]:
            if key not in visible_settings:
                visible_settings += ";%s" % key
                visible_settings_changed = True

        if not visible_settings_changed:
            return

        preferences.setValue("general/visible_settings", visible_settings)

        expanded_settings = preferences.getValue("cura/categories_expanded")
        if expanded_settings is None:
            expanded_settings = ""
        for key in ["blackbelt_settings"]:
            if key not in expanded_settings:
                expanded_settings += ";%s" % key
        preferences.setValue("cura/categories_expanded", expanded_settings)
        self._application.expandedCategoriesChanged.emit()

    def _filterGcode(self, output_device):
        global_stack = Application.getInstance().getGlobalContainerStack()

        enable_secondary_fans = global_stack.getProperty("blackbelt_secondary_fans_enabled", "value")
        repetitions = global_stack.getProperty("blackbelt_repetitions", "value")
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
                        search_regex = re.compile(r"M106 S(\d*\.?\d*?)")
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
