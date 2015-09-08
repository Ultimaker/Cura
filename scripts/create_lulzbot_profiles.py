#!/usr/bin/python
#
# This script is used to generate print profiles for lulzbot printers
# based off of the lulzbot_profiles directory which contains common
# profiles for multiple toolheads.
# To generate profiles or update them, make sure there are no existing profiles
# by doing a rm -rf resources/quickprint/lulzbot_mini* resources/quickprint/lulzbot_TAZ*
# then run the script from the root Cura directory with ./scripts/create_lulzbot_profiles.py
#


import glob
import os
import sys


CURA_QUICKPRINT_DIR="resources/quickprint/"
PROFILES_DIR="lulzbot_profiles"

dir_map = {
    'Mini_single_extruder_v2': ('lulzbot_mini',),
    'Mini_flexystruder_v2': ('lulzbot_mini_flexystruder',),
    'TAZ_single_extruder_0.35nozzle': ('lulzbot_TAZ_4_SingleV1',
                                       'lulzbot_TAZ_5_SingleV1',
                                       'lulzbot_TAZ_4_035nozzle',
                                       'lulzbot_TAZ_5_035nozzle'),
    'TAZ_single_extruder_0.5nozzle': ('lulzbot_TAZ_4_05nozzle',
                                      'lulzbot_TAZ_5_05nozzle'),
    'TAZ_dual_extruder_v1': ('lulzbot_TAZ_4_DualV1',
                             'lulzbot_TAZ_5_DualV1'),
    'TAZ_dual_extruder_v2': ('lulzbot_TAZ_4_DualV2',
                             'lulzbot_TAZ_5_DualV2'),
    'TAZ_flexystruder_v1': ('lulzbot_TAZ_4_FlexystruderV1',
                            'lulzbot_TAZ_5_FlexystruderV1'),
    'TAZ_flexystruder_v2': ('lulzbot_TAZ_4_FlexystruderV2',
                            'lulzbot_TAZ_5_FlexystruderV2'),
    'TAZ_flexy_dually_v1': ('lulzbot_TAZ_4_FlexyDuallyV1',
                            'lulzbot_TAZ_5_FlexyDuallyV1'),
    'TAZ_flexy_dually_v2': ('lulzbot_TAZ_4_FlexyDuallyV2',
                            'lulzbot_TAZ_5_FlexyDuallyV2'),
}

material_map = {
    # Beginner
    "HIPS_eSUN": "HIPS",
    "PLA_eSUN": "PLA",
    "PLA_VP": "PLA",
    # Intermediate
    "ABS_VP": "ABS",
    "Laybrick" : "laybrick",
    "PP_Iron": "PP-magnetic-iron",
    "PP_Iron": "PP_magnetic_iron",
    "PP_Steel": "PP-stainless-steel",
    "PP_Steel": "PP_stainless_steel",
    # Advanced
    "Alloy910": "alloy910",
    "Bridge": "bridge",
    "Laywood": "laywood",
    "n-vent": "n-vent",
    "PCTPE": "PCTPE",
    "PC-ABS": "PC-ABS",
    "T-Glase": "T-Glase",
    # Expert
    "PP-Conductive": "PP_conductive",
    "PP-Conductive": "PP-conductive",
    "HIPS_VP" : "HIPS",
    "PC_VP": "polycarbonate",
    "618-Nylon": "nylon618-645",
    "618-Nylon": "618-645_nylon",
    "645-Nylon": "nylon618-645",
    "645-Nylon": "618-645_nylon",
    # Dual extruder (Expert)
    'PLA_PVA': 'PLA_PVA_support',
    'ABS_ABS': 'ABS_dual_color',
    'PLA_PLA': 'PLA_dual_color',
    # Flexystruder (Expert)
    "ninjaflex" : "ninjaflex",
    "semiflex" : "semiflex",
    # Flexy Dually (Expert)
    "ABS_ninjaflex" : "ABS_ninjaflex",
    "ABS_semiflex" : "ABS_semiflex",
}

material_order = {
    # Beginner
    "HIPS_eSUN": 0,
    "PLA_eSUN": 1,
    "PLA_VP": 2,
    # Intermediate
    "ABS_VP": 10,
    "Laybrick" : 11,
    "PP_Iron": 12,
    "PP_Steel": 13,
    # Advanced
    "Alloy910": 50,
    "Bridge": 51,
    "Laywood": 52,
    "n-vent": 53,
    "PCTPE": 54,
    "PC-ABS": 55,
    "T-Glase": 56,
    # Expert
    "PP-Conductive": 500,
    "HIPS_VP" : 501,
    "PC_VP": 502,
    "618-Nylon": 503,
    "645-Nylon": 504,
    # Dual extruder (Expert)
    'PLA_PVA': 2,
    'ABS_ABS': 1,
    'PLA_PLA': 0,
    # Flexystruder (Expert)
    "ninjaflex" : 0,
    "semiflex" : 1,
    # Flexy Dually (Expert)
    "ABS_ninjaflex" : 0,
    "ABS_semiflex" : 1,
}

