"""
DAE are COLLADA files.
The DAE reader is a limited COLLADA reader. And has only been tested with DAE exports from SketchUp, http://www.sketchup.com/
The reason for this reader in Cura is that the free version of SketchUp by default does not support any other format that we can read.

http://en.wikipedia.org/wiki/COLLADA
"""
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

from  xml.parsers.expat import ParserCreate
import os

from Cura.util import printableObject

def loadScene(filename):
	loader = daeLoader(filename)
	return [loader.obj]

class daeLoader(object):
	"""
	COLLADA object loader. This class is a bit of a mess, COLLADA files are complex beasts, and this code has only been tweaked to accept
	the COLLADA files exported from SketchUp.

	Parts of this class can be cleaned up and improved by using more numpy.
	"""
	def __init__(self, filename):
		self.obj = printableObject.printableObject(filename)
		self.mesh = self.obj._addMesh()

		r = ParserCreate()
		r.StartElementHandler = self._StartElementHandler
		r.EndElementHandler = self._EndElementHandler
		r.CharacterDataHandler = self._CharacterDataHandler

		self._base = {}
		self._cur = self._base
		self._idMap = {}
		self._geometryList = []
		self._faceCount = 0
		r.ParseFile(open(filename, "r"))
		
		self.vertexCount = 0
		for instance_visual_scene in self._base['collada'][0]['scene'][0]['instance_visual_scene']:
			for node in self._idMap[instance_visual_scene['_url']]['node']:
				self._ProcessNode1(node)
		self.mesh._prepareFaceCount(self._faceCount)
		for instance_visual_scene in self._base['collada'][0]['scene'][0]['instance_visual_scene']:
			for node in self._idMap[instance_visual_scene['_url']]['node']:
				self._ProcessNode2(node)

		scale = float(self._base['collada'][0]['asset'][0]['unit'][0]['_meter']) * 1000
		self.mesh.vertexes *= scale
		
		self._base = None
		self._cur = None
		self._idMap = None
		
		self.obj._postProcessAfterLoad()

	def _ProcessNode1(self, node):
		if 'node' in node:
			for n in node['node']:
				self._ProcessNode1(n)
		if 'instance_geometry' in node:
			for instance_geometry in node['instance_geometry']:
				mesh = self._idMap[instance_geometry['_url']]['mesh'][0]
				if 'triangles' in mesh:
					for triangles in mesh['triangles']:
						self._faceCount += int(triangles['_count'])
				elif 'lines' in mesh:
					pass #Ignore lines
				else:
					print mesh.keys()
		if 'instance_node' in node:
			for instance_node in node['instance_node']:
				self._ProcessNode1(self._idMap[instance_node['_url']])

	def _ProcessNode2(self, node, matrix = None):
		if 'matrix' in node:
			oldMatrix = matrix
			matrix = map(float, node['matrix'][0]['__data'].split())
			if oldMatrix is not None:
				newMatrix = [0]*16
				newMatrix[0] = oldMatrix[0] * matrix[0] + oldMatrix[1] * matrix[4] + oldMatrix[2] * matrix[8] + oldMatrix[3] * matrix[12]
				newMatrix[1] = oldMatrix[0] * matrix[1] + oldMatrix[1] * matrix[5] + oldMatrix[2] * matrix[9] + oldMatrix[3] * matrix[13]
				newMatrix[2] = oldMatrix[0] * matrix[2] + oldMatrix[1] * matrix[6] + oldMatrix[2] * matrix[10] + oldMatrix[3] * matrix[14]
				newMatrix[3] = oldMatrix[0] * matrix[3] + oldMatrix[1] * matrix[7] + oldMatrix[2] * matrix[11] + oldMatrix[3] * matrix[15]
				newMatrix[4] = oldMatrix[4] * matrix[0] + oldMatrix[5] * matrix[4] + oldMatrix[6] * matrix[8] + oldMatrix[7] * matrix[12]
				newMatrix[5] = oldMatrix[4] * matrix[1] + oldMatrix[5] * matrix[5] + oldMatrix[6] * matrix[9] + oldMatrix[7] * matrix[13]
				newMatrix[6] = oldMatrix[4] * matrix[2] + oldMatrix[5] * matrix[6] + oldMatrix[6] * matrix[10] + oldMatrix[7] * matrix[14]
				newMatrix[7] = oldMatrix[4] * matrix[3] + oldMatrix[5] * matrix[7] + oldMatrix[6] * matrix[11] + oldMatrix[7] * matrix[15]
				newMatrix[8] = oldMatrix[8] * matrix[0] + oldMatrix[9] * matrix[4] + oldMatrix[10] * matrix[8] + oldMatrix[11] * matrix[12]
				newMatrix[9] = oldMatrix[8] * matrix[1] + oldMatrix[9] * matrix[5] + oldMatrix[10] * matrix[9] + oldMatrix[11] * matrix[13]
				newMatrix[10] = oldMatrix[8] * matrix[2] + oldMatrix[9] * matrix[6] + oldMatrix[10] * matrix[10] + oldMatrix[11] * matrix[14]
				newMatrix[11] = oldMatrix[8] * matrix[3] + oldMatrix[9] * matrix[7] + oldMatrix[10] * matrix[11] + oldMatrix[11] * matrix[15]
				newMatrix[12] = oldMatrix[12] * matrix[0] + oldMatrix[13] * matrix[4] + oldMatrix[14] * matrix[8] + oldMatrix[15] * matrix[12]
				newMatrix[13] = oldMatrix[12] * matrix[1] + oldMatrix[13] * matrix[5] + oldMatrix[14] * matrix[9] + oldMatrix[15] * matrix[13]
				newMatrix[14] = oldMatrix[12] * matrix[2] + oldMatrix[13] * matrix[6] + oldMatrix[14] * matrix[10] + oldMatrix[15] * matrix[14]
				newMatrix[15] = oldMatrix[12] * matrix[3] + oldMatrix[13] * matrix[7] + oldMatrix[14] * matrix[11] + oldMatrix[15] * matrix[15]
				matrix = newMatrix
		if 'node' in node:
			for n in node['node']:
				self._ProcessNode2(n, matrix)
		if 'instance_geometry' in node:
			for instance_geometry in node['instance_geometry']:
				mesh = self._idMap[instance_geometry['_url']]['mesh'][0]
				
				if 'triangles' in mesh:
					for triangles in mesh['triangles']:
						for input in triangles['input']:
							if input['_semantic'] == 'VERTEX':
								vertices = self._idMap[input['_source']]
						for input in vertices['input']:
							if input['_semantic'] == 'POSITION':
								vertices = self._idMap[input['_source']]
						indexList = map(int, triangles['p'][0]['__data'].split())
						positionList = map(float, vertices['float_array'][0]['__data'].split())

						faceCount = int(triangles['_count'])
						stepSize = len(indexList) / (faceCount * 3)
						for i in xrange(0, faceCount):
							idx0 = indexList[((i * 3) + 0) * stepSize]
							idx1 = indexList[((i * 3) + 1) * stepSize]
							idx2 = indexList[((i * 3) + 2) * stepSize]
							x0 = positionList[idx0*3]
							y0 = positionList[idx0*3+1]
							z0 = positionList[idx0*3+2]
							x1 = positionList[idx1*3]
							y1 = positionList[idx1*3+1]
							z1 = positionList[idx1*3+2]
							x2 = positionList[idx2*3]
							y2 = positionList[idx2*3+1]
							z2 = positionList[idx2*3+2]
							if matrix is not None:
								self.mesh._addFace(
									x0 * matrix[0] + y0 * matrix[1] + z0 * matrix[2] + matrix[3], x0 * matrix[4] + y0 * matrix[5] + z0 * matrix[6] + matrix[7], x0 * matrix[8] + y0 * matrix[9] + z0 * matrix[10] + matrix[11],
									x1 * matrix[0] + y1 * matrix[1] + z1 * matrix[2] + matrix[3], x1 * matrix[4] + y1 * matrix[5] + z1 * matrix[6] + matrix[7], x1 * matrix[8] + y1 * matrix[9] + z1 * matrix[10] + matrix[11],
									x2 * matrix[0] + y2 * matrix[1] + z2 * matrix[2] + matrix[3], x2 * matrix[4] + y2 * matrix[5] + z2 * matrix[6] + matrix[7], x2 * matrix[8] + y2 * matrix[9] + z2 * matrix[10] + matrix[11]
								)
							else:
								self.mesh._addFace(x0, y0, z0, x1, y1, z1, x2, y2, z2)
		if 'instance_node' in node:
			for instance_node in node['instance_node']:
				self._ProcessNode2(self._idMap[instance_node['_url']], matrix)
	
	def _StartElementHandler(self, name, attributes):
		name = name.lower()
		if not name in self._cur:
			self._cur[name] = []
		new = {'__name': name, '__parent': self._cur}
		self._cur[name].append(new)
		self._cur = new
		for k in attributes.keys():
			self._cur['_' + k] = attributes[k]
		
		if 'id' in attributes:
			self._idMap['#' + attributes['id']] = self._cur
		
	def _EndElementHandler(self, name):
		self._cur = self._cur['__parent']

	def _CharacterDataHandler(self, data):
		if len(data.strip()) < 1:
			return
		if '__data' in self._cur:
			self._cur['__data'] += data
		else:
			self._cur['__data'] = data
	
	def _GetWithKey(self, item, basename, key, value):
		input = basename
		while input in item:
			if item[basename]['_'+key] == value:
				return self._idMap[item[input]['_source']]
			basename += "!"
