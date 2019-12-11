# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser #To get version numbers from config files.
from typing import Dict, Iterable, List, Optional, Set, Tuple

from UM.VersionUpgrade import VersionUpgrade # Superclass of the plugin.

from . import MachineInstance # To upgrade machine instances.
from . import Preferences #To upgrade preferences.
from . import Profile # To upgrade profiles.

##  Which machines have material-specific profiles in the new version?
#
#   These are the 2.1 machine identities with "has_machine_materials": true in
#   their definitions in Cura 2.2. So these are the machines for which profiles
#   need to split into multiple profiles, one for each material and variant.
#
#   Each machine has the materials and variants listed in which it needs to
#   split, since those might be different per machine.
#
#   This should contain the definition as they are stated in the profiles. The
#   inheritance structure cannot be found at this stage, since the definitions
#   may have changed in later versions than 2.2.
_machines_with_machine_quality = {
    "ultimaker2plus": {
        "materials": { "generic_abs", "generic_cpe", "generic_pla", "generic_pva", "generic_cpe_plus", "generic_nylon", "generic_pc", "generic_tpu" },
        "variants": { "0.25 mm", "0.4 mm", "0.6 mm", "0.8 mm" }
    },
    "ultimaker2_extended_plus": {
        "materials": { "generic_abs", "generic_cpe", "generic_pla", "generic_pva", "generic_cpe_plus", "generic_nylon", "generic_pc", "generic_tpu" },
        "variants": { "0.25 mm", "0.4 mm", "0.6 mm", "0.8 mm" }
    }
} # type: Dict[str, Dict[str, Set[str]]]

##  How to translate material names from the old version to the new.
_material_translations = {
    "PLA": "generic_pla",
    "ABS": "generic_abs",
    "CPE": "generic_cpe",
    "CPE+": "generic_cpe_plus",
    "Nylon": "generic_nylon",
    "PC": "generic_pc",
    "TPU": "generic_tpu",
} # type: Dict[str, str]

##  How to translate material names for in the profile names.
_material_translations_profiles = {
    "PLA": "pla",
    "ABS": "abs",
    "CPE": "cpe",
    "CPE+": "cpep",
    "Nylon": "nylon",
    "PC": "pc",
    "TPU": "tpu",
} # type: Dict[str, str]

##  How to translate printer names from the old version to the new.
_printer_translations = {
    "ultimaker2plus": "ultimaker2_plus"
} # type: Dict[str, str]

_printer_translations_profiles = {
    "ultimaker2plus": "um2p", #Does NOT get included in PLA profiles!
    "ultimaker2_extended_plus": "um2ep" #Has no profiles for CPE+, Nylon, PC and TPU!
} # type: Dict[str, str]

