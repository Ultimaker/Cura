#!/usr/bin/python
#
# This script is used to generate print profiles for lulzbot printers
# based off of the lulzbot_profiles directory which contains common
# profiles for multiple toolheads.
# To update profiles, run the script from the root Cura
# directory with ./scripts/recreate_lulzbot_profiles.py
#


import glob
import os
import shutil


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
    "PP-Iron": "protopasta-magnetic-iron",
    "PP-Steel": "protopasta-stainless-steel",
    "Bamboofill": "bamboofill",
    "Woodfill": "woodfill",
    # Advanced
    "Alloy910": "alloy910",
    "Bridge": "bridge",
    "Laywood": "laywood",
    "n-vent": "n-vent",
    "XT": "XT",
    "INOVA-1800": "CS-INOVA-1800",
    "PCTPE": "PCTPE",
    "PC-ABS": "PC-ABS",
    "T-Glase": "t-glase",
    "Bronzefill": "bronzefill",
    "Copperfill": "copperfill",
    # Expert
    "PP-Conductive": "protopasta-conductive-PLA",
    "HIPS_VP" : "HIPS",
    "PC_VP": "polycarbonate",
    "618-Nylon": "618-645-nylon",
    "645-Nylon": "618-645-nylon",
    # Dual extruder (Expert)
    'PLA_PVA': 'PLA-PVA-support',
    'ABS_ABS': 'ABS-ABS',
    'PLA_PLA': 'PLA-PLA',
    # Flexystruder (Expert)
    "ninjaflex" : "ninjaflex",
    "semiflex" : "semiflex",
    # Flexy Dually (Expert)
    "ABS_ninjaflex" : "ABS-ninjaflex",
    "ABS_semiflex" : "ABS-semiflex",

    # Others
    # b-pet
    # tritan
    # PLA-protopasta-conductive-PLA
}

material_order = {
    # Beginner
    "HIPS_eSUN": 0,
    "PLA_eSUN": 1,
    "PLA_VP": 2,
    # Intermediate
    "ABS_VP": 10,
    "Laybrick" : 11,
    "PP-Iron": 12,
    "PP-Steel": 13,
    "Bamboofill":14,
    "Woodfill":15,
    # Advanced
    "Alloy910": 50,
    "Bridge": 51,
    "Laywood": 52,
    "n-vent": 53,
    "XT": 54,
    "INOVA-1800": 55,
    "PCTPE": 56,
    "PC-ABS": 57,
    "T-Glase": 58,
    "Bronzefill":59,
    "Copperfill":60,
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
    "PP-Iron": "Intermediate",
    "PP-Steel": "Intermediate",
    "Bamboofill": "Intermediate",
    "Woodfill": "Intermediate",
    # Advanced
    "Alloy910": "Advanced",
    "Bridge": "Advanced",
    "Laywood": "Advanced",
    "n-vent": "Advanced",
    "XT": "Advanced",
    "INOVA-1800": "Advanced",
    "PCTPE": "Advanced",
    "PC-ABS": "Advanced",
    "T-Glase": "Advanced",
    "Bronzefill": "Advanced",
    "Copperfill": "Advanced",
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
    "PP-Iron": "Magnetic (Proto-pasta)",
    "PP-Steel": "Steel PLA (Proto-pasta)",
    "Bamboofill": "Bamboofill (colorFabb)",
    "Woodfill": "Woodfill (colorFabb)",
    # Advanced
    "Alloy910": "Alloy 910 (Taulman)",
    "Bridge": "Bridge Nylon (Taulman)",
    "Laywood": "Laywoo-D3 (CC-Products)",
    "n-vent": "n-vent (Taulman)",
    "XT": "XT (colorFabb)",
    "INOVA-1800": "INOVA-1800 (ChromaStrand)",
    "PCTPE": "PCTPE (Taulman)",
    "PC-ABS": "PC-ABS (Proto-pasta)",
    "T-Glase": "t-glase (Taulman)",
    "Bronzefill": "Bronzefill (colorFabb)",
    "Copperfill": "Copperfill (colorFabb)",
    # Expert
    "PP-Conductive": "Conductive (Proto-pasta)",
    "HIPS_VP" : "HIPS (Village Plastics)",
    "PC_VP": "PC (Village Plastics)",
    "618-Nylon": "618 Nylon (Taulman)",
    "645-Nylon": "645 Nylon (Taulman)",
    # Dual extruder (Expert)
    'PLA_PVA': "PLA & PVA",
    'ABS_ABS': "ABS & ABS",
    'PLA_PLA': "PLA & PLA",
    # Flexystruder (Expert)
    "ninjaflex" : "NinjaFlex (Fenner Drives)",
    "semiflex" : "SemiFlex (Fenner Drives)",
    # Flexy Dually (Expert)
    "ABS_ninjaflex" : "ABS & NinjaFlex",
    "ABS_semiflex" : "ABS & SemiFlex",
}

