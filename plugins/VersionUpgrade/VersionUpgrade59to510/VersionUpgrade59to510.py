import configparser
import io
from typing import Dict, Tuple, List

from UM.VersionUpgrade import VersionUpgrade

_RENAMED_SETTINGS = {
    "wall_overhang_speed_factor": "wall_overhang_speed_factors"
}  # type: Dict[str, str]

_NEW_SETTING_VERSION = "25"


class VersionUpgrade59to510(VersionUpgrade):
    def upgradePreferences(self, serialized: str, filename: str):
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Fix 'renamed'(ish) settings for visibility
        if "visible_settings" in parser["general"]:
            all_setting_keys = parser["general"]["visible_settings"].strip().split(";")
            if all_setting_keys:
                for idx, key in enumerate(all_setting_keys):
                    if key in _RENAMED_SETTINGS:
                        all_setting_keys[idx] = _RENAMED_SETTINGS[key]
                parser["general"]["visible_settings"] = ";".join(all_setting_keys)

        # Update version number.
        parser["metadata"]["setting_version"] = _NEW_SETTING_VERSION

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None, comment_prefixes = ())
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = _NEW_SETTING_VERSION

        if "values" in parser:
            for old_name, new_name in _RENAMED_SETTINGS.items():
                if old_name in parser["values"]:
                    parser["values"][new_name] = parser["values"][old_name]
                    del parser["values"][old_name]
            if "wall_overhang_speed_factors" in parser["values"]:
                old_value = float(parser["values"]["wall_overhang_speed_factors"])
                new_value = [max(1, int(round(old_value)))]
                parser["values"]["wall_overhang_speed_factor"] = str(new_value)

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        if "metadata" not in parser:
            parser["metadata"] = {}

        parser["metadata"]["setting_version"] = _NEW_SETTING_VERSION

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
