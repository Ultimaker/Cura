# Copyright (c) 2016 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

import UM.Settings.Models

class MaterialSettingsVisibilityHandler(UM.Settings.Models.SettingVisibilityHandler):
    def __init__(self, parent = None, *args, **kwargs):
        super().__init__(parent = parent, *args, **kwargs)

        material_settings = set([
            "material_print_temperature",
            "material_bed_temperature",
            "material_standby_temperature",
            "cool_fan_speed",
            "retraction_amount",
            "retraction_speed",
        ])

        self.setVisible(material_settings)