##  How to translate profile names from the old version to the new.
#
#   This must have an entry for every built-in profile, since it also services
#   as a set for which profiles were built-in.
_profile_translations = {
    "Low Quality": "low",
    "Normal Quality": "normal",
    "High Quality": "high",
    "Ulti Quality": "high", #This one doesn't have an equivalent. Map it to high.
    "abs_0.25_normal": "um2p_abs_0.25_normal",
    "abs_0.4_fast": "um2p_abs_0.4_fast",
    "abs_0.4_high": "um2p_abs_0.4_high",
    "abs_0.4_normal": "um2p_abs_0.4_normal",
    "abs_0.6_normal": "um2p_abs_0.6_normal",
    "abs_0.8_normal": "um2p_abs_0.8_normal",
    "cpe_0.25_normal": "um2p_cpe_0.25_normal",
    "cpe_0.4_fast": "um2p_cpe_0.4_fast",
    "cpe_0.4_high": "um2p_cpe_0.4_high",
    "cpe_0.4_normal": "um2p_cpe_0.4_normal",
    "cpe_0.6_normal": "um2p_cpe_0.6_normal",
    "cpe_0.8_normal": "um2p_cpe_0.8_normal",
    "cpep_0.4_draft": "um2p_cpep_0.4_draft",
    "cpep_0.4_normal": "um2p_cpep_0.4_normal",
    "cpep_0.6_draft": "um2p_cpep_0.6_draft",
    "cpep_0.6_normal": "um2p_cpep_0.6_normal",
    "cpep_0.8_draft": "um2p_cpep_0.8_draft",
    "cpep_0.8_normal": "um2p_cpep_0.8_normal",
    "nylon_0.25_high": "um2p_nylon_0.25_high",
    "nylon_0.25_normal": "um2p_nylon_0.25_normal",
    "nylon_0.4_fast": "um2p_nylon_0.4_fast",
    "nylon_0.4_normal": "um2p_nylon_0.4_normal",
    "nylon_0.6_fast": "um2p_nylon_0.6_fast",
    "nylon_0.6_normal": "um2p_nylon_0.6_normal",
    "nylon_0.8_draft": "um2p_nylon_0.8_draft",
    "nylon_0.8_normal": "um2p_nylon_0.8_normal",
    "pc_0.25_high": "um2p_pc_0.25_high",
    "pc_0.25_normal": "um2p_pc_0.25_normal",
    "pc_0.4_fast": "um2p_pc_0.4_fast",
    "pc_0.4_normal": "um2p_pc_0.4_normal",
    "pc_0.6_fast": "um2p_pc_0.6_fast",
    "pc_0.6_normal": "um2p_pc_0.6_normal",
    "pc_0.8_draft": "um2p_pc_0.8_draft",
    "pc_0.8_normal": "um2p_pc_0.8_normal",
    "pla_0.25_normal": "pla_0.25_normal", #Note that the PLA profiles don't get the um2p_ prefix, though they are for UM2+.
    "pla_0.4_fast": "pla_0.4_fast",
    "pla_0.4_high": "pla_0.4_high",
    "pla_0.4_normal": "pla_0.4_normal",
    "pla_0.6_normal": "pla_0.6_normal",
    "pla_0.8_normal": "pla_0.8_normal",
    "tpu_0.25_high": "um2p_tpu_0.25_high",
    "tpu_0.4_normal": "um2p_tpu_0.4_normal",
    "tpu_0.6_fast": "um2p_tpu_0.6_fast"
} # type: Dict[str, str]

##  Settings that are no longer in the new version.
_removed_settings = {
    "fill_perimeter_gaps",
    "support_area_smoothing"
} # type: Set[str]

##  How to translate setting names from the old version to the new.
_setting_name_translations = {
    "remove_overlapping_walls_0_enabled": "travel_compensate_overlapping_walls_0_enabled",
    "remove_overlapping_walls_enabled": "travel_compensate_overlapping_walls_enabled",
    "remove_overlapping_walls_x_enabled": "travel_compensate_overlapping_walls_x_enabled",
    "retraction_hop": "retraction_hop_enabled",
    "skin_overlap": "infill_overlap",
    "skirt_line_width": "skirt_brim_line_width",
    "skirt_minimal_length": "skirt_brim_minimal_length",
    "skirt_speed": "skirt_brim_speed",
    "speed_support_lines": "speed_support_infill",
    "speed_support_roof": "speed_support_interface",
    "support_roof_density": "support_interface_density",
    "support_roof_enable": "support_interface_enable",
    "support_roof_extruder_nr": "support_interface_extruder_nr",
    "support_roof_line_distance": "support_interface_line_distance",
    "support_roof_line_width": "support_interface_line_width",
    "support_roof_pattern": "support_interface_pattern"
} # type: Dict[str, str]

