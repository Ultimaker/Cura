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

def loadMesh(filename):
	ext = filename[filename.rfind('.'):].lower()
	if ext == '.stl':
		return stl.stlModel().load(filename)
	if ext == '.obj':
		return obj.objModel().load(filename)
	if ext == '.dae':
		return dae.daeModel().load(filename)
	if ext == '.amf':
		return amf.amfModel().load(filename)
	print 'Error: Unknown model extension: %s' % (ext)
	return None

