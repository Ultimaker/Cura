# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, TYPE_CHECKING

import UM.Settings.Models.SettingVisibilityHandler

if TYPE_CHECKING:
    from PyQt5.QtCore import QObject

class MaterialSettingsVisibilityHandler(UM.Settings.Models.SettingVisibilityHandler.SettingVisibilityHandler):
    def __init__(self, parent: Optional["QObject"] = None, *args, **kwargs) -> None:
        super().__init__(parent = parent, *args, **kwargs)

        material_settings = {
            "default_material_print_temperature",
            "default_material_bed_temperature",
            "material_standby_temperature",
            #"material_flow_temp_graph",
            "cool_fan_speed",
            "retraction_amount",
            "retraction_speed",
        }

        self.setVisible(material_settings)
