# Copyright (c) 2018 fieldOfView
# The FadeHeightSettingPlugin is a ketchu13 modified version of LinearAdvanceSettingPlugin by fieldOfView
# Released under the terms of the AGPLv3 or higher.

from UM.Extension import Extension
from UM.Application import Application
from UM.Settings.SettingDefinition import SettingDefinition
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.ContainerRegistry import ContainerRegistry
from collections import OrderedDict
from UM.i18n import i18nCatalog
from UM.Preferences import Preferences
from UM.Logger import Logger

i18n_catalog = i18nCatalog("FadeHeightSettingPlugin")


class FadeHeightSettingPlugin(Extension):
    def __init__(self):
        super().__init__()

        self._application = Application.getInstance()

        self._i18n_catalog = None
        self._category_key = "platform_adhesion"
        self._fade_height_setting_key = "fade_height_mm"
        self._fade_height_setting_dict = {
            "label": "Fade Height",
            "description": "Sets the auto bed leveling fade height in mm. Note that unless this setting is used in a start gcode snippet, it has no effect!",
            "unit": "mm",
            "type": "float",
            "default_value": 0,
            "settable_per_mesh": False,
            "settable_per_extruder": False,
            "settable_per_meshgroup": False,
            "enabled": "abl_enabled"
        }
        self._abl_enabled_key = "abl_enabled"
        self._abl_enabled_dict = {
            "label": "Auto Bed Leveling",
            "description": "Enable or disable the bed leveling correction.",
            "type": "bool",
            "default_value": False,
            "settable_per_mesh": False,
            "settable_per_extruder": False,
            "settable_per_meshgroup": False
        }

        ContainerRegistry.getInstance().containerLoadComplete.connect(self._onContainerLoadComplete)
        self._application.engineCreatedSignal.connect(self._onEngineCreated)

        self._application.globalContainerStackChanged.connect(self._onGlobalContainerStackChanged)
        self._onGlobalContainerStackChanged()

        self._application.getOutputDeviceManager().writeStarted.connect(self._filterGcode)

    def _onGlobalContainerStackChanged(self):
        self._global_container_stack = self._application.getGlobalContainerStack()

    def _onContainerLoadComplete(self, container_id):
        container = ContainerRegistry.getInstance().findContainers(id=container_id)[0]
        if not isinstance(container, DefinitionContainer):
            # skip containers that are not definitions
            return
        if container.getMetaDataEntry("type") == "extruder":
            # skip extruder definitions
            return

        category = container.findDefinitions(key=self._category_key)
        if not category:
            category = SettingDefinition(self._category_key, container, None, self._i18n_catalog)
            category_dict = self._category_dict
            category_dict["children"] = OrderedDict()
            category.deserialize(category_dict)
            container.addDefinition(category)
            container._updateRelations(category)

        self.create_and_attach_setting(container,
                                       self._abl_enabled_key,
                                       self._abl_enabled_dict,
                                       self._category_key
                                       )
        self.create_and_attach_setting(container,
                                       self._fade_height_setting_key,
                                       self._fade_height_setting_dict,
                                       self._category_key
                                       )

    def create_and_attach_setting(self, container, setting_key, setting_dict, parent):
        parent_category = container.findDefinitions(key=parent)
        definition = container.findDefinitions(key=setting_key)
        if parent_category and not definition:
            # this machine doesn't have a scalable extra prime setting yet
            parent_category = parent_category[0]
            setting_definition = SettingDefinition(setting_key, container, parent_category, self._i18n_catalog)
            setting_definition.deserialize(setting_dict)

            parent_category._children.append(setting_definition)
            container._definition_cache[setting_key] = setting_definition
            container._updateRelations(setting_definition)

    def _onEngineCreated(self):
        # Fix preferences
        preferences = Preferences.getInstance()
        visible_settings = preferences.getValue("general/visible_settings")
        if not visible_settings:
            # Wait until the default visible settings have been set
            return
        visible_settings_changed = False
        if self._category_key not in visible_settings:
            visible_settings += ";%s" % self._category_key
            visible_settings_changed = True

        if not visible_settings_changed:
            return
        preferences.setValue("general/visible_settings", visible_settings)

    def getPropVal(self, name_key):
        """Get the property value by is name"""
        property_value = self._global_container_stack.getProperty(name_key, "value")
        return property_value

    def _filterGcode(self, output_device):
        scene = self._application.getController().getScene()

        global_container_stack = self._application.getGlobalContainerStack()
        if not global_container_stack:
            return

        # check if Fade Height settings are already applied
        start_gcode = global_container_stack.getProperty("machine_start_gcode", "value")
        if "M420 " in start_gcode:
            return

        # get setting from Cura
        fade_height_mm = self.getPropVal(self._fade_height_setting_key)
        abl_enabled = self.getPropVal(self._abl_enabled_key)

        if fade_height_mm == 0 or abl_enabled is False:
            return

        gcode_dict = getattr(scene, "gcode_dict", {})
        if not gcode_dict:  # this also checks for an empty dict
            Logger.log("w", "Scene has no gcode to process")
            return

        for plate_id in gcode_dict:
            gcode_list = gcode_dict[plate_id]
            if len(gcode_list) < 2:
                Logger.log("w", "Plate %s does not contain any layers", plate_id)
                continue

            if ";FADEHEIGHTPROCESSED\n" not in gcode_list[0]:
                gcode_list[1] = gcode_list[1] + ("M420 S%i Z%d ;added by FadeHeightSettingPlugin\n" % (
                int(abl_enabled), fade_height_mm))
                gcode_list[0] += ";FADEHEIGHTPROCESSED\n"
                gcode_dict[plate_id] = gcode_list
                dict_changed = True
            else:
                Logger.log("d", "Plate %s has already been processed by FadeHeight", plate_id)
                continue

        if dict_changed:
            setattr(scene, "gcode_dict", gcode_dict)
