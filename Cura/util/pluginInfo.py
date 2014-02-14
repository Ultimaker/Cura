"""
The plugin module contains information about the plugins found for Cura.
It keeps track of a list of installed plugins and the information contained within.
"""
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import os
import sys
import traceback
import platform
import re
import tempfile
import cPickle as pickle

from Cura.util import profile
from Cura.util import resources

_pluginList = None

class pluginInfo(object):
	"""
	Plugin information object. Used to keep track of information about the available plugins in this installation of Cura.
	Each plugin as meta-data associated with it which can be retrieved from this class.
	"""
	def __init__(self, dirname, filename):
		self._dirname = dirname
		self._filename = filename
		self._name = os.path.splitext(os.path.basename(filename))[0]
		self._type = 'unknown'
		self._info = ''
		self._params = []
		with open(os.path.join(dirname, filename), "r") as f:
			for line in f:
				line = line.strip()
				if not line.startswith('#'):
					break
				line = line[1:].split(':', 1)
				if len(line) != 2:
					continue
				if line[0].upper() == 'NAME':
					self._name = line[1].strip()
				elif line[0].upper() == 'INFO':
					self._info = line[1].strip()
				elif line[0].upper() == 'TYPE':
					self._type = line[1].strip()
				elif line[0].upper() == 'DEPEND':
					pass
				elif line[0].upper() == 'PARAM':
					m = re.match('([a-zA-Z][a-zA-Z0-9_]*)\(([a-zA-Z_]*)(?::([^\)]*))?\) +(.*)', line[1].strip())
					if m is not None:
						self._params.append({'name': m.group(1), 'type': m.group(2), 'default': m.group(3), 'description': m.group(4)})
				# else:
				# 	print "Unknown item in plugin meta data: %s %s" % (line[0], line[1])

	def getFilename(self):
		return self._filename

	def getFullFilename(self):
		return os.path.join(self._dirname, self._filename)

	def getType(self):
		return self._type

	def getName(self):
		return self._name

	def getInfo(self):
		return self._info

	def getParams(self):
		return self._params

def getPostProcessPluginConfig():
	try:
		return pickle.loads(str(profile.getProfileSetting('plugin_config')))
	except:
		return []

def setPostProcessPluginConfig(config):
	profile.putProfileSetting('plugin_config', pickle.dumps(config))

def getPluginBasePaths():
	ret = []
	if platform.system() != "Windows":
		ret.append(os.path.expanduser('~/.cura/plugins/'))
	if platform.system() == "Darwin" and hasattr(sys, 'frozen'):
		ret.append(os.path.normpath(os.path.join(resources.resourceBasePath, "plugins")))
	else:
		ret.append(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'plugins')))
	return ret

def getPluginList(pluginType):
	global _pluginList
	if _pluginList is None:
		_pluginList = []
		for basePath in getPluginBasePaths():
			if os.path.isdir(basePath):
				for filename in os.listdir(basePath):
					if filename.startswith('.'):
						continue
					if filename.startswith('_'):
						continue
					if os.path.isdir(os.path.join(basePath, filename)):
						if os.path.exists(os.path.join(basePath, filename, 'script.py')):
							_pluginList.append(pluginInfo(basePath, os.path.join(filename, 'script.py')))
					elif filename.endswith('.py'):
						_pluginList.append(pluginInfo(basePath, filename))
	ret = []
	for plugin in _pluginList:
		if plugin.getType() == pluginType:
			ret.append(plugin)
	return ret

def runPostProcessingPlugins(engineResult):
	pluginConfigList = getPostProcessPluginConfig()
	pluginList = getPluginList('postprocess')

	tempfilename = None
	for pluginConfig in pluginConfigList:
		plugin = None
		for pluginTest in pluginList:
			if pluginTest.getFilename() == pluginConfig['filename']:
				plugin = pluginTest
		if plugin is None:
			continue

		pythonFile = plugin.getFullFilename()

		if tempfilename is None:
			f = tempfile.NamedTemporaryFile(prefix='CuraPluginTemp', delete=False)
			tempfilename = f.name
			f.write(engineResult.getGCode())
			f.close()

		locals = {'filename': tempfilename}
		for param in plugin.getParams():
			value = param['default']
			if param['name'] in pluginConfig['params']:
				value = pluginConfig['params'][param['name']]

			if param['type'] == 'float':
				try:
					value = float(value)
				except:
					value = float(param['default'])

			locals[param['name']] = value
		try:
			execfile(pythonFile, locals)
		except:
			locationInfo = traceback.extract_tb(sys.exc_info()[2])[-1]
			return "%s: '%s' @ %s:%s:%d" % (str(sys.exc_info()[0].__name__), str(sys.exc_info()[1]), os.path.basename(locationInfo[0]), locationInfo[2], locationInfo[1])
	if tempfilename is not None:
		f = open(tempfilename, "r")
		engineResult.setGCode(f.read())
		f.close()
		os.unlink(tempfilename)
	return None
