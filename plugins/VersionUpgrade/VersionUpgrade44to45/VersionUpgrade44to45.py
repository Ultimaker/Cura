# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
from typing import Tuple, List
import fnmatch  # To filter files that we need to delete.
import io
import os  # To get the path to check for hidden stacks to delete.
import urllib.parse  # To get the container IDs from file names.
import re  # To filter directories to search for hidden stacks to delete.
from UM.Logger import Logger
from UM.Resources import Resources  # To get the path to check for hidden stacks to delete.
from UM.Version import Version  # To sort folders by version number.
from UM.VersionUpgrade import VersionUpgrade

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
        """
        Creates the version upgrade plug-in from 4.4 to 4.5.

        In this case the plug-in will also check for stacks that need to be
        deleted.
        """

        # Only delete hidden stacks when upgrading from version 4.4. Not 4.3 or 4.5, just when you're starting out from 4.4.
        # If you're starting from an earlier version, you can't have had the bug that produces too many hidden stacks (https://github.com/Ultimaker/Cura/issues/6731).
        # If you're starting from a later version, the bug was already fixed.
        data_storage_root = os.path.dirname(Resources.getDataStoragePath())
        folders = set(os.listdir(data_storage_root))  # All version folders.
        folders = set(filter(lambda p: re.fullmatch(r"\d+\.\d+", p), folders))  # Only folders with a correct version number as name.
        folders.difference_update({os.path.basename(Resources.getDataStoragePath())})  # Remove current version from candidates (since the folder was just copied).
        if folders:
            latest_version = max(folders, key = Version)  # Sort them by semantic version numbering.
            if latest_version == "4.4":
                self.removeHiddenStacks()

    def removeHiddenStacks(self) -> None:
        """
        If starting the upgrade from 4.4, this will remove any hidden printer
        stacks from the configuration folder as well as all of the user profiles
        and definition changes profiles.

        This will ONLY run when upgrading from 4.4, not when e.g. upgrading from
        4.3 to 4.6 (through 4.4). This is because it's to fix a bug
        (https://github.com/Ultimaker/Cura/issues/6731) that occurred in 4.4
        only, so only there will it have hidden stacks that need to be deleted.
        If people upgrade from 4.3 they don't need to be deleted. If people
        upgrade from 4.5 they have already been deleted previously or never got
        the broken hidden stacks.
        """
        Logger.log("d", "Removing all hidden container stacks.")
        hidden_global_stacks = set()  # Which global stacks have been found? We'll delete anything referred to by these. Set of stack IDs.
        hidden_extruder_stacks = set()  # Which extruder stacks refer to the hidden global profiles?
        hidden_instance_containers = set()  # Which instance containers are referred to by the hidden stacks?

        # First find all of the hidden container stacks.
        data_storage = Resources.getDataStoragePath()
        for root, _, files in os.walk(data_storage):
            for filename in fnmatch.filter(files, "*.global.cfg"):
                parser = configparser.ConfigParser(interpolation = None)
                parser.read(os.path.join(root, filename))
                if "metadata" in parser and "hidden" in parser["metadata"] and parser["metadata"]["hidden"] == "True":
                    stack_id = urllib.parse.unquote_plus(os.path.basename(filename).split(".")[0])
                    hidden_global_stacks.add(stack_id)
                    # The user container and definition changes container are specific to this stack. We need to delete those too.
                    if "containers" in parser:
                        if "0" in parser["containers"]:  # User container.
                            hidden_instance_containers.add(parser["containers"]["0"])
                        if "6" in parser["containers"]:  # Definition changes container.
                            hidden_instance_containers.add(parser["containers"]["6"])
                    os.remove(os.path.join(root, filename))

        # Walk a second time to find all extruder stacks referring to these hidden container stacks.
        for root, _, files in os.walk(data_storage):
            for filename in fnmatch.filter(files, "*.extruder.cfg"):
                parser = configparser.ConfigParser(interpolation = None)
                parser.read(os.path.join(root, filename))
                if "metadata" in parser and "machine" in parser["metadata"] and parser["metadata"]["machine"] in hidden_global_stacks:
                    stack_id = urllib.parse.unquote_plus(os.path.basename(filename).split(".")[0])
                    hidden_extruder_stacks.add(stack_id)
                    # The user container and definition changes container are specific to this stack. We need to delete those too.
                    if "containers" in parser:
                        if "0" in parser["containers"]:  # User container.
                            hidden_instance_containers.add(parser["containers"]["0"])
                        if "6" in parser["containers"]:  # Definition changes container.
                            hidden_instance_containers.add(parser["containers"]["6"])
                    os.remove(os.path.join(root, filename))

        # Walk a third time to remove all instance containers that are referred to by either of those.
        for root, _, files in os.walk(data_storage):
            for filename in fnmatch.filter(files, "*.inst.cfg"):
                container_id = urllib.parse.unquote_plus(os.path.basename(filename).split(".")[0])
                if container_id in hidden_instance_containers:
                    os.remove(os.path.join(root, filename))

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
        parser["metadata"]["setting_version"] = "11"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
