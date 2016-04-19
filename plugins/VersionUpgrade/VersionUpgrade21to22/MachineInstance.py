# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import UM.Settings.SettingsError #To indicate that a file is of incorrect format.

import configparser #To read config files.
import io #To write config files to strings as if they were files.

##  Creates a new machine instance instance by parsing a serialised machine
#   instance in version 1 of the file format.
#
#   \param serialised The serialised form of a machine instance in version 1.
#   \return A machine instance instance, or None if the file format is
#   incorrect.
def importVersion1(serialised):
    try:
        return MachineInstance(serialised)
    except (configparser.Error, SettingsError.InvalidFormatError, SettingsError.InvalidVersionError):
        return None

##  A representation of a machine instance used as intermediary form for
#   conversion from one format to the other.
class MachineInstance:
    ##  Reads version 1 of the file format, storing it in memory.
    #
    #   \param serialised A string with the contents of a machine instance file.
    def __init__(self, serialised):
        config = configparser.ConfigParser(interpolation = None)
        config.read_string(serialised) #Read the input string as config file.

        #Checking file correctness.
        if not config.has_section("general"):
            raise SettingsError.InvalidFormatError("general")
        if not config.has_option("general", "version"):
            raise SettingsError.InvalidFormatError("general/version")
        if not config.has_option("general", "name"):
            raise SettingsError.InvalidFormatError("general/name")
        if not config.has_option("general", "type"):
            raise SettingsError.InvalidFormatError("general/type")
        if int(config.get("general", "version")) != 1: #Explicitly hard-code version 1, since if this number changes the programmer MUST change this entire function.
            raise SettingsError.InvalidVersionError("Version upgrade intermediary version 1")

        self._type_name = config.get("general", "type")
        self._variant_name = config.get("general", "variant", fallback = None)
        self._name = config.get("general", "name")
        self._key = config.get("general", "key", fallback = None)
        self._active_profile_name = config.get("general", "active_profile", fallback = None)
        self._active_material_name = config.get("general", "material", fallback = None)

        self._machine_setting_overrides = {}
        for key, value in config["machine_settings"].items():
            self._machine_setting_overrides[key] = value

    ##  Serialises this machine instance as file format version 2.
    #
    #   This is where the actual translation happens in this case.
    #
    #   \return A serialised form of this machine instance, serialised in
    #   version 2 of the file format.
    def exportVersion2():
        config = configparser.ConfigParser(interpolation = None) #Build a config file in the form of version 2.

        config.add_section("general")
        config.set("general", "name", self._name)
        config.set("general", "type", self._type_name)
        config.set("general", "version", 2) #Hard-code version 2, since if this number changes the programmer MUST change this entire function.
        if self._variant_name:
            config.set("general", "variant", self._variant_name)
        if self._key:
            config.set("general", "key", self._key)
        if self._active_profile_name:
            config.set("general", "active_profile", self._active_profile_name)
        if self._active_material_name:
            config.set("general", "material", self._active_material_name)

        config.add_section("machine_settings")
        for key, value in self._machine_setting_overrides.items():
            if key == "speed_support_lines": #Setting key was changed for 2.2.
                key = "speed_support_infill"
            config.set("machine_settings", key, value)

        output = io.StringIO()
        config.write(output)
        return output.getvalue()