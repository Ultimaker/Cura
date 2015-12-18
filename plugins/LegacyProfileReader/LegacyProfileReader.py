# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import configparser #For reading the legacy profile INI files.
import json #For reading the Dictionary of Doom.
import os.path #For concatenating the path to the plugin and the relative path to the Dictionary of Doom.

from UM.Application import Application #To get the machine manager to create the new profile in.
from UM.Logger import Logger #Logging errors.
from UM.PluginRegistry import PluginRegistry #For getting the path to this plugin's directory.
from UM.Settings.Profile import Profile
from UM.Settings.ProfileReader import ProfileReader

##  A plugin that reads profile data from legacy Cura versions.
#
#   It reads a profile from an .ini file, and performs some translations on it.
#   Not all translations are correct, mind you, but it is a best effort.
class LegacyProfileReader(ProfileReader):
    ##  Initialises the legacy profile reader.
    #
    #   This does nothing since the only other function is basically stateless.
    def __init__(self):
        super().__init__()

    ##  Prepares the local variables that can be used in evaluation of computing
    #   new setting values from the old ones.
    #
    #   This fills a dictionary with all settings from the legacy Cura version
    #   and their values, so that they can be used in evaluating the new setting
    #   values as Python code.
    #
    #   \param parser The ConfigParser that finds the settings in the legacy
    #   profile.
    #   \param section The section in the profile where the settings should be
    #   found.
    #   \return A set of local variables, one for each setting in the legacy
    #   profile.
    def prepareLocals(self, parser, section):
        locals = {}
        for option in parser.options(section):
            locals[option] = parser.get(section, option)
        return locals

    ##  Reads a legacy Cura profile from a file and returns it.
    #
    #   \param file_name The file to read the legacy Cura profile from.
    #   \return The legacy Cura profile that was in the file, if any. If the
    #   file could not be read or didn't contain a valid profile, \code None
    #   \endcode is returned.
    def read(self, file_name):
        profile = Profile(machine_manager = Application.getInstance().getMachineManager(), read_only = False) #Create an empty profile.
        profile.setName("Imported Legacy Profile")

        parser = configparser.ConfigParser(interpolation = None)
        try:
            with open(file_name) as f:
                parser.readfp(f) #Parse the INI file.
        except Exception as e:
            Logger.log("e", "Unable to open legacy profile %s: %s", file_name, str(e))
            return None

        #Legacy Cura saved the profile under the section "profile_N" where N is the ID of a machine, except when you export in which case it saves it in the section "profile".
        #Since importing multiple machine profiles is out of scope, just import the first section we find.
        section = ""
        for found_section in parser.sections():
            if found_section.startswith("profile"):
                section = found_section
                break
        if not section: #No section starting with "profile" was found. Probably not a proper INI file.
            return None

        legacy_settings = self.prepareLocals(parser, section) #Gets the settings from the legacy profile.

        try:
            with open(os.path.join(PluginRegistry.getInstance().getPluginPath("LegacyProfileReader"), "DictionaryOfDoom.json"), "r", -1, "utf-8") as f:
                dict_of_doom = json.load(f) #Parse the Dictionary of Doom.    
        except IOError as e:
            Logger.log("e", "Could not open DictionaryOfDoom.json for reading: %s", str(e))
            return None
        except Exception as e:
            Logger.log("e", "Could not parse DictionaryOfDoom.json: %s", str(e))
            return None

        if "translation" not in dict_of_doom:
            Logger.log("e", "Dictionary of Doom has no translation. Is it the correct JSON file?")
            return None
        for new_setting in dict_of_doom["translation"]: #Evaluate all new settings that would get a value from the translations.
            old_setting_expression = dict_of_doom["translation"][new_setting]
            compiled = compile(old_setting_expression, new_setting, "eval")
            new_value = eval(compiled, {}, legacy_settings) #Pass the legacy settings as local variables to allow access to in the evaluation.
            profile.setSettingValue(new_setting, new_value) #Store the setting in the profile!

        return profile