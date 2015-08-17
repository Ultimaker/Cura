#!/usr/bin/python

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
    'ABS': 'ABS',
    'PLA': 'PLA',
    'HIPS': 'HIPS',
    'ninjaflex': 'NinjaFlex',
    'semiflex': 'SemiFlex',
    'ABS_ninjaflex': 'ABS & NinjaFlex',
    'ABS_semiflex': 'ABS & SemiFlex',
    'PLA_PVA': 'PLA & PVA',
    'ABS_dual_color': 'ABS & ABS',
    'PLA_dual_color': 'PLA & PLA',
    'PLA_PVA_support': 'PLA & PVA',
}

material_order = {
    'ABS': 2,
    'PLA': 1,
    'HIPS': 0,
    'ninjaflex': 0,
    'semiflex': 1,
    'ABS_ninjaflex': 0,
    'ABS_semiflex': 1,
    'PLA_PVA': 2,
    'ABS_dual_color': 0, 
    'PLA_dual_color': 1,
    'PLA_PVA_support': 2,
}

profile_map = {
    'high-quality': 'Fine',
    'medium-quality': 'Normal',
    'high-speed': 'Fast',
}

profile_order = {
    'high-quality': 0,
    'medium-quality': 1,
    'high-speed': 2,
}

disable_materials = {
    'PET': ('High', 'Low', 'Normal', 'Ulti'),
    'PLA': ('High', 'Low', 'Normal', 'Ulti'),
    'ABS': ('High', 'Low', 'Normal', 'Ulti')
}

def split_profile(filename):
    material = None
    profile = None
    for m in material_map.keys():
        if filename.startswith(m):
            material = m
            for p in profile_map.keys():
                if filename.startswith(m + "_" + p):
                    profile = p
                    return (material, profile)
                    
    return (material, profile)

def create_machine_type(machine_type, path, dir):
    files = glob.glob(os.path.join(path, "*.ini"))
    path = os.path.join(CURA_QUICKPRINT_DIR, machine_type)
    for file in files:
        filename = os.path.basename(file)
        (material, profile) = split_profile(filename)
        if material is None or profile is None:
            continue
        profile_file = os.path.join("..", "..", "..", PROFILES_DIR, dir, filename)
        if not os.path.exists(os.path.join(path, material, profile)):
            os.makedirs(os.path.join(path, material, profile))
        with open(os.path.join(path, material, 'material.ini'), 'w') as f:
            f.write("[info]\n")
            f.write("name = %s\n" % material_map[material])
            f.write("order = %d\n" % material_order[material])
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


if __name__ == '__main__':
	main()
