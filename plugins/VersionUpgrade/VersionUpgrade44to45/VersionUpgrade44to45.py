import configparser
from typing import Tuple, List
import io
from UM.VersionUpgrade import VersionUpgrade

# Settings that were merged into one. Each one is a pair of settings. If both
# are overwritten, the key wins. If only the key or the value is overwritten,
# that value is used in the key.
_merged_settings = {
    "machine_head_with_fans_polygon": "machine_head_polygon",
    "support_wall_count": "support_tree_wall_count"
}

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
        parser = configparser.ConfigParser(interpolation = None, comment_prefixes = ())
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "11"

        if "values" in parser:
            # Merged settings: When two settings are merged, one is preferred.
            # If the preferred one is available, that value is taken regardless
            # of the other one. If only the non-preferred one is available, that
            # value is moved to the preferred setting value.
            for preferred, removed in _merged_settings.items():
                if removed in parser["values"]:
                    if preferred not in parser["values"]:
                        parser["values"][preferred] = parser["values"][removed]
                    del parser["values"][removed]

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
