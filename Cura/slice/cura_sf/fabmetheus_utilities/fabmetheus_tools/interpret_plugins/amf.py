from __future__ import absolute_import

import zipfile
try:
	from xml.etree import cElementTree as ElementTree
except:
	from xml.etree import ElementTree

from fabmetheus_utilities.geometry.geometry_tools import face
from fabmetheus_utilities.geometry.solids import triangle_mesh
from fabmetheus_utilities.vector3 import Vector3

def getCarving(fileName=''):
	"Get the triangle mesh for the dae file."
	return amfModel().load(fileName)

class amfModel(triangle_mesh.TriangleMesh):
	def __init__(self):
		super(amfModel, self).__init__()

	def load(self, filename):
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

		for obj in amf.iter('object'):
			for mesh in obj.iter('mesh'):
				startIndex = len(self.vertexes)
				for vertices in mesh.iter('vertices'):
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
							self.vertexes.append(Vector3(v[0], v[1], v[2]))
				for volume in mesh.iter('volume'):
					for triangle in volume.iter('triangle'):
						f = face.Face()
						f.index = len(self.faces)
						for t in triangle:
							if t.tag == 'v1' or t.tag == 'v2' or t.tag == 'v3':
								f.vertexIndexes.append(startIndex + int(t.text))
						self.faces.append(f)
		return self
