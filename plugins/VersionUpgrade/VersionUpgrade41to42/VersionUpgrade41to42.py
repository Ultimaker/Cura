##  Upgrades configurations from the state they were in at version 4.1 to the
#   state they should be in at version 4.2.
import configparser
import io
from typing import Tuple, List

from UM.VersionUpgrade import VersionUpgrade


class VersionUpgrade41to42(VersionUpgrade):

    def getCfgVersion(self, serialised: str) -> int:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)
        format_version = int(parser.get("general", "version")) #Explicitly give an exception when this fails. That means that the file format is not recognised.
        setting_version = int(parser.get("metadata", "setting_version", fallback = "0"))
        return format_version * 1000000 + setting_version

    ##  Upgrades stacks to have the new version number.
    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(serialized)

        # We should only have 6 levels when we start.
        assert "7" not in parser["containers"]

        # Update version number.
        parser["general"]["version"] = "5"

        # We added the intent container in Cura 4.2. This means that all other containers move one step down.
        parser["containers"]["7"] = parser["containers"]["6"]
        parser["containers"]["6"] = parser["containers"]["5"]
        parser["containers"]["5"] = parser["containers"]["4"]
        parser["containers"]["4"] = parser["containers"]["3"]
        parser["containers"]["3"] = parser["containers"]["2"]
        parser["containers"]["2"] = "empty_intent"

        result = io.StringIO()
        parser.write(result)

        return [filename], [result.getvalue()]
    