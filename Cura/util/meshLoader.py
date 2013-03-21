from __future__ import absolute_import

from Cura.util.meshLoaders import stl
from Cura.util.meshLoaders import obj
from Cura.util.meshLoaders import dae
from Cura.util.meshLoaders import amf

def supportedExtensions():
	return ['.stl', '.obj', '.dae', '.amf']

def wildcardFilter():
	wildcardList = ';'.join(map(lambda s: '*' + s, supportedExtensions()))
	return "Mesh files (%s)|%s;%s" % (wildcardList, wildcardList, wildcardList.upper())

#loadMeshes loads 1 or more printableObjects from a file.
# STL files are a single printableObject with a single mesh, these are most common.
# OBJ files usually contain a single mesh, but they can contain multiple meshes
# AMF can contain whole scenes of objects with each object having multiple meshes.
# DAE files are a mess, but they can contain scenes of objects as well as grouped meshes

def loadMeshes(filename):
	ext = filename[filename.rfind('.'):].lower()
	if ext == '.stl':
		return stl.loadSTLscene(filename)
	if ext == '.obj':
		return obj.objModel().load(filename)
	if ext == '.dae':
		return dae.daeModel().load(filename)
	if ext == '.amf':
		return amf.amfModel().load(filename)
	print 'Error: Unknown model extension: %s' % (ext)
	return []
