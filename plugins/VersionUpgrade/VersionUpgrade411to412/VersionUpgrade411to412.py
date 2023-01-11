# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
import io
import json
import os.path
from typing import List, Tuple

from UM.VersionUpgrade import VersionUpgrade


class VersionUpgrade411to412(VersionUpgrade):
    """
    Upgrades configurations from the state they were in at version 4.11 to the
    state they should be in at version 4.12.
    """

    _flsun_profile_mapping = {
        "extra_coarse": "flsun_sr_normal",
        "coarse": "flsun_sr_normal",
        "extra_fast": "flsun_sr_normal",
        "draft": "flsun_sr_normal",
        "fast": "flsun_sr_normal",
        "normal": "flsun_sr_normal",
        "high": "flsun_sr_fine"
    }

    _flsun_quality_type_mapping = {
        "extra coarse": "normal",
        "coarse"      : "normal",
        "verydraft"   : "normal",
        "draft"       : "normal",
        "fast"        : "normal",
        "normal"      : "normal",
        "high"        : "fine"
    }

    def upgradePreferences(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades preferences to have the new version number.
        :param serialized: The original contents of the preferences file.
        :param filename: The file name of the preferences file.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "19"

        # If the account scope in 4.11 is outdated, delete it so that the user is enforced to log in again and get the
        # correct permissions.
        new_scopes = {"account.user.read",
                      "drive.backup.read",
                      "drive.backup.write",
                      "packages.download",
                      "packages.rating.read",
                      "packages.rating.write",
                      "connect.cluster.read",
                      "connect.cluster.write",
                      "library.project.read",
                      "library.project.write",
                      "cura.printjob.read",
                      "cura.printjob.write",
                      "cura.mesh.read",
                      "cura.mesh.write",
                      "cura.material.write"}
        if "ultimaker_auth_data" in parser["general"]:
            ultimaker_auth_data = json.loads(parser["general"]["ultimaker_auth_data"])
            if new_scopes - set(ultimaker_auth_data["scope"].split(" ")):
                parser["general"]["ultimaker_auth_data"] = "{}"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]


    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades instance containers to have the new version number.
        :param serialized: The original contents of the instance container.
        :param filename: The file name of the instance container.
        :return: A list of file names, and a list of the new contents for those
        files.
        """
        parser = configparser.ConfigParser(interpolation = None, comment_prefixes = ())
        parser.read_string(serialized)

        # Update setting version number.
        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "19"

        # Update user-made quality profiles of flsun_sr printers to use the flsun_sr-specific qualities instead of the
        # global ones as their base
        file_base_name = os.path.basename(filename)  # Remove any path-related characters from the filename
        if file_base_name.startswith("flsun_sr_") and parser["metadata"].get("type") == "quality_changes":
            if "general" in parser and parser["general"].get("definition") == "fdmprinter":
                old_quality_type = parser["metadata"].get("quality_type", "normal")
                parser["general"]["definition"] = "flsun_sr"
                parser["metadata"]["quality_type"] = self._flsun_quality_type_mapping.get(old_quality_type, "normal")

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades container stacks to have the new version number.
        Upgrades container stacks for FLSun Racer to change their profiles.
        :param serialized: The original contents of the container stack.
        :param filename: The file name of the container stack.
        :return: A list of file names, and a list of the new contents for those
        files.
        """
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update setting version number.
        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "19"

        # Change renamed profiles.
        if "containers" in parser:
            definition_id = parser["containers"].get("7")
            if definition_id == "flsun_sr":
                if parser["metadata"].get("type", "machine") == "machine":  # Only global stacks.
                    old_quality = parser["containers"].get("3")
                    new_quality = self._flsun_profile_mapping.get(old_quality, "flsun_sr_normal")
                    parser["containers"]["3"] = new_quality

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