material_types = {
    # Beginner
    "HIPS_eSUN": "Beginner",
    "PLA_eSUN": "Beginner",
    "PLA_VP": "Beginner",
    # Intermediate
    "ABS_VP": "Intermediate",
    "Laybrick" : "Intermediate",
    "PP_Iron": "Intermediate",
    "PP_Steel": "Intermediate",
    # Advanced
    "Alloy910": "Advanced",
    "Bridge": "Advanced",
    "Laywood": "Advanced",
    "n-vent": "Advanced",
    "PCTPE": "Advanced",
    "PC-ABS": "Advanced",
    "T-Glase": "Advanced",
    # Expert
    "PP-Conductive": "Expert",
    "HIPS_VP" : "Expert",
    "PC_VP": "Expert",
    "618-Nylon": "Expert",
    "645-Nylon": "Expert",
    # Dual extruder (Expert)
    'PLA_PVA': "Expert",
    'ABS_ABS': "Expert",
    'PLA_PLA': "Expert",
    # Flexystruder (Expert)
    "ninjaflex" : "Expert",
    "semiflex" : "Expert",
    # Flexy Dually (Expert)
    "ABS_ninjaflex" : "Expert",
    "ABS_semiflex" : "Expert",
}

material_names = {
    # Beginner
    "HIPS_eSUN": "HIPS (eSUN)",
    "PLA_eSUN": "PLA (eSUN)",
    "PLA_VP": "PLA (Village Plastics)",
    # Intermediate
    "ABS_VP": "ABS (Village Plastics)",
    "Laybrick" : "Laybrick (CC-Products)",
    "PP_Iron": "Iron PLA (Proto-pasta)",
    "PP_Steel": "Steel PLA (Proto-pasta)",
    # Advanced
    "Alloy910": "Alloy 910 (Taulman)",
    "Bridge": "Bridge Nylon (Taulman)",
    "Laywood": "Laywoo-D3 (CC-Products)",
    "n-vent": "n-vent (Taulman)",
    "PCTPE": "PCTPE (Taulman)",
    "PC-ABS": "PC-ABS (Proto-pasta",
    "T-Glase": "t-glase (Taulman)",
    # Expert
    "PP-Conductive": "Conductive (Proto-pasta)",
    "HIPS_VP" : "HIPS (Village Plastics)",
    "PC_VP": "PC (Village Plastics)",
    "618-Nylon": "618 Nylon (Taulman)",
    "645-Nylon": "645 Nylon (Taulman)",
    # Dual extruder (Expert)
    'PLA_PVA': "PLA & PVA",
    'ABS_ABS': "ABS & ABS",
    'PLA_PLA': "ABS & ABS",
    # Flexystruder (Expert)
    "ninjaflex" : "NinjaFlex (Fenner Drives)",
    "semiflex" : "SemiFlex (Fenner Drives)",
    # Flexy Dually (Expert)
    "ABS_ninjaflex" : "ABS & NinjaFlex",
    "ABS_semiflex" : "ABS & SemiFlex",
}

material_url = {
    # Beginner
    "HIPS_eSUN": "https://www.lulzbot.com/products/hips-3mm-filament-1kg-reel-esun",
    "PLA_eSUN": "https://www.lulzbot.com/products/pla-3mm-filament-1kg-or-500g-reel-esun",
    "PLA_VP": "https://www.lulzbot.com/products/pla-3mm-filament-1kg-reel-village-plastics",
    # Intermediate
    "ABS_VP": "https://www.lulzbot.com/products/abs-3mm-filament-1kg-reel",
    "Laybrick" : "https://www.lulzbot.com/products/laybrick-filament-3mm",
    "PP_Iron": "https://www.lulzbot.com/products/magnetic-iron-pla-3mm-filament-500g-reel-proto-pasta",
    "PP_Steel": "https://www.lulzbot.com/products/stainless-steel-pla-3mm-filament-500g-reel-proto-pasta",
    # Advanced
    "Alloy910": "https://www.lulzbot.com/products/alloy-910-3mm-filament-1lb-reel-taulman",
    "Bridge": "https://www.lulzbot.com/products/taulman-bridge-nylon-3mm-filament-1-pound",
    "Laywood": "https://www.lulzbot.com/products/laywoo-d3-cherry-laywood-3mm-250g-coil-cc-products",
    "n-vent": "https://www.lulzbot.com/products/n-vent-3mm-filament-1lb-taulman",
    "PCTPE": "https://www.lulzbot.com/products/taulman-pctpe-3mm-filament-1-pound",
    "PC-ABS": "https://www.lulzbot.com/products/pc-abs-alloy-3mm-filament-500g-reel-proto-pasta",
    "T-Glase": "https://www.lulzbot.com/products/t-glase-3mm-filament-1lb-reel",
    # Expert
    "PP-Conductive": "https://www.lulzbot.com/products/conductive-pla-3mm-filament-500g-reel-proto-pasta",
    "HIPS_VP" : "https://www.lulzbot.com/products/hips-3mm-filament-1kg-or-5lb-reel-village-plastics",
    "PC_VP": "https://www.lulzbot.com/products/polycarbonate-3mm-filament-1kg-reel",
    "618-Nylon": "https://www.lulzbot.com/products/taulman-618-nylon-3mm-filament-1-pound",
    "645-Nylon": "https://www.lulzbot.com/products/taulman-645-nylon-3mm-filament-1-pound",
    # Dual extruder (Expert)
    'ABS_ABS': "https://www.lulzbot.com/products/abs-3mm-filament-1kg-reel",
    'PLA_PLA': "https://www.lulzbot.com/products/pla-3mm-filament-1kg-or-500g-reel-esun",
    'PLA_PVA': "https://www.lulzbot.com/products/natural-pva-3mm-filament-05kg-reel-esun",
    # Flexystruder (Expert)
    "ninjaflex" : "https://www.lulzbot.com/ninjaflex",
    "semiflex" : "https://www.lulzbot.com/products/semiflex-tpe-thermoplastic-elastomer-3mm-075kg",
    # Flexy Dually (Expert)
    "ABS_ninjaflex" : "https://www.lulzbot.com/ninjaflex",
    "ABS_semiflex" : "https://www.lulzbot.com/products/semiflex-tpe-thermoplastic-elastomer-3mm-075kg",
}

