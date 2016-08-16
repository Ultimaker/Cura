#coding:utf8
"""
Helper module to get easy access to the path where resources are stored.
This is because the resource location is depended on the packaging method and OS
"""
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import os
import sys
import glob
import platform
import locale

import gettext
import profile
import ConfigParser as configparser

if sys.platform.startswith('darwin'):
	try:
		#Foundation import can crash on some MacOS installs
		from Foundation import *
	except:
		pass

if sys.platform.startswith('darwin'):
	if hasattr(sys, 'frozen'):
		try:
			resourceBasePath = NSBundle.mainBundle().resourcePath()
		except:
			resourceBasePath = os.path.join(os.path.dirname(__file__), "../../../../../")
	else:
		resourceBasePath = os.path.join(os.path.dirname(__file__), "../../resources")
else:
	resourceBasePath = os.path.join(os.path.dirname(__file__), "../../resources")

def getPathForResource(dir, subdir, resource_name):
	assert os.path.isdir(dir), "{p} is not a directory".format(p=dir)
	path = os.path.normpath(os.path.join(dir, subdir, resource_name))
	if not os.path.isfile(path):
		return None
	return path

def getPathForImage(name):
	return getPathForResource(resourceBasePath, 'images', name)

def getPathForMesh(name):
	return getPathForResource(resourceBasePath, 'meshes', name)

def getPathForFirmware(name):
	return getPathForResource(resourceBasePath, 'firmware', name)

def getDefaultMachineProfiles():
	path = os.path.normpath(os.path.join(resourceBasePath, 'machine_profiles', '*.ini'))
	return glob.glob(path)

def setupLocalization(selectedLanguage = None):
	#Default to english
	languages = ['en']

	if selectedLanguage is not None:
		for item in getLanguageOptions():
			if item[1] == selectedLanguage and item[0] is not None:
				languages = [item[0]]
				break
	if languages[0] == 'AUTO':
		languages = ['en']
		defaultLocale = getDefaultLocale()
		if defaultLocale is not None:
			for item in getLanguageOptions():
				if item[0] == 'AUTO':
					continue
				if item[0] is not None and defaultLocale.startswith(item[0]):
					languages = [item[0]]

	locale_path = os.path.normpath(os.path.join(resourceBasePath, 'locale'))
	translation = gettext.translation('Cura', locale_path, languages, fallback=True)
	#translation.ugettext = lambda message: u'#' + message
	translation.install(unicode=True)

def getLanguageOptions():
	return [
		['AUTO', 'Autodetect'],
		['en', 'English'],
		['de', 'Deutsch'],
		['fr', 'French'],
		['tr', 'Turkish'],
		['ru', 'Russian'],
		# ['ko', 'Korean'],
		# ['zh', 'Chinese'],
		# ['nl', 'Nederlands'],
		# ['es', 'Spanish'],
		# ['po', 'Polish']
	]

def getDefaultLocale():
	defaultLocale = None

	# On Windows, we look for the actual UI language, as someone could have
	# an english windows but use a non-english locale.
	if platform.system() == "Windows":
		try:
			import ctypes

			windll = ctypes.windll.kernel32
			defaultLocale = locale.windows_locale[windll.GetUserDefaultUILanguage()]
		except:
			pass

	if defaultLocale is None:
		try:
			defaultLocale = locale.getdefaultlocale()[0]
		except:
			pass

	return defaultLocale

