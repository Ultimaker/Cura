# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
from typing import List, Optional, Tuple

from UM.Logger import Logger
from UM.Settings.ContainerFormatError import ContainerFormatError
from UM.Settings.InstanceContainer import InstanceContainer  # The new profile to make.
from cura.CuraApplication import CuraApplication
from cura.Machines.ContainerTree import ContainerTree
from cura.ReaderWriters.ProfileReader import ProfileReader

import zipfile


class CuraProfileReader(ProfileReader):
    """A plugin that reads profile data from Cura profile files.
    
    It reads a profile from a .curaprofile file, and returns it as a profile
    instance.
    """

    def __init__(self) -> None:
        """Initialises the cura profile reader.
        
        This does nothing since the only other function is basically stateless.
        """
        super().__init__()

    def read(self, file_name: str) -> List[Optional[InstanceContainer]]:
        """Reads a cura profile from a file and returns it.
        
        :param file_name: The file to read the cura profile from.
        :return: The cura profiles that were in the file, if any. If the file
            could not be read or didn't contain a valid profile, ``None`` is
            returned.
        """

        try:
            with zipfile.ZipFile(file_name, "r") as archive:
                results = []  # type: List[Optional[InstanceContainer]]
                for profile_id in archive.namelist():
                    with archive.open(profile_id) as f:
                        serialized = f.read()
                    upgraded_profiles = self._upgradeProfile(serialized.decode("utf-8"), profile_id) #After upgrading it may split into multiple profiles.
                    for upgraded_profile in upgraded_profiles:
                        serialization, new_id = upgraded_profile
                        profile = self._loadProfile(serialization, new_id)
                        if profile is not None:
                            results.append(profile)
                return results

        except zipfile.BadZipFile:
            # It must be an older profile from Cura 2.1.
            with open(file_name, encoding = "utf-8") as fhandle:
                serialized_bytes = fhandle.read()
            return [self._loadProfile(serialized, profile_id) for serialized, profile_id in self._upgradeProfile(serialized_bytes, file_name)]

    def _upgradeProfile(self, serialized: str, profile_id: str) -> List[Tuple[str, str]]:
        """Convert a profile from an old Cura to this Cura if needed.
        
        :param serialized: The profile data to convert in the serialized on-disk format.
        :param profile_id: The name of the profile.
        :return: List of serialized profile strings and matching profile names.
        """

        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        if "general" not in parser:
            Logger.log("w", "Missing required section 'general'.")
            return []
        if "version" not in parser["general"]:
            Logger.log("w", "Missing required 'version' property")
            return []

        version = int(parser["general"]["version"])
        setting_version = int(parser["metadata"].get("setting_version", "0"))
        if InstanceContainer.Version != version:
            name = parser["general"]["name"]
            return self._upgradeProfileVersion(serialized, name, version, setting_version)
        else:
            return [(serialized, profile_id)]

    def _loadProfile(self, serialized: str, profile_id: str) -> Optional[InstanceContainer]:
        """Load a profile from a serialized string.
        
        :param serialized: The profile data to read.
        :param profile_id: The name of the profile.
        :return: The profile that was stored in the string.
        """

        # Create an empty profile.
        profile = InstanceContainer(profile_id)
        profile.setMetaDataEntry("type", "quality_changes")
        try:
            profile.deserialize(serialized, file_name = profile_id)
        except ContainerFormatError as e:
            Logger.log("e", "Error in the format of a container: %s", str(e))
            return None
        except Exception as e:
            Logger.log("e", "Error while trying to parse profile: %s", str(e))
            return None

        global_stack = CuraApplication.getInstance().getGlobalContainerStack()
        if global_stack is None:
            return None

        active_quality_definition = ContainerTree.getInstance().machines[global_stack.definition.getId()].quality_definition
        if profile.getMetaDataEntry("definition") != active_quality_definition:
            profile.setMetaDataEntry("definition", active_quality_definition)
        return profile

    def _upgradeProfileVersion(self, serialized: str, profile_id: str, main_version: int, setting_version: int) -> List[Tuple[str, str]]:
        """Upgrade a serialized profile to the current profile format.
        
        :param serialized: The profile data to convert.
        :param profile_id: The name of the profile.
        :param source_version: The profile version of 'serialized'.
        :return: List of serialized profile strings and matching profile names.
        """

        source_version = main_version * 1000000 + setting_version

        from UM.VersionUpgradeManager import VersionUpgradeManager
        results = VersionUpgradeManager.getInstance().updateFilesData("quality_changes", source_version, [serialized], [profile_id])
        if results is None:
            return []

        serialized = results.files_data[0]

        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)
        if "general" not in parser:
            Logger.log("w", "Missing required section 'general'.")
            return []

        new_source_version = results.version
        if int(new_source_version / 1000000) != InstanceContainer.Version or new_source_version % 1000000 != CuraApplication.SettingVersion:
            Logger.log("e", "Failed to upgrade profile [%s]", profile_id)

        if int(parser["general"]["version"]) != InstanceContainer.Version:
            Logger.log("e", "Failed to upgrade profile [%s]", profile_id)
            return []
        return [(serialized, profile_id)]
