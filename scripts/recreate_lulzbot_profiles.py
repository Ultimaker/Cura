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
	#Profile location/directory name: machine name in Cura
	"Mini_single_extruder_v2": ("lulzbot_mini",),
	"Mini_flexystruder_v2": ("lulzbot_mini_flexystruder",),
	
	"TAZ_single_extruder_0.35nozzle": ("lulzbot_TAZ_4_SingleV1",
									   "lulzbot_TAZ_5_SingleV1",
									   "lulzbot_TAZ_4_035nozzle",
									   "lulzbot_TAZ_5_035nozzle"),
	"TAZ_single_extruder_0.5nozzle": ("lulzbot_TAZ_4_05nozzle",
									  "lulzbot_TAZ_5_05nozzle"),
	"TAZ_dual_extruder_v1": ("lulzbot_TAZ_4_DualV1",
							 "lulzbot_TAZ_5_DualV1"),
	"TAZ_dual_extruder_v2": ("lulzbot_TAZ_4_DualV2",
							 "lulzbot_TAZ_5_DualV2"),
	"TAZ_flexystruder_v1": ("lulzbot_TAZ_4_FlexystruderV1",
							"lulzbot_TAZ_5_FlexystruderV1"),
	"TAZ_flexystruder_v2": ("lulzbot_TAZ_4_FlexystruderV2",
							"lulzbot_TAZ_5_FlexystruderV2"),
	"TAZ_flexy_dually_v1": ("lulzbot_TAZ_4_FlexyDuallyV1",
							"lulzbot_TAZ_5_FlexyDuallyV1"),
	"TAZ_flexy_dually_v2": ("lulzbot_TAZ_4_FlexyDuallyV2",
							"lulzbot_TAZ_5_FlexyDuallyV2"),
	"TAZ5_moarstruder_v2": ("lulzbot_TAZ_5_Moarstruder_v2",),
		
	"TAZ6_single_extruder_v2.1": ("lulzbot_TAZ_6_Single_v2.1",),
	"TAZ6_flexystruder_v2": ("lulzbot_TAZ_6_Flexystruder_v2",),
	"TAZ6_dual_extruder_v2": ("lulzbot_TAZ_6_Dual_v2",),
	"TAZ6_flexy_dually_v2": ("lulzbot_TAZ_6_FlexyDually_v2",),
	"TAZ6_moarstruder_v2": ("lulzbot_TAZ_6_Moarstruder_v2",),
}

material_map = {
	# Beginner
	"HIPS_eSUN": "HIPS",
	"PLA_eSUN": "PLA",
	"PLA_VP": "PLA",
	"PLA_verbatim": "PLA",
	"nGen": "nGen",
	"PLA_PHA": "PLA-PHA",
	"PLA_poly": "PLA-polylite",
	
	# Intermediate
	"ABS_VP": "ABS",
	"Laybrick": "laybrick",
	"PP-Iron": "protopasta-metal-filled",
	"PP-Steel": "protopasta-metal-filled",
	"Bamboofill": "bamboofill",
	"Woodfill": "woodfill",
	"Corkfill": "corkfill",
	"PP-Coffee": "protopasta-aromatic-coffee-PLA",
	"PP-HT-PLA": "protopasta-high-temp-PLA",
	
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
	"Bronzefill": "colorfabb-metal-filled",
	"Copperfill": "colorfabb-metal-filled",
	
	# Expert
	"PP-Conductive": "protopasta-conductive-PLA",
	"HIPS_VP": "HIPS",
	"PC_VP": "polycarbonate",
	"618-Nylon": "618-nylon",
	"645-Nylon": "645-nylon",
	
	# Flexystruder (Expert)
	"ninjaflex": "ninjaflex",
	"cheetah": "cheetah",
	"semiflex": "semiflex",

	# Dual extruder (Expert)
	"PLA_PVA": "PLA-PVA-support",
	"ABS_ABS": "ABS-ABS",
	"PLA_PLA": "PLA-PLA",
	"910_PVA": "910-PVA-support",
	"ABS_HIPS": "ABS-HIPS",
	"HIPS_HIPS": "HIPS-HIPS",
	"PCTPE_PVA": "PCTPE-PVA-support",
	"BRIDGE_PVA": "Bridge-PVA-support",
	"NGEN-NGEN": "nGen-nGen",
	"INOVA-INOVA": "CS-INOVA-1800-CS-INOVA-1800",
	"ABS_BRIDGE": "ABS-Bridge",

	# Flexy Dually (Expert)
	"ABS_ninjaflex": "ABS-ninjaflex",
	"ABS_semiflex": "ABS-semiflex",
	"ABS_cheetah": "ABS-cheetah",
	"HIPS_cheetah": "HIPS-cheetah",
	"HIPS_ninjaflex": "HIPS-ninjaflex",
	"HIPS_semiflex": "HIPS-semiflex",
	"PLA_PVA": "PLA-PVA-support",
	"INOVA_ninjaflex": "CS-INOVA-1800-ninjaflex",
	"NGEN_ninjaflex": "nGen-ninjaflex",
	"NGEN_semiflex": "nGen-semiflex",
	"INOVA_semiflex": "CS-INOVA-1800-semiflex",
	"ABS_scaffold": "ABS-scaffold-support",
	"HIPS_scaffold": "HIPS-scaffold-support",
	
	#Experimental
	"HT": "HT-5300",
	"b-pet": "b-pet",
	"PC-MAX": "polymaker-PC-MAX",
	"wood-bamboo": "woodFill-bambooFill",
	"polyflex": "polyflex",
	"armadillo": "armadillo",
	"brassfill": "colorfabb-metal-filled",
	"silk": "silk",
	"linen": "linen",
}

