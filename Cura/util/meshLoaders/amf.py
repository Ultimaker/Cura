from __future__ import absolute_import

import zipfile
try:
	from xml.etree import cElementTree as ElementTree
except:
	from xml.etree import ElementTree

from Cura.util import mesh

def loadScene(filename):
	try:
		zfile = zipfile.ZipFile(filename)
		xml = zfile.read(zfile.namelist()[0])
		zfile.close()
	except zipfile.BadZipfile:
		f = open(filename, "r")
		xml = f.read()
		f.close()
	amf = ElementTree.fromstring(xml)
	if 'unit' in amf.attrib:
		unit = amf.attrib['unit'].lower()
	else:
		unit = 'millimeter'
	if unit == 'millimeter':
		scale = 1.0
	elif unit == 'meter':
		scale = 1000.0
	elif unit == 'inch':
		scale = 25.4
	elif unit == 'feet':
		scale = 304.8
	elif unit == 'micron':
		scale = 0.001
	else:
		print "Unknown unit in amf: %s" % (unit)
		scale = 1.0

	ret = []
	for amfObj in amf.iter('object'):
		obj = mesh.printableObject()
		for amfMesh in amfObj.iter('mesh'):
			vertexList = []
			for vertices in amfMesh.iter('vertices'):
				for vertex in vertices.iter('vertex'):
					for coordinates in vertex.iter('coordinates'):
						v = [0.0,0.0,0.0]
						for t in coordinates:
							if t.tag == 'x':
								v[0] = float(t.text)
							elif t.tag == 'y':
								v[1] = float(t.text)
							elif t.tag == 'z':
								v[2] = float(t.text)
						vertexList.append(v)

			for volume in amfMesh.iter('volume'):
				m = obj._addMesh()
				count = 0
				for triangle in volume.iter('triangle'):
					count += 1
				m._prepareFaceCount(count)

				for triangle in volume.iter('triangle'):
					for t in triangle:
						if t.tag == 'v1':
							v1 = vertexList[int(t.text)]
						elif t.tag == 'v2':
							v2 = vertexList[int(t.text)]
						elif t.tag == 'v3':
							v3 = vertexList[int(t.text)]
							m._addFace(v1[0], v1[1], v1[2], v2[0], v2[1], v2[2], v3[0], v3[1], v3[2])
		obj._postProcessAfterLoad()
		ret.append(obj)

	return ret
