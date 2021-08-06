import configparser
from typing import Tuple, List, Set, Dict
import io

from UM.VersionUpgrade import VersionUpgrade
from cura.PrinterOutput.PrinterOutputDevice import ConnectionType

deleted_settings = {"bridge_wall_max_overhang"}  # type: Set[str]
renamed_configurations = {"connect_group_name": "group_name"}  # type: Dict[str, str]


class VersionUpgrade35to40(VersionUpgrade):
    #  Upgrades stacks to have the new version number.
    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(serialized)

        # Update version number.
        parser["general"]["version"] = "4"
        parser["metadata"]["setting_version"] = "6"

        if parser["metadata"].get("um_network_key") is not None or parser["metadata"].get("octoprint_api_key") is not None:
            # Set the connection type if um_network_key or the octoprint key is set.
            parser["metadata"]["connection_type"] = str(ConnectionType.NetworkConnection.value)

        if "metadata" in parser:
            for old_name, new_name in renamed_configurations.items():
                if old_name not in parser["metadata"]:
                    continue
                parser["metadata"][new_name] = parser["metadata"][old_name]
                del parser["metadata"][old_name]

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradePreferences(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """Upgrades Preferences to have the new version number."""

        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(serialized)

        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["general"]["version"] = "6"
        parser["metadata"]["setting_version"] = "6"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """Upgrades instance containers to have the new version number."""

        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(serialized)

        # Update version number.
        parser["general"]["version"] = "4"
        parser["metadata"]["setting_version"] = "6"

        #self._resetConcentric3DInfillPattern(parser)
        if "values" in parser:
            for deleted_setting in deleted_settings:
                if deleted_setting not in parser["values"]:
                    continue
                del parser["values"][deleted_setting]

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
