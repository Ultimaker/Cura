# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import UM.VersionUpgrade #To indicate that a file is of incorrect format.

import configparser #To read config files.
import io #To write config files to strings as if they were files.

##  Creates a new machine instance instance by parsing a serialised machine
#   instance in version 1 of the file format.
#
#   \param serialised The serialised form of a machine instance in version 1.
#   \param filename The supposed file name of this machine instance, without
#   extension.
#   \return A machine instance instance, or None if the file format is
#   incorrect.
def importFrom(serialised, filename):
    try:
        return MachineInstance(serialised, filename)
    except (configparser.Error, UM.VersionUpgrade.FormatException, UM.VersionUpgrade.InvalidVersionException):
        return None

##  A representation of a machine instance used as intermediary form for
#   conversion from one format to the other.
class MachineInstance:
    ##  Reads version 1 of the file format, storing it in memory.
    #
    #   \param serialised A string with the contents of a machine instance file,
    #   without extension.
    #   \param filename The supposed file name of this machine instance.
    def __init__(self, serialised, filename):
        self._filename = filename

        config = configparser.ConfigParser(interpolation = None)
        config.read_string(serialised) # Read the input string as config file.

        # Checking file correctness.
        if not config.has_section("general"):
            raise UM.VersionUpgrade.FormatException("No \"general\" section.")
        if not config.has_option("general", "version"):
            raise UM.VersionUpgrade.FormatException("No \"version\" in \"general\" section.")
        if not config.has_option("general", "name"):
            raise UM.VersionUpgrade.FormatException("No \"name\" in \"general\" section.")
        if not config.has_option("general", "type"):
            raise UM.VersionUpgrade.FormatException("No \"type\" in \"general\" section.")
        if int(config.get("general", "version")) != 1: # Explicitly hard-code version 1, since if this number changes the programmer MUST change this entire function.
            raise UM.VersionUpgrade.InvalidVersionException("The version of this machine instance is wrong. It must be 1.")

        self._type_name = config.get("general", "type")
        self._variant_name = config.get("general", "variant", fallback = "empty_variant")
        self._name = config.get("general", "name", fallback = "")
        self._key = config.get("general", "key", fallback = None)
        self._active_profile_name = config.get("general", "active_profile", fallback = "empty_quality")
        self._active_material_name = config.get("general", "material", fallback = "empty_material")

        self._machine_setting_overrides = {}
        for key, value in config["machine_settings"].items():
            self._machine_setting_overrides[key] = value

    ##  Serialises this machine instance as file format version 2.
    #
    #   This is where the actual translation happens in this case.
    #
    #   \return A tuple containing the new filename and a serialised form of
    #   this machine instance, serialised in version 2 of the file format.
    def export(self):
        config = configparser.ConfigParser(interpolation = None) # Build a config file in the form of version 2.

        config.add_section("general")
        config.set("general", "name", self._name)
        config.set("general", "id", self._name)
        config.set("general", "type", self._type_name)
        config.set("general", "version", "2") # Hard-code version 2, since if this number changes the programmer MUST change this entire function.

        import VersionUpgrade21to22 # Import here to prevent circular dependencies.
        has_machine_qualities = self._type_name in VersionUpgrade21to22.VersionUpgrade21to22.VersionUpgrade21to22.machinesWithMachineQuality()
        type_name = VersionUpgrade21to22.VersionUpgrade21to22.VersionUpgrade21to22.translatePrinter(self._type_name)
        active_material = VersionUpgrade21to22.VersionUpgrade21to22.VersionUpgrade21to22.translateProfile(self._active_material_name)
        variant = VersionUpgrade21to22.VersionUpgrade21to22.VersionUpgrade21to22.translateVariant(self._variant_name, type_name)
        variant_materials = VersionUpgrade21to22.VersionUpgrade21to22.VersionUpgrade21to22.translateVariantForMaterials(self._variant_name, type_name)
        active_profile = VersionUpgrade21to22.VersionUpgrade21to22.VersionUpgrade21to22.translateProfile(self._active_profile_name)
        if has_machine_qualities: #This machine now has machine-quality profiles.
            active_profile += "_" + active_material + "_" + variant
            active_material += "_" + variant_materials #That means that the profile was split into multiple.
            current_settings = "empty" #The profile didn't know the definition ID when it was upgraded, so it will have been invalid. Sorry, your current settings are lost now.
        else:
            current_settings = self._name + "_current_settings"

        containers = [
            current_settings,
            active_profile,
            active_material,
            variant,
            type_name
        ]
        config.set("general", "containers", ",".join(containers))

        config.add_section("metadata")
        config.set("metadata", "type", "machine")

        VersionUpgrade21to22.VersionUpgrade21to22.VersionUpgrade21to22.translateSettings(self._machine_setting_overrides)
        config.add_section("values")
        for key, value in self._machine_setting_overrides.items():
            config.set("values", key, str(value))

        output = io.StringIO()
        config.write(output)
        return [self._filename], [output.getvalue()]