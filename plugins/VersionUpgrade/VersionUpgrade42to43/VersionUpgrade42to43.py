import configparser
import io
from typing import Dict, Tuple, List

from UM.VersionUpgrade import VersionUpgrade

_renamed_profiles = {"generic_pla_0.4_coarse": "jbo_generic_pla_0.4_coarse",
                     "generic_pla_0.4_fine": "jbo_generic_pla_fine",
                     "generic_pla_0.4_medium": "jbo_generic_pla_medium",
                     "generic_pla_0.4_ultrafine": "jbo_generic_pla_ultrafine",

                     "generic_petg_0.4_coarse": "jbo_generic_petg_0.4_coarse",
                     "generic_petg_0.4_fine": "jbo_generic_petg_fine",
                     "generic_petg_0.4_medium": "jbo_generic_petg_medium",
                     }

# - The variant "imade3d jellybox 0.4 mm 2-fans" for machine definition "imade3d_jellybox"
# is now "0.4 mm" for machine definition "imade3d jellybox_2".
# - Materials "imade3d_petg_green" and "imade3d_petg_pink" are now "imade3d_petg_175".
# - Materials "imade3d_pla_green" and "imade3d_pla_pink" are now "imade3d_petg_175".
#
# Note: Theoretically, the old material profiles with "_2-fans" at the end should be updated to:
#  - machine definition: imade3d_jellybox_2
#  - variant:            0.4 mm (for jellybox 2)
#  - material:           (as an example) imade3d_petg_175_imade3d_jellybox_2_0.4_mm
#
# But this involves changing the definition of the global stack and the extruder stacks, which can cause more trouble
# than what we can fix. So, here, we update all material variants, regardless of having "_2-fans" at the end or not, to
# jellybox_0.4_mm.
#
_renamed_material_profiles = { # PETG
                              "imade3d_petg_green":                                "imade3d_petg_175",
                              "imade3d_petg_green_imade3d_jellybox":               "imade3d_petg_175_imade3d_jellybox",
                              "imade3d_petg_green_imade3d_jellybox_0.4_mm":        "imade3d_petg_175_imade3d_jellybox_0.4_mm",
                              "imade3d_petg_green_imade3d_jellybox_0.4_mm_2-fans": "imade3d_petg_175_imade3d_jellybox_0.4_mm",
                              "imade3d_petg_pink":                                 "imade3d_petg_175",
                              "imade3d_petg_pink_imade3d_jellybox":                "imade3d_petg_175_imade3d_jellybox",
                              "imade3d_petg_pink_imade3d_jellybox_0.4_mm":         "imade3d_petg_175_imade3d_jellybox_0.4_mm",
                              "imade3d_petg_pink_imade3d_jellybox_0.4_mm_2-fans":  "imade3d_petg_175_imade3d_jellybox_0.4_mm",
                              # PLA
                              "imade3d_pla_green":                                "imade3d_pla_175",
                              "imade3d_pla_green_imade3d_jellybox":               "imade3d_pla_175_imade3d_jellybox",
                              "imade3d_pla_green_imade3d_jellybox_0.4_mm":        "imade3d_pla_175_imade3d_jellybox_0.4_mm",
                              "imade3d_pla_green_imade3d_jellybox_0.4_mm_2-fans": "imade3d_pla_175_imade3d_jellybox_0.4_mm",
                              "imade3d_pla_pink":                                 "imade3d_pla_175",
                              "imade3d_pla_pink_imade3d_jellybox":                "imade3d_pla_175_imade3d_jellybox",
                              "imade3d_pla_pink_imade3d_jellybox_0.4_mm":         "imade3d_pla_175_imade3d_jellybox_0.4_mm",
                              "imade3d_pla_pink_imade3d_jellybox_0.4_mm_2-fans":  "imade3d_pla_175_imade3d_jellybox_0.4_mm",
                              }

_removed_settings = {
    "start_layers_at_same_position"
}

_renamed_settings = {
    "support_infill_angle": "support_infill_angles"
}  # type: Dict[str, str]


class VersionUpgrade42to43(VersionUpgrade):
    """Upgrades configurations from the state they were in at version 4.2 to the

    state they should be in at version 4.3.
    """
    def upgradePreferences(self, serialized: str, filename: str):
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        if "camera_perspective_mode" in parser["general"] and parser["general"]["camera_perspective_mode"] == "orthogonal":
            parser["general"]["camera_perspective_mode"] = "orthographic"

        # Fix renamed settings for visibility
        if "visible_settings" in parser["general"]:
            all_setting_keys = parser["general"]["visible_settings"].strip().split(";")
            if all_setting_keys:
                for idx, key in enumerate(all_setting_keys):
                    if key in _renamed_settings:
                        all_setting_keys[idx] = _renamed_settings[key]
                parser["general"]["visible_settings"] = ";".join(all_setting_keys)

        parser["metadata"]["setting_version"] = "9"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """Upgrades instance containers to have the new version number.

        This renames the renamed settings in the containers.
        """
        parser = configparser.ConfigParser(interpolation = None, comment_prefixes = ())
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "9"

        if "values" in parser:
            for old_name, new_name in _renamed_settings.items():
                if old_name in parser["values"]:
                    parser["values"][new_name] = parser["values"][old_name]
                    del parser["values"][old_name]
            for key in _removed_settings:
                if key in parser["values"]:
                    del parser["values"][key]

            if "support_infill_angles" in parser["values"]:
                old_value = float(parser["values"]["support_infill_angles"])
                new_value = [int(round(old_value))]
                parser["values"]["support_infill_angles"] = str(new_value)

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """Upgrades stacks to have the new version number."""

        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "9"
        # Handle changes for the imade3d jellybox. The machine was split up into parts (eg; a 2 fan version and a single
        # fan version. Perviously it used variants for this. The only upgrade we can do here is strip that variant.
        # This is because we only upgrade per stack (and to fully do these changes, we'd need to switch out something
        # in the global container based on changes made to the extruder stack)
        if parser["containers"]["6"] == "imade3d_jellybox_extruder_0":
            quality_id = parser["containers"]["2"]
            if quality_id.endswith("_2-fans"):
                parser["containers"]["2"] = quality_id.replace("_2-fans", "")

            if parser["containers"]["2"] in _renamed_profiles:
                parser["containers"]["2"] = _renamed_profiles[parser["containers"]["2"]]

            material_id = parser["containers"]["3"]
            if material_id in _renamed_material_profiles:
                parser["containers"]["3"] = _renamed_material_profiles[material_id]
            variant_id = parser["containers"]["4"]

            if variant_id.endswith("_2-fans"):
                parser["containers"]["4"] = variant_id.replace("_2-fans", "")

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