material_order = {
	# Beginner
	"nGen":                 0,
	"PLA_VP":               1,
	"HIPS_eSUN":            2,
	"PLA_eSUN":             3,
	"PLA_PHA":              4,
	"PLA_verbatim":         5,
	"PLA_poly":          	6,
	
	# Intermediate
	"ABS_VP":              10,
	"Laybrick":            11,
	"PP-Iron":             12,
	"PP-Steel":            13,
	"Bamboofill":          14,
	"Woodfill":            15,
	"Corkfill":            16,
	"PP-Coffee":           17,
	"PP-HT-PLA":           18,
	
	# Advanced
	"INOVA-1800":          50,
	"Alloy910":            51,
	"Bridge":              52,
	"Laywood":             53,
	"n-vent":              54,
	"XT":                  55,
	"PCTPE":               56,
	"PC-ABS":              57,
	"T-Glase":             58,
	"Bronzefill":          59,
	"Copperfill":          60,
	
	# Expert
	"PP-Conductive":      500,
	"HIPS_VP":            501,
	"PC_VP":              502,
	"618-Nylon":          503,
	"645-Nylon":          504,
	
	# Flexystruder (Expert)
	"ninjaflex":            0,
	"cheetah":              1,
	"semiflex":             2,
	
	# Dual extruder (Expert)
	"PLA_PLA":             20,
	"ABS_ABS":             21,
	"PLA_PVA":             22,
	"910_PVA":             23,
	"ABS_HIPS":            24,
	"HIPS_HIPS":           25,
	"PCTPE_PVA":           26,
	"BRIDGE_PVA":          27,
	"NGEN-NGEN":           28,
	"INOVA-INOVA":         29,
	"ABS_BRIDGE":          30,

	# Flexy Dually (Expert)
	"ABS_ninjaflex":      100,
	"ABS_semiflex":       101,
	"ABS_cheetah":        102,
	"HIPS_cheetah":       103,
	"HIPS_ninjaflex":     104,
	"HIPS_semiflex":      105,
	"PLA_PVA":            106,
	"INOVA_ninjaflex":    107,
	"NGEN_ninjaflex":     108,
	"NGEN_semiflex":      109,
	"INOVA_semiflex":     110,
	"ABS_scaffold":       111,
	"HIPS_scaffold":      112,
	
	#Experimental
	"HT":                5001,
	"b-pet":             5002,
	"PC-MAX":            5003,
	"wood-bamboo":       5004,
	"polyflex":          5006,
	"armadillo":         5007,
	"brassfill":         5008,
	"silk":              5009,
	"linen":             5010,
}

