#  Copyright (c) 2024 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.

from dataclasses import asdict
from typing import Optional, cast, List, Dict, Pattern, Set

from PyQt6.QtCore import QObject, pyqtProperty

from UM import i18nCatalog
from UM.Settings.SettingDefinition import SettingDefinition
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.SettingFunction import SettingFunction

from cura.CuraApplication import CuraApplication
from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.GlobalStack import GlobalStack

from .SettingsExportGroup import SettingsExportGroup
from .SettingExport import SettingExport


class SettingsExportModel(QObject):

    EXPORTABLE_SETTINGS = {'infill_sparse_density',
                           'adhesion_type',
                           'support_enable',
                           'infill_pattern',
                           'support_type',
                           'support_structure',
                           'support_angle',
                           'support_infill_rate',
                           'ironing_enabled',
                           'fill_outline_gaps',
                           'coasting_enable',
                           'skin_monotonic',
                           'z_seam_position',
                           'infill_before_walls',
                           'ironing_only_highest_layer',
                           'xy_offset',
                           'adaptive_layer_height_enabled',
                           'brim_gap',
                           'support_offset',
                           'brim_location',
                           'magic_spiralize',
                           'slicing_tolerance',
                           'outer_inset_first',
                           'magic_fuzzy_skin_outside_only',
                           'conical_overhang_enabled',
                           'min_infill_area',
                           'small_hole_max_size',
                           'magic_mesh_surface_mode',
                           'carve_multiple_volumes',
                           'meshfix_union_all_remove_holes',
                           'support_tree_rest_preference',
                           'small_feature_max_length',
                           'draft_shield_enabled',
                           'brim_smart_ordering',
                           'ooze_shield_enabled',
                           'bottom_skin_preshrink',
                           'skin_edge_support_thickness',
                           'alternate_carve_order',
                           'top_skin_preshrink',
                           'interlocking_enable'}

    PER_MODEL_EXPORTABLE_SETTINGS_KEYS = {"anti_overhang_mesh",
                                          "infill_mesh",
                                          "cutting_mesh",
                                          "support_mesh"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings_groups = []

        application = CuraApplication.getInstance()

        self._appendGlobalSettings(application)
        self._appendExtruderSettings(application)
        self._appendModelSettings(application)

    def _appendGlobalSettings(self, application):
        global_stack = application.getGlobalContainerStack()
        self._settings_groups.append(SettingsExportGroup(
            global_stack, "Global settings", SettingsExportGroup.Category.Global, self._exportSettings(global_stack)))

    def _appendExtruderSettings(self, application):
        extruders_stacks = ExtruderManager.getInstance().getUsedExtruderStacks()
        for extruder_stack in extruders_stacks:
            color = extruder_stack.material.getMetaDataEntry("color_code") if extruder_stack.material else ""
            self._settings_groups.append(SettingsExportGroup(
                extruder_stack, "Extruder settings", SettingsExportGroup.Category.Extruder,
                self._exportSettings(extruder_stack), extruder_index=extruder_stack.position, extruder_color=color))

    def _appendModelSettings(self, application):
        scene = application.getController().getScene()
        for scene_node in scene.getRoot().getChildren():
            self._appendNodeSettings(scene_node, "Model settings", SettingsExportGroup.Category.Model)

    def _appendNodeSettings(self, node, title_prefix, category):
        stack = node.callDecoration("getStack")
        if stack:
            self._settings_groups.append(SettingsExportGroup(
                stack, f"{title_prefix}", category, self._exportSettings(stack), node.getName()))
        for child in node.getChildren():
            self._appendNodeSettings(child, f"Children of {node.getName()}", SettingsExportGroup.Category.Model)


    @pyqtProperty(list, constant=True)
    def settingsGroups(self) -> List[SettingsExportGroup]:
        return self._settings_groups

    @staticmethod
    def _exportSettings(settings_stack):
        settings_catalog = i18nCatalog("fdmprinter.def.json")
        user_settings_container = settings_stack.userChanges
        user_keys = user_settings_container.getAllKeys()
        exportable_settings = SettingsExportModel.EXPORTABLE_SETTINGS
        settings_export = []
        # Check whether any of the user keys exist in PER_MODEL_EXPORTABLE_SETTINGS_KEYS
        is_exportable = any(key in SettingsExportModel.PER_MODEL_EXPORTABLE_SETTINGS_KEYS for key in user_keys)

        for setting_to_export in user_keys:
            show_in_menu = setting_to_export not in SettingsExportModel.PER_MODEL_EXPORTABLE_SETTINGS_KEYS
            label_msgtxt = f"{str(setting_to_export)} label"
            label_msgid = settings_stack.getProperty(setting_to_export, "label")
            label = settings_catalog.i18nc(label_msgtxt, label_msgid)
            value = settings_stack.getProperty(setting_to_export, "value")
            unit = settings_stack.getProperty(setting_to_export, "unit")
            setting_type = settings_stack.getProperty(setting_to_export, "type")
            value_name = str(SettingDefinition.settingValueToString(setting_type, value))
            if unit:
                value_name += " " + str(unit)
            if setting_type == "enum":
                options = settings_stack.getProperty(setting_to_export, "options")
                value_msgctxt = f"{str(setting_to_export)} option {str(value)}"
                value_msgid = options.get(value, "")
                value_name = settings_catalog.i18nc(value_msgctxt, value_msgid)

            if setting_type is not None:
                value = f"{str(SettingDefinition.settingValueToString(setting_type, value))} {unit}"
            else:
                value = str(value)

            settings_export.append(SettingExport(setting_to_export,
                                                 label,
                                                 value,
                                                 value_name,
                                                 is_exportable or setting_to_export in exportable_settings,
                                                 show_in_menu))

        return settings_export