##  Custom profiles become quality_changes. This dictates which quality to base
#   the quality_changes profile on.
#
#   Which quality profile to base the quality_changes on depends on the machine,
#   material and nozzle.
#
#   If a current configuration is missing, fall back to "normal".
_quality_fallbacks = {
    "ultimaker2_plus": {
        "ultimaker2_plus_0.25": {
            "generic_abs": "um2p_abs_0.25_normal",
            "generic_cpe": "um2p_cpe_0.25_normal",
            #No CPE+.
            "generic_nylon": "um2p_nylon_0.25_normal",
            "generic_pc": "um2p_pc_0.25_normal",
            "generic_pla": "pla_0.25_normal",
            "generic_tpu": "um2p_tpu_0.25_high"
        },
        "ultimaker2_plus_0.4": {
            "generic_abs": "um2p_abs_0.4_normal",
            "generic_cpe": "um2p_cpe_0.4_normal",
            "generic_cpep": "um2p_cpep_0.4_normal",
            "generic_nylon": "um2p_nylon_0.4_normal",
            "generic_pc": "um2p_pc_0.4_normal",
            "generic_pla": "pla_0.4_normal",
            "generic_tpu": "um2p_tpu_0.4_normal"
        },
        "ultimaker2_plus_0.6": {
            "generic_abs": "um2p_abs_0.6_normal",
            "generic_cpe": "um2p_cpe_0.6_normal",
            "generic_cpep": "um2p_cpep_0.6_normal",
            "generic_nylon": "um2p_nylon_0.6_normal",
            "generic_pc": "um2p_pc_0.6_normal",
            "generic_pla": "pla_0.6_normal",
            "generic_tpu": "um2p_tpu_0.6_fast",
        },
        "ultimaker2_plus_0.8": {
            "generic_abs": "um2p_abs_0.8_normal",
            "generic_cpe": "um2p_cpe_0.8_normal",
            "generic_cpep": "um2p_cpep_0.8_normal",
            "generic_nylon": "um2p_nylon_0.8_normal",
            "generic_pc": "um2p_pc_0.8_normal",
            "generic_pla": "pla_0.8_normal",
            #No TPU.
        }
    }
} # type: Dict[str, Dict[str, Dict[str, str]]]

##  How to translate variants of specific machines from the old version to the
#   new.
_variant_translations = {
    "ultimaker2_plus": {
        "0.25 mm": "ultimaker2_plus_0.25",
        "0.4 mm": "ultimaker2_plus_0.4",
        "0.6 mm": "ultimaker2_plus_0.6",
        "0.8 mm": "ultimaker2_plus_0.8"
    },
    "ultimaker2_extended_plus": {
        "0.25 mm": "ultimaker2_extended_plus_0.25",
        "0.4 mm": "ultimaker2_extended_plus_0.4",
        "0.6 mm": "ultimaker2_extended_plus_0.6",
        "0.8 mm": "ultimaker2_extended_plus_0.8"
    }
} # type: Dict[str, Dict[str, str]]

##  How to translate variant names for in the profile names.
_variant_translations_profiles = {
    "0.25 mm": "0.25",
    "0.4 mm": "0.4",
    "0.6 mm": "0.6",
    "0.8 mm": "0.8"
} # type: Dict[str, str]

##  Cura 2.2's material profiles use a different naming scheme for variants.
#
#   Getting pretty stressed out by this sort of thing...
_variant_translations_materials = {
    "ultimaker2_plus": {
        "0.25 mm": "ultimaker2_plus_0.25_mm",
        "0.4 mm": "ultimaker2_plus_0.4_mm",
        "0.6 mm": "ultimaker2_plus_0.6_mm",
        "0.8 mm": "ultimaker2_plus_0.8_mm"
    },
    "ultimaker2_extended_plus": {
        "0.25 mm": "ultimaker2_plus_0.25_mm",
        "0.4 mm": "ultimaker2_plus_0.4_mm",
        "0.6 mm": "ultimaker2_plus_0.6_mm",
        "0.8 mm": "ultimaker2_plus_0.8_mm"
    }
} # type: Dict[str, Dict[str, str]]