profile_map = {
    'medium-quality': 'Standard',
    'high-speed': 'High Speed',
    'high-quality': 'High Detail',
    'high-clarity': 'High Clarity',
    'high-strength': 'High Strength'
}

profile_order = {
    'medium-quality': 0,
    'high-speed': 1,
    'high-quality': 2,
    'high-clarity': 3,
    'high-strength': 4
}

disable_materials = {
    'PET': ('High', 'Low', 'Normal', 'Ulti'),
    'PLA': ('High', 'Low', 'Normal', 'Ulti'),
    'ABS': ('High', 'Low', 'Normal', 'Ulti')
}

def find_file_for_profile(files, material):
    for file in files:
        filename = os.path.basename(file)
        if filename.startswith(material):
            for p in profile_map.keys():
                if filename.startswith(material + "_" + p):
                    profile = p
                    return (file, material, profile)
    return (None, None, None)
    
def create_machine_type(machine_type, path, dir):
    files = glob.glob(os.path.join(path, "*.ini"))
    path = os.path.join(CURA_QUICKPRINT_DIR, machine_type)
    for m in material_map.keys():
        (file, material, profile) = find_file_for_profile(files, material_map[m])
        material = m
        if file is None or material is None or profile is None:
            continue
        filename = os.path.basename(file)
        profile_file = os.path.join("..", "..", "..", PROFILES_DIR, dir, filename)
        if not os.path.exists(os.path.join(path, material, profile)):
            os.makedirs(os.path.join(path, material, profile))
        with open(os.path.join(path, material, 'material.ini'), 'w') as f:
            f.write("[info]\n")
            f.write("name = %s\n" % material_names[material])
            order = material_order[material]
            if material_types.has_key(material):
                types = material_types[material]
                if (material == "HIPS_eSUN" and machine_type.startswith("lulzbot_mini")) or \
                   (material == "ABS_VP" and machine_type.startswith("lulzbot_TAZ")):
                    types = types + "|First Run"
                    order = 0
                f.write("material_types = %s\n" % types)
            f.write("order = %d\n" % order)
            if material_url.has_key(material):
                f.write("url = %s\n" % material_url[material])
        with open(os.path.join(path, material, profile, 'profile.ini'), 'w') as f:
            f.write("[info]\n")
            f.write("name = %s\n" % profile_map[profile])
            f.write("order = %d\n" % profile_order[profile])
            f.write("profile_file = %s\n" % profile_file)
    for material in disable_materials.keys():
        if os.path.exists(os.path.join(path, material)):
            for profile in disable_materials[material]:
                if not os.path.exists(os.path.join(path, material, profile)):
                    os.makedirs(os.path.join(path, material, profile))
                    with open(os.path.join(path, material, profile, 'profile.ini'), 'w') as f:
                        f.write("[info]\n")
                        f.write("disabled = true\n")
        else:
            os.makedirs(os.path.join(path, material))
            with open(os.path.join(path, material, 'material.ini'), 'w') as f:
                f.write("[info]\n")
                f.write("disabled = true\n")
                

def main():
    if not os.path.exists(CURA_QUICKPRINT_DIR):
        print "Cura path is wrong"
        return -1

    dirs = glob.glob(os.path.join(CURA_QUICKPRINT_DIR, PROFILES_DIR, "*"))

    for d in dirs:
        dir = os.path.basename(d)
        if dir_map.has_key(dir):
            for machine_type in dir_map[dir]:
                create_machine_type(machine_type, d, dir)

    print "All done :D"


if __name__ == '__main__':
    main()
