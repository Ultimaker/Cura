#  Copyright (c) 2024 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtCore import QObject, pyqtProperty

from .SettingsExportGroup import SettingsExportGroup
from .SettingExport import SettingsExport
from cura.CuraApplication import CuraApplication
from UM.Settings.SettingDefinition import SettingDefinition
from cura.Settings.ExtruderManager import ExtruderManager


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
                           'brim_outside_only',
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

    def __init__(self, parent = None):
        super().__init__(parent)
        self._settings_groups = []

        application = CuraApplication.getInstance()

        # Display global settings
        global_stack = application.getGlobalContainerStack()
        self._settings_groups.append(SettingsExportGroup("Global settings",
                                                         SettingsExportGroup.Category.Global,
                                                         self._exportSettings(global_stack)))

        # Display per-extruder settings
        extruders_stacks = ExtruderManager.getInstance().getUsedExtruderStacks()
        for extruder_stack in extruders_stacks:
            color = ""
            if extruder_stack.material:
                color = extruder_stack.material.getMetaDataEntry("color_code")

            self._settings_groups.append(SettingsExportGroup("Extruder settings",
                                                             SettingsExportGroup.Category.Extruder,
                                                             self._exportSettings(extruder_stack),
                                                             extruder_index=extruder_stack.position,
                                                             extruder_color=color))

        # Display per-model settings
        scene_root = application.getController().getScene().getRoot()
        for scene_node in scene_root.getChildren():
            per_model_stack = scene_node.callDecoration("getStack")
            if per_model_stack is not None:
                self._settings_groups.append(SettingsExportGroup("Model settings",
                                                                 SettingsExportGroup.Category.Model,
                                                                 self._exportSettings(per_model_stack),
                                                                 scene_node.getName()))

    @pyqtProperty(list, constant=True)
    def settingsGroups(self):
        return self._settings_groups

    @staticmethod
    def _exportSettings(settings_stack):
        user_settings_container = settings_stack.getTop()
        user_keys = user_settings_container.getAllKeys()

        settings_export = []

        for setting_to_export in user_keys.intersection(SettingsExportModel.EXPORTABLE_SETTINGS):
            label = settings_stack.getProperty(setting_to_export, "label")
            value = settings_stack.getProperty(setting_to_export, "value")

            setting_type = settings_stack.getProperty(setting_to_export, "type")
            if setting_type is not None:
                # This is not very good looking, but will do for now
                value = SettingDefinition.settingValueToString(setting_type, value)
            else:
                value = str(value)

            settings_export.append(SettingsExport(label, value))

        return settings_export