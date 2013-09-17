from __future__ import absolute_import
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import os
import sys

#Cura/util classes should not depend on wx...
import wx
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
		resourceBasePath = os.path.join(os.path.dirname(__file__), "../resources")
else:
	if hasattr(sys, 'frozen'):
		resourceBasePath = os.path.join(os.path.dirname(__file__), "../../resources")
	else:
		resourceBasePath = os.path.join(os.path.dirname(__file__), "../resources")

def getPathForResource(dir, subdir, resource_name):
	assert os.path.isdir(dir), "{p} is not a directory".format(p=dir)
	path = os.path.normpath(os.path.join(dir, subdir, resource_name))
	assert os.path.isfile(path), "{p} is not a file.".format(p=path)
	return path

def getPathForImage(name):
	return getPathForResource(resourceBasePath, 'images', name)

def getPathForMesh(name):
	return getPathForResource(resourceBasePath, 'meshes', name)

def getPathForFirmware(name):
	return getPathForResource(resourceBasePath, 'firmware', name)

def setupLocalization():
	try:
		if sys.platform.startswith('darwin'):
			languages = NSLocale.preferredLanguages()
		else:
			#Using wx.Locale before you created wx.App seems to cause an nasty exception. So default to 'en' at the moment.
			languages = [wx.Locale(wx.LANGUAGE_DEFAULT).GetCanonicalName()]
	except Exception as e:
		languages = ['en']

	locale_path = os.path.normpath(os.path.join(resourceBasePath, 'locale'))
	translation = gettext.translation('Cura', locale_path, languages, fallback=True)
	translation.install(unicode=True)