class ProfileIni(object):
	@staticmethod
	def str2bool(str):
		return False if str is None else str.lower() in ['true', 'yes', '1', 'y', 't']

	def __init__(self, ini_file):
		self.ini = ini_file
		self.path = os.path.split(self.ini)[0]
		self.base_name = os.path.splitext(os.path.basename(self.ini))[0]
		if self.base_name == 'profile' or self.base_name == 'material':
			self.base_name = os.path.basename(self.path)
		# Name to show in the UI
		self.name = self._getProfileInfo(ini_file, 'name')
		if self.name is None:
			self.name = self.base_name
		self.full_name = self._getProfileInfo(ini_file, 'full_name')
		if self.full_name is None:
			self.full_name = self.name
		# URL for the profile
		self.url = self._getProfileInfo(ini_file, 'url')
		# Finds the full path to the real profile_file
		self.profile_file = self._findProfileFile()
		# default = The default profile to select
		self.default = self.str2bool(self._getProfileInfo(self.ini, 'default'))
		# disabled = do not make available in the UI
		self.disabled = self.str2bool(self._getProfileInfo(self.ini, 'disabled'))
		# always_visible = Always display in the UI even if it's the only available option
		if self._getProfileInfo(self.ini, 'always_visible') is None:
			self.always_visible = True
		else:
			self.always_visible = self.str2bool(self._getProfileInfo(self.ini, 'always_visible'))
		try:
			self.order = int(self._getProfileInfo(self.ini, 'order'))
		except:
			self.order = 999

	def _findProfileFile(self):
		profile_file = self._getProfileInfo(self.ini, 'profile_file')
		if profile_file is None:
			return self.ini
		else:
			if os.path.exists(profile_file):
				return profile_file
			elif os.path.exists(os.path.join(self.path, profile_file)):
				return os.path.join(self.path, profile_file)
			else:
				return self.ini

	def _getProfileInfo(self, ini_file, key):
		cp = configparser.ConfigParser()
		cp.read(ini_file)
		disabled = False
		if cp.has_option('info', key):
			return cp.get('info', key)
		return None

	def _isInList(self, list):
		""" Check if an option with the same base name already exists in the list """
		for ini in list:
			if ini.base_name == self.base_name:
				return True
		return False

	def getProfileDict(self):
		profile_dict = {}
		cp = configparser.ConfigParser()
		cp.read(self.profile_file)
		for setting in profile.settingsList:
			section = 'profile' if setting.isProfile() else 'alterations'
			if setting.isProfile() or setting.isAlteration():
				if cp.has_option(section, setting.getName()):
					profile_dict[setting.getName()] = cp.get(section, setting.getName())

		return profile_dict

	def __cmp__(self, cmp):
		if self.order < cmp.order:
			return -1
		elif self.order > cmp.order:
			return 1
		else:
			if self.name < cmp.name:
				return -1
			elif self.name == cmp.name:
				return 0
			else:
				return 1

	def __str__ (self):
		return "%s%s: %d" % (self.name, "(disabled)" if self.disabled else "", self.order)

	def __repr__ (self):
		return str(self)

class PrintMaterial(ProfileIni):
	def __init__(self, ini_file):
		super(PrintMaterial, self).__init__(ini_file)

		self.profiles = []
		self.options = []
		self.types = []
		types = self._getProfileInfo(self.ini, 'material_types')

		if types != None:
			for type in types.split('|'):
				self.types.append(type.strip())
		# Comment for the profile
		self.description = self._getProfileInfo(ini_file, 'description')

		self.parseDirectory(self.path)

	def parseDirectory(self, path):
		profile_files = sorted(glob.glob(os.path.join(path, '*/profile.ini')))
		if len(profile_files) > 0:
			for profile_file in profile_files:
				profile_ini = ProfileIni(profile_file)
				if not profile_ini._isInList(self.profiles):
					self.profiles.append(profile_ini)

		option_files = sorted(glob.glob(os.path.join(path, 'option_*.ini')))
		for option_file in option_files:
			option = ProfileIni(option_file)
			if not option._isInList(self.options):
				self.options.append(option)

		self.profiles.sort()
		self.options.sort()

	def addGlobalOptions(self, global_options):
		for option in global_options:
			if not option._isInList(self.options):
				self.options.append(option)
		self.options.sort()

	def __str__ (self):
		return "%s%s: %d - Profiles : %s - Options - %s\n" % (self.name, "(disabled)" if self.disabled else "",
															  self.order, self.profiles, self.options)

def alphaAndExperimental(item):
	has_special = False
	experimental_indicator = '*'
	key = item.name
	if key.startswith(experimental_indicator):
		has_special = True
	return has_special, key.lstrip(experimental_indicator).lower()

def getSimpleModeMaterials():
	machine_type = profile.getMachineSetting('machine_type')
	paths = []
	paths.append(os.path.normpath(os.path.expanduser(os.path.join('~', '.Cura', 'quickprint', machine_type))))
	paths.append(os.path.normpath(os.path.expanduser(os.path.join('~', '.Cura', 'quickprint'))))
	paths.append(os.path.normpath(os.path.join(resourceBasePath, 'quickprint', machine_type)))
	paths.append(os.path.normpath(os.path.join(resourceBasePath, 'quickprint')))

	materials = []
	global_options = []
	for path in paths:
		if os.path.isdir(path):
			option_files = sorted(glob.glob(os.path.join(path, 'option_*.ini')))
			for option_file in option_files:
				option = ProfileIni(option_file)
				if not option._isInList(global_options):
					global_options.append(option)

			material_files = sorted(glob.glob(os.path.join(path, '*/material.ini')))
			if len(material_files) > 0:
				for material_file in material_files:
					material = PrintMaterial(material_file)
					if not material._isInList(materials):
						materials.append(material)
					else:
						for ini in materials:
							if ini.base_name == material.base_name:
								ini.parseDirectory(os.path.split(material_file)[0])
								break

	materials.sort(key=alphaAndExperimental)
	for material in materials:
		material.addGlobalOptions(global_options)

	#print "Materials found for %s :\n%s" % (machine_type, materials)
	return materials
