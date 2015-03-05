from Cura.util.settings import lulzbot_mini_settings

import ConfigParser as configparser
from Cura.util import profile
from Cura.util import resources

class SimpleModeSettings(object):
	# Set the Quickprint settings:
	#
	# Settings Format : Dictionary[machine_type] = machine_settings
	#					Dictionary[None] = other_machine_settings
	#
	# Machine settings Format : List of setting dictionaries
	# Setting dictionary Format: Dictionary['Material'] = material ini filename
	#							 Dictionary['Profile'] = profile ini filename
	#							 Dictionary['Options'] = list of other options ini filenames
	#							 Dictionary['Ini'] = Ini filename to load from extra/ subdir
	#							 Dictionary['Settings'] = Option settings
	# Option settings format : List of tuples ('profile setting', 'value')
	#										  ('profile setting', callable function)
	# Example :
	# settings['prusa_i3'] = [
	#							{'Material': '1_pla', 'Profile': '2_normal', 'Ini': 'normal_pla'},
	#							{'Material': '2_abs', 'Profile': '1_high', 'Ini': 'prusa_i3/high_abs'},
	#							{'Material': '1_pla', 'Options': ['brim', 'support'],
	#							  'Settings': [('support', _('Everywhere')), ('platform_adhesion', 'Brim')]
	#							}
	#						]
	#
	#
	# All the settings in the list of machine settings will be checked. For
	# each of those settings, the list of options will be verified and only the
	# settings in which all the options match will be applied.
	# The 'Settings' key in the dictionary will contain the settings to apply.
	# Those settings will be a a list a tuples of key:value in which the value
	# can be a callable function for greater control
	#
	# For example, a Dictionary with only 'Settings' will always be applied
	# while a setting with {'Brim':True} will only be applied if the printBrim
	# option is enabled, and settings with {'MaterialABS':True, 'TypeHigh':False}
	# will only be applied for Low and Normal quality prints in ABS

	settings = {"lulzbot_mini": lulzbot_mini_settings,
				None: {}}


	@staticmethod
	def getSimpleSettings(profile_setting, material_setting, other_settings):
		simple_settings = {}
		machine_type = profile.getMachineSetting('machine_type')
		if SimpleModeSettings.settings.has_key(machine_type):
			machine_settings = SimpleModeSettings.settings[machine_type]
		else:
			machine_settings = SimpleModeSettings.settings[None]

		for setting_dict in machine_settings:
			settings = setting_dict.get('Settings', None)
			ini = setting_dict.get('Ini', None)
			print_material = setting_dict.get('Material', None)
			print_profile = setting_dict.get('Profile', None)
			print_others = setting_dict.get('Options', None)
			# Check if the material/profile/other options match the settings
			if (print_material is None or print_material == material_setting) and \
			   (print_profile is None or print_profile == profile_setting) and \
			   (print_others is None or len(set(print_others)) == len(set(print_others).intersection(set(other_settings)))):
				if settings:
					for item in settings:
						if len(item) != 2 or not profile.isProfileSetting(item[0]):
							continue
						if hasattr(item[1], '__call__'):
							simple_settings[item[0]] = item[1]()
						else:
							simple_settings[item[0]] = item[1]
				if ini:
					ini_file = resources.getSimpleModeIniFiles('extra', ini + '.ini')
					if len(ini_file) > 0:
						cp = configparser.ConfigParser()
						cp.read(ini_file[0])
						for setting in profile.settingsList:
							if setting.isProfile():
								if cp.has_option('profile', setting.getName()):
									simple_settings[setting.getName()] = cp.get('profile', setting.getName())

		return simple_settings
