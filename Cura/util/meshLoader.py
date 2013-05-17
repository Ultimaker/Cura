from __future__ import absolute_import
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

from Cura.util.meshLoaders import stl
from Cura.util.meshLoaders import obj
from Cura.util.meshLoaders import dae
from Cura.util.meshLoaders import amf

def loadSupportedExtensions():
	return ['.stl', '.obj', '.dae', '.amf']

def saveSupportedExtensions():
	return ['.amf', '.stl']

def loadWildcardFilter():
	wildcardList = ';'.join(map(lambda s: '*' + s, loadSupportedExtensions()))
	return "Mesh files (%s)|%s;%s" % (wildcardList, wildcardList, wildcardList.upper())

def saveWildcardFilter():
	wildcardList = ';'.join(map(lambda s: '*' + s, saveSupportedExtensions()))
	return "Mesh files (%s)|%s;%s" % (wildcardList, wildcardList, wildcardList.upper())

#loadMeshes loads 1 or more printableObjects from a file.
# STL files are a single printableObject with a single mesh, these are most common.
# OBJ files usually contain a single mesh, but they can contain multiple meshes
# AMF can contain whole scenes of objects with each object having multiple meshes.
# DAE files are a mess, but they can contain scenes of objects as well as grouped meshes

def loadMeshes(filename):
	ext = filename[filename.rfind('.'):].lower()
	if ext == '.stl':
		return stl.loadScene(filename)
	if ext == '.obj':
		return obj.loadScene(filename)
	if ext == '.dae':
		return dae.loadScene(filename)
	if ext == '.amf':
		return amf.loadScene(filename)
	print 'Error: Unknown model extension: %s' % (ext)
	return []

def saveMeshes(filename, objects):
	ext = filename[filename.rfind('.'):].lower()
	if ext == '.stl':
		stl.saveScene(filename, objects)
		return
	if ext == '.amf':
		amf.saveScene(filename, objects)
		return
	print 'Error: Unknown model extension: %s' % (ext)