material_types = {
	# Beginner
	"HIPS_eSUN": "Beginner",
	"PLA_eSUN": "Beginner",
	"PLA_VP": "Beginner",
	"nGen": "Beginner",
	"PLA_PHA": "Beginner",
	"PLA_verbatim": "Beginner",
	"PLA_poly": "Beginner",
	
	# Intermediate
	"ABS_VP": "Intermediate",
	"Laybrick": "Intermediate",
	"PP-Iron": "Intermediate",
	"PP-Steel": "Intermediate",
	"Bamboofill": "Intermediate",
	"Woodfill": "Intermediate",
	"Corkfill": "Intermediate",
	"PP-Coffee": "Intermediate",
	"PP-HT-PLA": "Intermediate",
	
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
	"HIPS_VP": "Expert",
	"PC_VP": "Expert",
	"618-Nylon": "Expert",
	"645-Nylon": "Expert",
	
	# Flexystruder (Expert)
	"ninjaflex": "Expert",
	#"cheetah": "Expert",
	"semiflex": "Expert",
		
	# Dual extruder (Expert)
	"PLA_PVA": "Expert",
	"ABS_ABS": "Expert",
	"PLA_PLA": "Expert",
	"910_PVA": "Expert",
	"ABS_HIPS": "Expert",
	"HIPS_HIPS": "Expert",
	"PCTPE_PVA": "Expert",
	"BRIDGE_PVA": "Expert",
	"NGEN-NGEN": "Expert",
	"INOVA-INOVA": "Expert",
	"ABS_BRIDGE": "Expert",
	
	# Flexy Dually (Expert)
	"ABS_ninjaflex": "Expert",
	"ABS_semiflex": "Expert",
	#"ABS_cheetah": "Expert",
	#"HIPS_cheetah": "Expert",
	"HIPS_semiflex": "Expert",
	"PLA_PVA": "Expert",
	"INOVA_ninjaflex": "Expert",
	"NGEN_ninjaflex": "Expert",
	"NGEN_semiflex": "Expert",
	"INOVA_semiflex": "Expert",
	"ABS_scaffold": "Expert",
	"HIPS_scaffold": "Expert",
	
	# 'Experimental' is assumed when the material has no other category 
}

material_names = {
	# Beginner
	"HIPS_eSUN": "HIPS (eSUN)",
	"PLA_eSUN": "PLA (eSUN)",
	"PLA_VP": "PLA (Village Plastics)",
	"nGen": "nGen (colorFabb)",
	"PLA_PHA": "PLA/PHA (colorFabb)",
	"PLA_verbatim": "PLA (Verbatim)",
	"PLA_poly": "PLA Polylite (Polymaker)",
	
	# Intermediate
	"ABS_VP": "ABS (Village Plastics)",
	"Laybrick": "Laybrick (CC-Products)",
	"PP-Iron": "Magnetic (Proto-pasta)",
	"PP-Steel": "Steel PLA (Proto-pasta)",
	"Bamboofill": "bambooFill (colorFabb)",
	"Woodfill": "woodFill (colorFabb)",
	"Corkfill": "corkFill (colorFabb)",
	"PP-Coffee": "Coffee PLA (Proto-pasta)",
	"PP-HT-PLA": "High Temp PLA (Proto-pasta)",
	
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
	"Bronzefill": "bronzeFill (colorFabb)",
	"Copperfill": "copperFill (colorFabb)",
	
	# Expert
	"PP-Conductive": "Conductive (Proto-pasta)",
	"HIPS_VP": "HIPS (Village Plastics)",
	"PC_VP": "PC (Village Plastics)",
	"618-Nylon": "618 Nylon (Taulman)",
	"645-Nylon": "645 Nylon (Taulman)",
	
	# Flexystruder (Expert)
	"ninjaflex": "NinjaFlex (NinjaTek)",
	"cheetah": "Cheetah (NinjaTek)",
	"semiflex": "SemiFlex (NinjaTek)",
	
	# Dual extruder (Expert)
	"PLA_PVA": "PLA & PVA Support",
	"ABS_ABS": "ABS & ABS",
	"PLA_PLA": "PLA & PLA",
	"910_PVA": "910 & PVA Support",
	"ABS_HIPS": "ABS & HIPS",
	"HIPS_HIPS": "HIPS & HIPS",
	"PCTPE_PVA": "PCTPE & PVA Support",
	"BRIDGE_PVA": "Bridge & PVA Support",
	"NGEN-NGEN": "nGen & nGen",
	"INOVA-INOVA": "INOVA & INOVA",
	"ABS_BRIDGE": "ABS & Bridge",

	# Flexy Dually (Expert)
	"ABS_ninjaflex": "ABS & NinjaFlex",
	"ABS_semiflex": "ABS & SemiFlex",
	"ABS_cheetah": "ABS & Cheetah",
	"HIPS_cheetah": "HIPS & Cheetah",
	"HIPS_ninjaflex": "HIPS & Ninjaflex",
	"HIPS_semiflex": "HIPS & Semiflex",
	"PLA_PVA": "PLA & PVA Support",
	"INOVA_ninjaflex": "INOVA & Ninjaflex",
	"NGEN_ninjaflex": "nGen & Ninjaflex",
	"NGEN_semiflex": "nGen & Semiflex",
	"INOVA_semiflex": "INOVA & Semiflex",
	"ABS_scaffold": "ABS & Scaffold Support",
	"HIPS_scaffold": "HIPS & Scaffold Support",
	
	# Experimental
	"HT": "HT (colorFabb)",
	"b-pet": "B-Pet",
	"PC-MAX": "PC-MAX (Polymaker)",
	"wood-bamboo": "WoodFill & BambooFill",
	"polyflex": "Polyflex (Polymaker)",
	"armadillo": "Armadillo (NinjaTek)",
	"brassfill": "brassFill (colorFabb)",
	"silk": "BioFila Silk (twoBEars)",
	"linen": "BioFila Linen (twoBEars)",
}

