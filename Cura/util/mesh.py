from __future__ import absolute_import
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import time
import math
import os

import numpy
numpy.seterr(all='ignore')

class printableObject(object):
	def __init__(self, originFilename):
		self._originFilename = originFilename
		if originFilename is None:
			self._name = 'None'
		else:
			self._name = os.path.basename(originFilename)
		if '.' in self._name:
			self._name = self._name[0:self._name.rfind('.')]
		self._meshList = []
		self._position = numpy.array([0.0, 0.0])
		self._matrix = numpy.matrix([[1,0,0],[0,1,0],[0,0,1]], numpy.float64)
		self._transformedMin = None
		self._transformedMax = None
		self._transformedSize = None
		self._boundaryCircleSize = None
		self._drawOffset = None
		self._loadAnim = None

	def copy(self):
		ret = printableObject(self._originFilename)
		ret._matrix = self._matrix.copy()
		ret._transformedMin = self._transformedMin.copy()
		ret._transformedMax = self._transformedMin.copy()
		ret._transformedSize = self._transformedSize.copy()
		ret._boundaryCircleSize = self._boundaryCircleSize
		ret._drawOffset = self._drawOffset.copy()
		for m in self._meshList[:]:
			m2 = ret._addMesh()
			m2.vertexes = m.vertexes
			m2.vertexCount = m.vertexCount
			m2.vbo = m.vbo
			m2.vbo.incRef()
		return ret

	def _addMesh(self):
		m = mesh(self)
		self._meshList.append(m)
		return m

	def _postProcessAfterLoad(self):
		for m in self._meshList:
			m._calculateNormals()
		self.processMatrix()

	def applyMatrix(self, m):
		self._matrix *= m
		self.processMatrix()

	def processMatrix(self):
		self._transformedMin = numpy.array([999999999999,999999999999,999999999999], numpy.float64)
		self._transformedMax = numpy.array([-999999999999,-999999999999,-999999999999], numpy.float64)
		self._boundaryCircleSize = 0

		for m in self._meshList:
			transformedVertexes = m.getTransformedVertexes()
			transformedMin = transformedVertexes.min(0)
			transformedMax = transformedVertexes.max(0)
			for n in xrange(0, 3):
				self._transformedMin[n] = min(transformedMin[n], self._transformedMin[n])
				self._transformedMax[n] = max(transformedMax[n], self._transformedMax[n])

			#Calculate the boundary circle
			transformedSize = transformedMax - transformedMin
			center = transformedMin + transformedSize / 2.0
			boundaryCircleSize = round(math.sqrt(numpy.max(((transformedVertexes[::,0] - center[0]) * (transformedVertexes[::,0] - center[0])) + ((transformedVertexes[::,1] - center[1]) * (transformedVertexes[::,1] - center[1])) + ((transformedVertexes[::,2] - center[2]) * (transformedVertexes[::,2] - center[2])))), 3)
			self._boundaryCircleSize = max(self._boundaryCircleSize, boundaryCircleSize)
		self._transformedSize = self._transformedMax - self._transformedMin
		self._drawOffset = (self._transformedMax + self._transformedMin) / 2
		self._drawOffset[2] = self._transformedMin[2]
		self._transformedMax -= self._drawOffset
		self._transformedMin -= self._drawOffset

	def getName(self):
		return self._name
	def getOriginFilename(self):
		return self._originFilename
	def getPosition(self):
		return self._position
	def setPosition(self, newPos):
		self._position = newPos
	def getMatrix(self):
		return self._matrix

	def getMaximum(self):
		return self._transformedMax
	def getMinimum(self):
		return self._transformedMin
	def getSize(self):
		return self._transformedSize
	def getDrawOffset(self):
		return self._drawOffset
	def getBoundaryCircle(self):
		return self._boundaryCircleSize

	def mirror(self, axis):
		matrix = [[1,0,0], [0, 1, 0], [0, 0, 1]]
		matrix[axis][axis] = -1
		self.applyMatrix(numpy.matrix(matrix, numpy.float64))

	def getScale(self):
		return numpy.array([
			numpy.linalg.norm(self._matrix[::,0].getA().flatten()),
			numpy.linalg.norm(self._matrix[::,1].getA().flatten()),
			numpy.linalg.norm(self._matrix[::,2].getA().flatten())], numpy.float64);

	def setScale(self, scale, axis, uniform):
		currentScale = numpy.linalg.norm(self._matrix[::,axis].getA().flatten())
		scale /= currentScale
		if scale == 0:
			return
		if uniform:
			matrix = [[scale,0,0], [0, scale, 0], [0, 0, scale]]
		else:
			matrix = [[1.0,0,0], [0, 1.0, 0], [0, 0, 1.0]]
			matrix[axis][axis] = scale
		self.applyMatrix(numpy.matrix(matrix, numpy.float64))

	def setSize(self, size, axis, uniform):
		scale = self.getSize()[axis]
		scale = size / scale
		if scale == 0:
			return
		if uniform:
			matrix = [[scale,0,0], [0, scale, 0], [0, 0, scale]]
		else:
			matrix = [[1,0,0], [0, 1, 0], [0, 0, 1]]
			matrix[axis][axis] = scale
		self.applyMatrix(numpy.matrix(matrix, numpy.float64))

	def resetScale(self):
		x = 1/numpy.linalg.norm(self._matrix[::,0].getA().flatten())
		y = 1/numpy.linalg.norm(self._matrix[::,1].getA().flatten())
		z = 1/numpy.linalg.norm(self._matrix[::,2].getA().flatten())
		self.applyMatrix(numpy.matrix([[x,0,0],[0,y,0],[0,0,z]], numpy.float64))

	def resetRotation(self):
		x = numpy.linalg.norm(self._matrix[::,0].getA().flatten())
		y = numpy.linalg.norm(self._matrix[::,1].getA().flatten())
		z = numpy.linalg.norm(self._matrix[::,2].getA().flatten())
		self._matrix = numpy.matrix([[x,0,0],[0,y,0],[0,0,z]], numpy.float64)
		self.processMatrix()

	def layFlat(self):
		transformedVertexes = self._meshList[0].getTransformedVertexes()
		minZvertex = transformedVertexes[transformedVertexes.argmin(0)[2]]
		dotMin = 1.0
		dotV = None
		for v in transformedVertexes:
			diff = v - minZvertex
			len = math.sqrt(diff[0] * diff[0] + diff[1] * diff[1] + diff[2] * diff[2])
			if len < 5:
				continue
			dot = (diff[2] / len)
			if dotMin > dot:
				dotMin = dot
				dotV = diff
		if dotV is None:
			return
		rad = -math.atan2(dotV[1], dotV[0])
		self._matrix *= numpy.matrix([[math.cos(rad), math.sin(rad), 0], [-math.sin(rad), math.cos(rad), 0], [0,0,1]], numpy.float64)
		rad = -math.asin(dotMin)
		self._matrix *= numpy.matrix([[math.cos(rad), 0, math.sin(rad)], [0,1,0], [-math.sin(rad), 0, math.cos(rad)]], numpy.float64)


		transformedVertexes = self._meshList[0].getTransformedVertexes()
		minZvertex = transformedVertexes[transformedVertexes.argmin(0)[2]]
		dotMin = 1.0
		dotV = None
		for v in transformedVertexes:
			diff = v - minZvertex
			len = math.sqrt(diff[1] * diff[1] + diff[2] * diff[2])
			if len < 5:
				continue
			dot = (diff[2] / len)
			if dotMin > dot:
				dotMin = dot
				dotV = diff
		if dotV is None:
			return
		if dotV[1] < 0:
			rad = math.asin(dotMin)
		else:
			rad = -math.asin(dotMin)
		self.applyMatrix(numpy.matrix([[1,0,0], [0, math.cos(rad), math.sin(rad)], [0, -math.sin(rad), math.cos(rad)]], numpy.float64))

	def scaleUpTo(self, size):
		vMin = self._transformedMin
		vMax = self._transformedMax

		scaleX1 = (size[0] / 2 - self._position[0]) / ((vMax[0] - vMin[0]) / 2)
		scaleY1 = (size[1] / 2 - self._position[1]) / ((vMax[1] - vMin[1]) / 2)
		scaleX2 = (self._position[0] + size[0] / 2) / ((vMax[0] - vMin[0]) / 2)
		scaleY2 = (self._position[1] + size[1] / 2) / ((vMax[1] - vMin[1]) / 2)
		scaleZ = size[2] / (vMax[2] - vMin[2])
		scale = min(scaleX1, scaleY1, scaleX2, scaleY2, scaleZ)
		if scale > 0:
			self.applyMatrix(numpy.matrix([[scale,0,0],[0,scale,0],[0,0,scale]], numpy.float64))

	#Split splits an object with multiple meshes into different objects, where each object is a part of the original mesh that has
	# connected faces. This is useful to split up plate STL files.
	def split(self, callback):
		ret = []
		for oriMesh in self._meshList:
			ret += oriMesh.split(callback)
		return ret

	def canStoreAsSTL(self):
		return len(self._meshList) < 2

	#getVertexIndexList returns an array of vertexes, and an integer array for each mesh in this object.
	# the integer arrays are indexes into the vertex array for each triangle in the model.
	def getVertexIndexList(self):
		vertexMap = {}
		vertexList = []
		meshList = []
		for m in self._meshList:
			verts = m.getTransformedVertexes(True)
			meshIdxList = []
			for idx in xrange(0, len(verts)):
				v = verts[idx]
				hashNr = int(v[0] * 100) | int(v[1] * 100) << 10 | int(v[2] * 100) << 20
				vIdx = None
				if hashNr in vertexMap:
					for idx2 in vertexMap[hashNr]:
						if numpy.linalg.norm(v - vertexList[idx2]) < 0.001:
							vIdx = idx2
				if vIdx is None:
					vIdx = len(vertexList)
					vertexMap[hashNr] = [vIdx]
					vertexList.append(v)
				meshIdxList.append(vIdx)
			meshList.append(numpy.array(meshIdxList, numpy.int32))
		return numpy.array(vertexList, numpy.float32), meshList

