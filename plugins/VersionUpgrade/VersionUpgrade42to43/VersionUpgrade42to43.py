import configparser
import io
from typing import Tuple, List

from UM.VersionUpgrade import VersionUpgrade

_renamed_profiles = {"generic_pla_0.4_coarse": "jbo_generic_pla_0.4_coarse",
                     "generic_pla_0.4_fine": "jbo_generic_pla_fine",
                     "generic_pla_0.4_medium": "jbo_generic_pla_medium",
                     "generic_pla_0.4_ultrafine": "jbo_generic_pla_ultrafine",

                     "generic_petg_0.4_coarse": "jbo_generic_petg_0.4_coarse",
                     "generic_petg_0.4_fine": "jbo_generic_petg_fine",
                     "generic_petg_0.4_medium": "jbo_generic_petg_medium",
                     }

_removed_settings = {
    "start_layers_at_same_position"
}

_renamed_settings = {
    "support_infill_angle": "support_infill_angles"
} # type: Dict[str, str]

##  Upgrades configurations from the state they were in at version 4.2 to the
#   state they should be in at version 4.3.
class VersionUpgrade42to43(VersionUpgrade):
    ##  Gets the version number from a CFG file in Uranium's 4.2 format.
    #
    #   Since the format may change, this is implemented for the 4.2 format only
    #   and needs to be included in the version upgrade system rather than
    #   globally in Uranium.
    #
    #   \param serialised The serialised form of a CFG file.
    #   \return The version number stored in the CFG file.
    #   \raises ValueError The format of the version number in the file is
    #   incorrect.
    #   \raises KeyError The format of the file is incorrect.
    def getCfgVersion(self, serialised: str) -> int:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)
        format_version = int(parser.get("general", "version"))  # Explicitly give an exception when this fails. That means that the file format is not recognised.
        setting_version = int(parser.get("metadata", "setting_version", fallback = "0"))
        return format_version * 1000000 + setting_version

    def upgradePreferences(self, serialized: str, filename: str):
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        if "camera_perspective_mode" in parser["general"] and parser["general"]["camera_perspective_mode"] == "orthogonal":
            parser["general"]["camera_perspective_mode"] = "orthographic"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    ##  Upgrades instance containers to have the new version
    #   number.
    #
    #   This renames the renamed settings in the containers.
    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
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

        parser["values"]["support_infill_angles"]["type"] = "[int]"
        parser["values"]["support_infill_angles"]["default_value"] = "[ ]"
        del parser["values"]["support_infill_angles"]["minimum_value"]
        del parser["values"]["support_infill_angles"]["maximum_value"]

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    ##  Upgrades stacks to have the new version number.
    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
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
            if material_id.endswith("_2-fans"):
                parser["containers"]["3"] = material_id.replace("_2-fans", "")
            variant_id = parser["containers"]["4"]

            if variant_id.endswith("_2-fans"):
                parser["containers"]["4"] = variant_id.replace("_2-fans", "")

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]