bed_prep_materials = {
    "ninjaflex",
    "semiflex",
    "Alloy910",
    "Bridge",
    "n-vent",
    "XT",
    "INOVA-1800",
	"PCTPE",
	"T-Glase",
	"618-Nylon",
	"645-Nylon",
	"PC-ABS"
}

material_url = {
    # Beginner
    "HIPS_eSUN": "lulzbot.com/store/filament/hips-esun",
    "PLA_eSUN": "lulzbot.com/store/filament/pla-esun",
    "PLA_VP": "lulzbot.com/store/filament/pla-village",
    # Intermediate
    "ABS_VP": "lulzbot.com/store/filament/abs",
    "Laybrick" : "lulzbot.com/store/filament/laybrick",
    "PP-Iron": "lulzbot.com/store/filament/magnetic-iron-pla",
    "PP-Steel": "lulzbot.com/store/filament/stainless-steel-pla",
#    "Bamboofill": "",
#    "Woodfill": "",
    # Advanced
    "Alloy910": "lulzbot.com/store/filament/alloy-910",
    "Bridge": "lulzbot.com/store/filament/bridge-nylon",
    "Laywood": "lulzbot.com/store/filament/laywoo-d3-laywood",
    "n-vent": "lulzbot.com/store/filament/n-vent",
#    "XT": "",
    "PCTPE": "lulzbot.com/store/filament/pctpe",
    "PC-ABS": "lulzbot.com/store/filament/pc-abs-alloy",
    "T-Glase": "lulzbot.com/store/filament/t-glase",
#    "Bronzefill": "",
#    "Copperfill": "",
    # Expert
    "PP-Conductive": "lulzbot.com/store/filament/conductive-pla",
    "HIPS_VP" : "lulzbot.com/store/filament/hips",
    "PC_VP": "lulzbot.com/store/filament/polycarbonate",
    "618-Nylon": "lulzbot.com/store/filament/nylon-618",
    "645-Nylon": "lulzbot.com/store/filament/nylon-645",
    # Dual extruder (Expert)
    'ABS_ABS': "lulzbot.com/store/filament/abs",
    'PLA_PLA': "lulzbot.com/store/filament/pla-esun",
    'PLA_PVA': "lulzbot.com/store/filament/natural-pva",
    # Flexystruder (Expert)
    "ninjaflex" : "lulzbot.com/store/filament/ninjaflex",
    "semiflex" : "lulzbot.com/store/filament/semiflex",
    # Flexy Dually (Expert)
    "ABS_ninjaflex" : "lulzbot.com/store/filament/ninjaflex",
    "ABS_semiflex" : "lulzbot.com/store/filament/semiflex",
}

profile_map = {
    'medium-quality': 'Standard',
    'high-speed': 'High speed',
    'high-quality': 'High detail',
    'high-clarity': 'High clarity',
    'high-strength': 'High strength'
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

def find_files_for_material(files, material):
    result = []
    for file in files:
        filename = os.path.basename(file)
        if filename.startswith(material):
            for p in profile_map.keys():
                if filename.startswith(material + "_" + p):
                    profile = p
                    result.append((file, material, profile))
    return result
    
def create_machine_type(machine_type, path, dir):
    files = glob.glob(os.path.join(path, "*.ini"))
    path = os.path.join(CURA_QUICKPRINT_DIR, machine_type)
    for m in material_map.keys():
        result = find_files_for_material(files, material_map[m])
        for (file, material, profile) in result:
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
                if material in bed_prep_materials:
                    f.write("description = \
                    Bed preparation required: \n\
                    Apply a PVA-based glue stick \n\
                    to bed surface before printing.\n")
                if material_url.has_key(material):
                    referer = "?pk_campaign=software-cura"
                    f.write("url = %s%s\n" %(material_url[material], referer) )
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

def clear_quickprint_folders():
    here = os.getcwd()
    quickprint_path = os.path.join(here,CURA_QUICKPRINT_DIR)
    candidates = os.listdir(quickprint_path)
    
    folder_paths = []
    for candidate in candidates:
        if "lulzbot_mini" in candidate or \
           "lulzbot_TAZ" in candidate:
            candidate_path = os.path.join(quickprint_path, candidate)
            if os.path.isdir(candidate_path):
                folder_paths.append(candidate_path)
    for path in folder_paths:
        shutil.rmtree(path)
    if not folder_paths:
        print("No Quickprint folders to delete")
    else:
        print("Quickprint folders deleted")

def main():
    if not os.path.exists(CURA_QUICKPRINT_DIR):
        print "Cura path is wrong"
        return -1

    clear_quickprint_folders()

    dirs = glob.glob(os.path.join(CURA_QUICKPRINT_DIR, PROFILES_DIR, "*"))
 
    for d in dirs:
        dir = os.path.basename(d)
        if dir_map.has_key(dir):
            for machine_type in dir_map[dir]:
                create_machine_type(machine_type, d, dir)

    print "Quickprint profiles regenerated"


if __name__ == '__main__':
    main()