material_url = {
	# Beginner
	"HIPS_eSUN": "lulzbot.com/store/filament/hips-esun",
	"PLA_eSUN": "lulzbot.com/store/filament/pla-esun",
	"PLA_VP": "lulzbot.com/store/filament/pla-village",
	"nGen": "lulzbot.com/store/filament/ngen",
#	"PLA_PHA": "",
#	"PLA_verbatim": "",
#	"PLA_poly": "",

	# Intermediate
	"ABS_VP": "lulzbot.com/store/filament/abs",
	"Laybrick": "lulzbot.com/store/filament/laybrick",
	"PP-Iron": "lulzbot.com/store/filament/magnetic-iron-pla",
	"PP-Steel": "lulzbot.com/store/filament/stainless-steel-pla",
	"Bamboofill": "lulzbot.com/store/filament/bamboofill",
	"Woodfill": "lulzbot.com/store/filament/woodfill",
#	"Corkfill": "",
	"PP-Coffee": "lulzbot.com/store/filament/coffee-pla",
#	"PP-HT-PLA": "",

	# Advanced
	"Alloy910": "lulzbot.com/store/filament/alloy-910",
	"Bridge": "lulzbot.com/store/filament/bridge-nylon",
	"Laywood": "lulzbot.com/store/filament/laywoo-d3-laywood",
	"n-vent": "lulzbot.com/store/filament/n-vent",
#	"XT": "",
	"INOVA-1800": "lulzbot.com/store/filament/inova-1800",
	"PCTPE": "lulzbot.com/store/filament/pctpe",
	"PC-ABS": "lulzbot.com/store/filament/pc-abs-alloy",
	"T-Glase": "lulzbot.com/store/filament/t-glase",
	"Bronzefill": "lulzbot.com/store/filament/bronzefill",
	"Copperfill": "lulzbot.com/store/filament/copperfill",

	# Expert
	"PP-Conductive": "lulzbot.com/store/filament/conductive-pla",
	"HIPS_VP": "lulzbot.com/store/filament/hips",
	"PC_VP": "lulzbot.com/store/filament/polycarbonate",
	"618-Nylon": "lulzbot.com/store/filament/nylon-618",
	"645-Nylon": "lulzbot.com/store/filament/nylon-645",

	# Flexystruder (Expert)
	"ninjaflex": "lulzbot.com/store/filament/ninjaflex",
#	"cheetah": "",
	"semiflex": "lulzbot.com/store/filament/semiflex",
	
	# Dual extruder (Expert)
	"ABS_ABS": "lulzbot.com/store/filament/abs",
	"PLA_PLA": "lulzbot.com/store/filament/pla-esun",
	"PLA_PVA": "lulzbot.com/store/filament/natural-pva",
	"ABS_HIPS": "lulzbot.com/store/filament/abs",
	"HIPS_HIPS": "lulzbot.com/store/filament/hips",
	"PCTPE_PVA": "lulzbot.com/store/filament/pctpe",
	"BRIDGE_PVA": "lulzbot.com/store/filament/bridge-nylon",
#	"NGEN-NGEN": "",
	"INOVA-INOVA": "lulzbot.com/store/filament/inova-1800",
#	"ABS_BRIDGE": "",

	# Flexy Dually (Expert)
	"ABS_ninjaflex": "lulzbot.com/store/filament/ninjaflex",
	"ABS_semiflex": "lulzbot.com/store/filament/semiflex",
#	"ABS_cheetah": "",
#	"HIPS_cheetah": "",
	"HIPS_ninjaflex": "lulzbot.com/store/filament/ninjaflex",
	"HIPS_semiflex": "lulzbot.com/store/filament/semiflex",
	"PLA_PVA": "lulzbot.com/store/filament/natural-pva",
	"INOVA_ninjaflex": "lulzbot.com/store/filament/inova-1800",
#	"NGEN_ninjaflex": "",
#	"NGEN_semiflex": "",
#	"INOVA_semiflex": "",
#	"ABS_scaffold": "",
#	"HIPS_scaffold": "",

	# Experimental
#	"HT": "",
#	"b-pet": "",
#	"PC-MAX": "",
#	"wood-bamboo": "",
#	"polyflex": "",
#	"armadillo": "",
#	"brassfill": "",
#	"silk": "",
#	"linen": "",
}