##  Converts configuration from Cura 2.1's file formats to Cura 2.2's.
#
#   It converts the machine instances and profiles.
class VersionUpgrade21to22(VersionUpgrade):
    ##  Gets the version number from a config file.
    #
    #   In all config files that concern this version upgrade, the version
    #   number is stored in general/version, so get the data from that key.
    #
    #   \param serialised The contents of a config file.
    #   \return The version number of that config file.
    def getCfgVersion(self, serialised: str) -> int:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)
        format_version = int(parser.get("general", "version")) #Explicitly give an exception when this fails. That means that the file format is not recognised.
        setting_version = int(parser.get("metadata", "setting_version", fallback = "0"))
        return format_version * 1000000 + setting_version

    ##  Gets the fallback quality to use for a specific machine-variant-material
    #   combination.
    #
    #   For custom profiles we fall back onto this quality profile, since we
    #   don't know which quality profile it was based on.
    #
    #   \param machine The machine ID of the user's configuration in 2.2.
    #   \param variant The variant ID of the user's configuration in 2.2.
    #   \param material The material ID of the user's configuration in 2.2.
    @staticmethod
    def getQualityFallback(machine: str, variant: str, material: str) -> str:
        if machine not in _quality_fallbacks:
            return "normal"
        if variant not in _quality_fallbacks[machine]:
            return "normal"
        if material not in _quality_fallbacks[machine][variant]:
            return "normal"
        return _quality_fallbacks[machine][variant][material]

    ##  Gets the set of built-in profile names in Cura 2.1.
    #
    #   This is required to test if profiles should be converted to a quality
    #   profile or a quality-changes profile.
    @staticmethod
    def builtInProfiles() -> Iterable[str]:
        return _profile_translations.keys()

    ##  Gets a set of the machines which now have per-material quality profiles.
    #
    #   \return A set of machine identifiers.
    @staticmethod
    def machinesWithMachineQuality() -> Dict[str, Dict[str, Set[str]]]:
        return _machines_with_machine_quality

    ##  Converts machine instances from format version 1 to version 2.
    #
    #   \param serialised The serialised machine instance in version 1.
    #   \param filename The supposed file name of the machine instance, without
    #   extension.
    #   \return A tuple containing the new filename and the serialised machine
    #   instance in version 2, or None if the input was not of the correct
    #   format.
    def upgradeMachineInstance(self, serialised: str, filename: str) -> Optional[Tuple[List[str], List[str]]]:
        machine_instance = MachineInstance.importFrom(serialised, filename)
        if not machine_instance: #Invalid file format.
            return None
        return machine_instance.export()

    ##  Converts preferences from format version 2 to version 3.
    #
    #   \param serialised The serialised preferences file in version 2.
    #   \param filename The supposed file name of the preferences file, without
    #   extension.
    #   \return A tuple containing the new filename and the serialised
    #   preferences in version 3, or None if the input was not of the correct
    #   format.
    def upgradePreferences(self, serialised: str, filename: str) -> Optional[Tuple[List[str], List[str]]]:
        preferences = Preferences.importFrom(serialised, filename)
        if not preferences: #Invalid file format.
            return None
        return preferences.export()

    ##  Converts profiles from format version 1 to version 2.
    #
    #   \param serialised The serialised profile in version 1.
    #   \param filename The supposed file name of the profile, without
    #   extension.
    #   \return A tuple containing the new filename and the serialised profile
    #   in version 2, or None if the input was not of the correct format.
    def upgradeProfile(self, serialised: str, filename: str) -> Optional[Tuple[List[str], List[str]]]:
        profile = Profile.importFrom(serialised, filename)
        if not profile: # Invalid file format.
            return None
        return profile.export()

    ##  Translates a material name for the change from Cura 2.1 to 2.2.
    #
    #   \param material A material name in Cura 2.1.
    #   \return The name of the corresponding material in Cura 2.2.
    @staticmethod
    def translateMaterial(material: str) -> str:
        if material in _material_translations:
            return _material_translations[material]
        return material

    ##  Translates a material name for the change from Cura 2.1 to 2.2 in
    #   quality profile names.
    #
    #   \param material A material name in Cura 2.1.
    #   \return The name of the corresponding material in the quality profiles
    #   in Cura 2.2.
    @staticmethod
    def translateMaterialForProfiles(material: str) -> str:
        if material in _material_translations_profiles:
            return _material_translations_profiles[material]
        return material

    ##  Translates a printer name that might have changed since the last
    #   version.
    #
    #   \param printer A printer name in Cura 2.1.
    #   \return The name of the corresponding printer in Cura 2.2.
    @staticmethod
    def translatePrinter(printer: str) -> str:
        if printer in _printer_translations:
            return _printer_translations[printer]
        return printer #Doesn't need to be translated.

    ##  Translates a printer name for the change from Cura 2.1 to 2.2 in quality
    #   profile names.
    #
    #   \param printer A printer name in 2.1.
    #   \return The name of the corresponding printer in Cura 2.2.
    @staticmethod
    def translatePrinterForProfile(printer: str) -> str:
        if printer in _printer_translations_profiles:
            return _printer_translations_profiles[printer]
        return printer

    ##  Translates a built-in profile name that might have changed since the
    #   last version.
    #
    #   \param profile A profile name in the old version.
    #   \return The corresponding profile name in the new version.
    @staticmethod
    def translateProfile(profile: str) -> str:
        if profile in _profile_translations:
            return _profile_translations[profile]
        return profile #Doesn't need to be translated.

    ##  Updates settings for the change from Cura 2.1 to 2.2.
    #
    #   The keys and values of settings are changed to what they should be in
    #   the new version. Each setting is changed in-place in the provided
    #   dictionary. This changes the input parameter.
    #
    #   \param settings A dictionary of settings (as key-value pairs) to update.
    #   \return The same dictionary.
    @staticmethod
    def translateSettings(settings: Dict[str, str]) -> Dict[str, str]:
        new_settings = {}
        for key, value in settings.items():
            if key in _removed_settings:
                continue
            if key == "retraction_combing": #Combing was made into an enum instead of a boolean.
                new_settings[key] = "off" if (value == "False") else "all"
                continue
            if key == "cool_fan_full_layer": #Layer counting was made one-indexed.
                new_settings[key] = str(int(value) + 1)
                continue
            if key in _setting_name_translations:
                new_settings[_setting_name_translations[key]] = value
                continue
            new_settings[key] = value
        return new_settings

    ##  Translates a setting name for the change from Cura 2.1 to 2.2.
    #
    #   \param setting The name of a setting in Cura 2.1.
    #   \return The name of the corresponding setting in Cura 2.2.
    @staticmethod
    def translateSettingName(setting: str) -> str:
        if setting in _setting_name_translations:
            return _setting_name_translations[setting]
        return setting #Doesn't need to be translated.

    ##  Translates a variant name for the change from Cura 2.1 to 2.2
    #
    #   \param variant The name of a variant in Cura 2.1.
    #   \param machine The name of the machine this variant is part of in Cura
    #   2.2's naming.
    #   \return The name of the corresponding variant in Cura 2.2.
    @staticmethod
    def translateVariant(variant: str, machine: str) -> str:
        if machine in _variant_translations and variant in _variant_translations[machine]:
            return _variant_translations[machine][variant]
        return variant

    ##  Translates a variant name for the change from Cura 2.1 to 2.2 in
    #   material profiles.
    #
    #   \param variant The name of the variant in Cura 2.1.
    #   \param machine The name of the machine this variant is part of in Cura
    #   2.2's naming.
    #   \return The name of the corresponding variant for in material profiles
    #   in Cura 2.2.
    @staticmethod
    def translateVariantForMaterials(variant: str, machine: str) -> str:
        if machine in _variant_translations_materials and variant in _variant_translations_materials[machine]:
            return _variant_translations_materials[machine][variant]
        return variant

    ##  Translates a variant name for the change from Cura 2.1 to 2.2 in quality
    #   profiles.
    #
    #   \param variant The name of the variant in Cura 2.1.
    #   \return The name of the corresponding variant for in quality profiles in
    #   Cura 2.2.
    @staticmethod
    def translateVariantForProfiles(variant: str) -> str:
        if variant in _variant_translations_profiles:
            return _variant_translations_profiles[variant]
        return variant