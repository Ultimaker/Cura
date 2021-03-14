import configparser
from typing import Tuple, List
import io
from UM.VersionUpgrade import VersionUpgrade
from UM.Util import parseBool  # To parse whether the Alternate Skin Rotations function is activated.

_renamed_container_id_map = {
    "ultimaker2_0.25": "ultimaker2_olsson_0.25",
    "ultimaker2_0.4": "ultimaker2_olsson_0.4",
    "ultimaker2_0.6": "ultimaker2_olsson_0.6",
    "ultimaker2_0.8": "ultimaker2_olsson_0.8",
    "ultimaker2_extended_0.25": "ultimaker2_extended_olsson_0.25",
    "ultimaker2_extended_0.4": "ultimaker2_extended_olsson_0.4",
    "ultimaker2_extended_0.6": "ultimaker2_extended_olsson_0.6",
    "ultimaker2_extended_0.8": "ultimaker2_extended_olsson_0.8",
    # HMS434 "extra coarse", "super coarse", and "ultra coarse" are removed.
    "hms434_global_Extra_Coarse_Quality": "hms434_global_Normal_Quality",
    "hms434_global_Super_Coarse_Quality": "hms434_global_Normal_Quality",
    "hms434_global_Ultra_Coarse_Quality": "hms434_global_Normal_Quality",
    # HMS434 "0.25", "0.6", "1.2", and "1.5" nozzles are removed.
    "hms434_0.25tpnozzle": "hms434_0.4tpnozzle",
    "hms434_0.6tpnozzle": "hms434_0.4tpnozzle",
    "hms434_1.2tpnozzle": "hms434_0.4tpnozzle",
    "hms434_1.5tpnozzle": "hms434_0.4tpnozzle",
}


class VersionUpgrade43to44(VersionUpgrade):

    def upgradePreferences(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """Upgrades Preferences to have the new version number.

        This renames the renamed settings in the list of visible settings.
        """

        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "10"

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
        parser["metadata"]["setting_version"] = "10"

        # Intent profiles were added, so the quality changes should match with no intent (so "default")
        if parser["metadata"].get("type", "") == "quality_changes":
            parser["metadata"]["intent_category"] = "default"

        if "values" in parser:
            # Alternate skin rotation should be translated to top/bottom line directions.
            if "skin_alternate_rotation" in parser["values"] and parseBool(parser["values"]["skin_alternate_rotation"]):
                parser["values"]["skin_angles"] = "[45, 135, 0, 90]"
            # Unit of adaptive layers topography size changed.
            if "adaptive_layer_height_threshold" in parser["values"]:
                val = parser["values"]["adaptive_layer_height_threshold"]
                if val.startswith("="):
                    val = val[1:]
                val = "=({val}) / 1000".format(val = val)  # Convert microns to millimetres. Works even if the profile contained a formula.
                parser["values"]["adaptive_layer_height_threshold"] = val

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """Upgrades stacks to have the new version number."""

        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "10"

        if "containers" in parser:
            # With the ContainerTree refactor, UM2 with Olsson block got moved to a separate definition.
            if "6" in parser["containers"]:
                if parser["containers"]["6"] == "ultimaker2":
                    if "metadata" in parser and "has_variants" in parser["metadata"] and parser["metadata"]["has_variants"] == "True":  # This is an Olsson block upgraded UM2!
                        parser["containers"]["6"] = "ultimaker2_olsson"
                        del parser["metadata"]["has_variants"]
                elif parser["containers"]["6"] == "ultimaker2_extended":
                    if "metadata" in parser and "has_variants" in parser["metadata"] and parser["metadata"]["has_variants"] == "True":  # This is an Olsson block upgraded UM2E!
                        parser["containers"]["6"] = "ultimaker2_extended_olsson"
                        del parser["metadata"]["has_variants"]

            # We should only have 6 levels when we start.
            if "7" in parser["containers"]:
                return ([], [])

            # We added the intent container in Cura 4.4. This means that all other containers move one step down.
            parser["containers"]["7"] = parser["containers"]["6"]
            parser["containers"]["6"] = parser["containers"]["5"]
            parser["containers"]["5"] = parser["containers"]["4"]
            parser["containers"]["4"] = parser["containers"]["3"]
            parser["containers"]["3"] = parser["containers"]["2"]
            parser["containers"]["2"] = "empty_intent"

            # Update renamed containers
            for key, value in parser["containers"].items():
                if value in _renamed_container_id_map:
                    parser["containers"][key] = _renamed_container_id_map[value]

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