bed_prep_materials = {
	"ninjaflex",
	"cheetah",
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
	"PC-ABS",
}

profile_map = {
	"medium-quality": "Standard",
	"high-speed": "High speed",
	"high-quality": "High detail",
	"high-clarity": "High clarity",
	"high-strength": "High strength",
	"spiral-vase": "Spiral vase",
}

profile_order = {
	"medium-quality": 0,
	"high-speed": 1,
	"high-quality": 2,
	"high-clarity": 3,
	"high-strength": 4,
	"spiral-vase": 5,
}

disable_materials = {
	"PET": ("High", "Low", "Normal", "Ulti"),
	"PLA": ("High", "Low", "Normal", "Ulti"),
	"ABS": ("High", "Low", "Normal", "Ulti")
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

def is_experimental(material, toolhead_type):
	answer = material not in material_types
	if "Moar" in toolhead_type:
		special_exclusions = {"PCTPE", "Alloy910", "PC_VP"}
		if material in special_exclusions:
			answer = True
	return answer

def get_material_display_name(material, machine_type):
	material_name = ""
	if is_experimental(material, machine_type):
		material_name += "* "
	material_name += material_names[material]
	return material_name

def get_description(material, machine_type):
	description_data = ""
	if is_experimental(material, machine_type):
		description_data = \
			"* Experimental profile, use at \n" + \
			" your own risk! Newer profiles \n" + \
			" may be available at this URL"
	elif material in bed_prep_materials:
		description_data += \
			"Bed preparation required: \n" + \
			" Apply a PVA-based glue stick \n" + \
			" to bed surface before printing."
	return description_data

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
			with open(os.path.join(path, material, "material.ini"), "w") as f:
				f.write("[info]\n")
				f.write("name = %s\n" % get_material_display_name(material, machine_type))
				order = material_order[material]
				if material_types.has_key(material):
					types = material_types[material]
					if ((material == "PLA_poly" and machine_type.startswith("lulzbot_mini")) or \
						(material == "ABS_VP" and machine_type.startswith("lulzbot_TAZ_4")) or \
						(material == "ABS_VP" and machine_type.startswith("lulzbot_TAZ_5")) or \
						(material == "nGen" and machine_type.startswith("lulzbot_TAZ_6"))):
						types = types + "|First Run"
						order = 0
						f.write("default = 1\n")
				if is_experimental(material, machine_type):
					types = "Experimental"
				f.write("material_types = %s\n" % types)
				f.write("order = %d\n" % order)
				description_data = get_description(material, machine_type)
				if description_data is not "":
					f.write("description = %s\n" % description_data)
				if material_url.has_key(material):
					referer = "?pk_campaign=software-cura"
					f.write("url = %s%s\n" %(material_url[material], referer) )
				elif is_experimental(material, machine_type):
					f.write("url = %s\n" %("code.alephobjects.com/diffusion/P/") )
			with open(os.path.join(path, material, profile, "profile.ini"), "w") as f:
				f.write("[info]\n")
				f.write("name = %s\n" % profile_map[profile])
				f.write("order = %d\n" % profile_order[profile])
				f.write("profile_file = %s\n" % profile_file)
	for material in disable_materials.keys():
		if os.path.exists(os.path.join(path, material)):
			for profile in disable_materials[material]:
				if not os.path.exists(os.path.join(path, material, profile)):
					os.makedirs(os.path.join(path, material, profile))
					with open(os.path.join(path, material, profile, "profile.ini"), "w") as f:
						f.write("[info]\n")
						f.write("disabled = true\n")
		else:
			os.makedirs(os.path.join(path, material))
			with open(os.path.join(path, material, "material.ini"), "w") as f:
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


if __name__ == "__main__":
	main()
