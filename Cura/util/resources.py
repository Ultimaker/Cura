#coding:utf8
"""
Helper module to get easy access to the path where resources are stored.
This is because the resource location is depended on the packaging method and OS
"""
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import os
import sys
import glob

import gettext

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

def getSimpleModeProfiles():
	path = os.path.normpath(os.path.join(resourceBasePath, 'quickprint', 'profiles', '*.ini'))
	user_path = os.path.normpath(os.path.expanduser(os.path.join('~', '.Cura', 'quickprint', 'profiles')))
	if os.path.isdir(user_path):
		files = sorted(glob.glob(os.path.join(user_path, '*.ini')))
		if len(files) > 0:
			return files
	return sorted(glob.glob(path))

def getSimpleModeMaterials():
	path = os.path.normpath(os.path.join(resourceBasePath, 'quickprint', 'materials', '*.ini'))
	user_path = os.path.normpath(os.path.expanduser(os.path.join('~', '.Cura', 'quickprint', 'materials')))
	if os.path.isdir(user_path):
		files = sorted(glob.glob(os.path.join(user_path, '*.ini')))
		if len(files) > 0:
			return files
	return sorted(glob.glob(path))

def setupLocalization(selectedLanguage = None):
	#Default to english
	languages = ['en']

	if selectedLanguage is not None:
		for item in getLanguageOptions():
			if item[1] == selectedLanguage and item[0] is not None:
				languages = [item[0]]

	locale_path = os.path.normpath(os.path.join(resourceBasePath, 'locale'))
	translation = gettext.translation('Cura', locale_path, languages, fallback=True)
	#translation.ugettext = lambda message: u'#' + message
	translation.install(unicode=True)

def getLanguageOptions():
	return [
		['en', 'English'],
		['de', 'Deutsch'],
		['fr', 'French'],
		['tr', 'Turkish'],
		# ['ko', 'Korean'],
		# ['zh', 'Chinese'],
		# ['nl', 'Nederlands'],
		# ['es', 'Spanish'],
		# ['po', 'Polish']
	]
