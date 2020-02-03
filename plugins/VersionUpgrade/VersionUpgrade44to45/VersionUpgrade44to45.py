import configparser
import os
from collections import namedtuple
from pathlib import Path
from typing import Tuple, List, Dict
import io

from UM.Logger import Logger
from UM.Resources import Resources
from UM.VersionUpgrade import VersionUpgrade
from UM.VersionUpgradeManager import VersionUpgradeManager, CallableTask

ExtruderMachineMapping = namedtuple("ExtruderMachineMapping", ["extruder_id", "extruder_filename", "machine_id"])
HiddenMachine = namedtuple("HiddenMachine", ["machine_id", "filename"])

# Settings that were merged into one. Each one is a pair of settings. If both
# are overwritten, the key wins. If only the key or the value is overwritten,
# that value is used in the key.
_merged_settings = {
    "machine_head_with_fans_polygon": "machine_head_polygon",
    "support_wall_count": "support_tree_wall_count"
}

_removed_settings = {
    "support_tree_wall_thickness"
}


class VersionUpgrade44to45(VersionUpgrade):

    def __init__(self) -> None:
        self._hidden_machines = {}  # type: Dict[str, str]
        """machine_id -> stack filename prefix"""

        self._extruder_machine_mapping = []  # type: List[ExtruderMachineMapping]


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

            for removed in _removed_settings:
                if removed in parser["values"]:
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

        # Check for leftover hidden machines. They should be deleted along with their associated files
        stack_id = parser["general"]["id"]
        if parser["metadata"]["setting_version"] == "10" and stack_id is not None:
            stack_type = parser["metadata"]["type"]
            if stack_type == "machine" and parser["metadata"]["hidden"]:
                if not self._hidden_machines:
                    # schedule a final upgrade step to delete all hidden machines
                    VersionUpgradeManager.getInstance().upgradeExtraTask(CallableTask(self.deleteHiddenMachines))
                self._hidden_machines[stack_id] = filename
            elif stack_type == "extruder_train":
                machine = parser["metadata"]["machine"]
                self._extruder_machine_mapping.append(ExtruderMachineMapping(stack_id, filename, machine))

        parser["metadata"]["setting_version"] = "11"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def deleteHiddenMachines(self) -> None:

        # delete extruders associated to hidden machines
        for item in self._extruder_machine_mapping:
            if item.machine_id in self._hidden_machines:
                Logger.debug("Deleting extruder files for {}".format(item))
                self._deleteConfigFiles(item.extruder_filename)

        # delete machine files
        for machine_id, filename in self._hidden_machines.items():
            Logger.debug("Deleting files for hidden machine {}".format(machine_id))
            self._deleteConfigFiles(filename)

    def _deleteConfigFiles(self, filename: str) -> None:
        path_prefix = Resources.getConfigStoragePath()
        # FIXME this rglob pattern does not work
        for file_path in Path(path_prefix).rglob(filename + "*.cfg"):
            Logger.debug("Deleting {}".format(file_path))
            os.remove(str(file_path))