class mesh(object):
	def __init__(self, obj):
		self.vertexes = None
		self.vertexCount = 0
		self.vbo = None
		self._obj = obj

	def _addFace(self, x0, y0, z0, x1, y1, z1, x2, y2, z2):
		n = self.vertexCount
		self.vertexes[n][0] = x0
		self.vertexes[n][1] = y0
		self.vertexes[n][2] = z0
		n += 1
		self.vertexes[n][0] = x1
		self.vertexes[n][1] = y1
		self.vertexes[n][2] = z1
		n += 1
		self.vertexes[n][0] = x2
		self.vertexes[n][1] = y2
		self.vertexes[n][2] = z2
		self.vertexCount += 3
	
	def _prepareFaceCount(self, faceNumber):
		#Set the amount of faces before loading data in them. This way we can create the numpy arrays before we fill them.
		self.vertexes = numpy.zeros((faceNumber*3, 3), numpy.float32)
		self.normal = numpy.zeros((faceNumber*3, 3), numpy.float32)
		self.vertexCount = 0

	def _calculateNormals(self):
		#Calculate the normals
		tris = self.vertexes.reshape(self.vertexCount / 3, 3, 3)
		normals = numpy.cross( tris[::,1 ] - tris[::,0]  , tris[::,2 ] - tris[::,0] )
		lens = numpy.sqrt( normals[:,0]**2 + normals[:,1]**2 + normals[:,2]**2 )
		normals[:,0] /= lens
		normals[:,1] /= lens
		normals[:,2] /= lens
		
		n = numpy.zeros((self.vertexCount / 3, 9), numpy.float32)
		n[:,0:3] = normals
		n[:,3:6] = normals
		n[:,6:9] = normals
		self.normal = n.reshape(self.vertexCount, 3)
		self.invNormal = -self.normal

	def _vertexHash(self, idx):
		v = self.vertexes[idx]
		return int(v[0] * 100) | int(v[1] * 100) << 10 | int(v[2] * 100) << 20

	def _idxFromHash(self, map, idx):
		vHash = self._vertexHash(idx)
		for i in map[vHash]:
			if numpy.linalg.norm(self.vertexes[i] - self.vertexes[idx]) < 0.001:
				return i

	def getTransformedVertexes(self, applyOffsets = False):
		if applyOffsets:
			pos = self._obj._position.copy()
			pos.resize((3))
			pos[2] = self._obj.getSize()[2] / 2
			offset = self._obj._drawOffset.copy()
			offset[2] += self._obj.getSize()[2] / 2
			return (numpy.matrix(self.vertexes, copy = False) * numpy.matrix(self._obj._matrix, numpy.float32)).getA() - offset + pos
		return (numpy.matrix(self.vertexes, copy = False) * numpy.matrix(self._obj._matrix, numpy.float32)).getA()

	def split(self, callback):
		vertexMap = {}

		vertexToFace = []
		for idx in xrange(0, self.vertexCount):
			if (idx % 100) == 0:
				callback(idx * 100 / self.vertexCount)
			vHash = self._vertexHash(idx)
			if vHash not in vertexMap:
				vertexMap[vHash] = []
			vertexMap[vHash].append(idx)
			vertexToFace.append([])

		faceList = []
		for idx in xrange(0, self.vertexCount, 3):
			if (idx % 100) == 0:
				callback(idx * 100 / self.vertexCount)
			f = [self._idxFromHash(vertexMap, idx), self._idxFromHash(vertexMap, idx+1), self._idxFromHash(vertexMap, idx+2)]
			vertexToFace[f[0]].append(idx / 3)
			vertexToFace[f[1]].append(idx / 3)
			vertexToFace[f[2]].append(idx / 3)
			faceList.append(f)

		ret = []
		doneSet = set()
		for idx in xrange(0, len(faceList)):
			if idx in doneSet:
				continue
			doneSet.add(idx)
			todoList = [idx]
			meshFaceList = []
			while len(todoList) > 0:
				idx = todoList.pop()
				meshFaceList.append(idx)
				for n in xrange(0, 3):
					for i in vertexToFace[faceList[idx][n]]:
						if not i in doneSet:
							doneSet.add(i)
							todoList.append(i)

			obj = printableObject(self._obj.getOriginFilename())
			obj._matrix = self._obj._matrix.copy()
			m = obj._addMesh()
			m._prepareFaceCount(len(meshFaceList))
			for idx in meshFaceList:
				m.vertexes[m.vertexCount] = self.vertexes[faceList[idx][0]]
				m.vertexCount += 1
				m.vertexes[m.vertexCount] = self.vertexes[faceList[idx][1]]
				m.vertexCount += 1
				m.vertexes[m.vertexCount] = self.vertexes[faceList[idx][2]]
				m.vertexCount += 1
			obj._postProcessAfterLoad()
			ret.append(obj)
		return ret
