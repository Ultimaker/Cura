import configparser
from typing import Tuple, List
import io
from UM.VersionUpgrade import VersionUpgrade

_renamed_container_id_map = {
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
    def getCfgVersion(self, serialised: str) -> int:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)
        format_version = int(parser.get("general", "version"))  # Explicitly give an exception when this fails. That means that the file format is not recognised.
        setting_version = int(parser.get("metadata", "setting_version", fallback = "0"))
        return format_version * 1000000 + setting_version

    ##  Upgrades Preferences to have the new version number.
    #
    #   This renames the renamed settings in the list of visible settings.
    def upgradePreferences(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "10"

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
        parser["metadata"]["setting_version"] = "10"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    ##  Upgrades stacks to have the new version number.
    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "10"

        if "containers" in parser:
            # Update renamed containers
            for key, value in parser["containers"].items():
                if value in _renamed_container_id_map:
                    parser["containers"][key] = _renamed_container_id_map[value]

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
