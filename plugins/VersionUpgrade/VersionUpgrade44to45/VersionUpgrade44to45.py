import configparser
from typing import Tuple, List
import io
from UM.VersionUpgrade import VersionUpgrade

# Merged preferences: machine_head_polygon and machine_head_with_fans_polygon -> machine_head_with_fans_polygon
# When both are present, machine_head_polygon will be removed
# When only one of the two is present, it's value will be used


class VersionUpgrade44to45(VersionUpgrade):
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
        parser["metadata"]["setting_version"] = "11"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    ##  Upgrades instance containers to have the new version
    #   number.
    #
    #   This renames the renamed settings in the containers.
    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None, comment_prefixes=())
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "11"

        if "values" in parser:
            # merge machine_head_with_fans_polygon (preferred) and machine_head_polygon
            if "machine_head_with_fans_polygon" in parser["values"]:
                if "machine_head_polygon" in parser["values"]:
                    del parser["values"]["machine_head_polygon"]
            elif "machine_head_polygon" in parser["values"]:
                parser["values"]["machine_head_with_fans_polygon"] = parser["values"]["machine_head_polygon"]
                del parser["values"]["machine_head_polygon"]

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
        parser["metadata"]["setting_version"] = "11"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
