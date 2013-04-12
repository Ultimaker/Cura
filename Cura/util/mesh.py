from __future__ import absolute_import

import time
import math

import numpy
numpy.seterr(all='ignore')

from Cura.util import util3d

class printableObject(object):
	def __init__(self):
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
		ret = printableObject()
		ret._matrix = self._matrix.copy()
		ret._meshList = self._meshList[:]
		ret._transformedMin = self._transformedMin
		ret._transformedMax = self._transformedMin
		ret._transformedSize = self._transformedSize
		ret._boundaryCircleSize = self._boundaryCircleSize
		ret._drawOffset = self._drawOffset
		for m in ret._meshList:
			m.vbo.incRef()
		return ret

	def _addMesh(self):
		m = mesh()
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
			transformedVertexes = (numpy.matrix(m.vertexes, copy = False) * self._matrix).getA()
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
		transformedVertexes = (numpy.matrix(self._meshList[0].vertexes, copy = False) * self._matrix).getA()
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


		transformedVertexes = (numpy.matrix(self._meshList[0].vertexes, copy = False) * self._matrix).getA()
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
		print scaleX1, scaleY1, scaleX2, scaleY2, scaleZ
		scale = min(scaleX1, scaleY1, scaleX2, scaleY2, scaleZ)
		if scale > 0:
			self.applyMatrix(numpy.matrix([[scale,0,0],[0,scale,0],[0,0,scale]], numpy.float64))

class mesh(object):
	def __init__(self):
		self.vertexes = None
		self.vertexCount = 0
		self.vbo = None

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

	def splitToParts(self, callback = None):
		t0 = time.time()

		#print "%f: " % (time.time() - t0), "Splitting a model with %d vertexes." % (len(self.vertexes))
		removeDict = {}
		tree = util3d.AABBTree()
		off = numpy.array([0.0001,0.0001,0.0001])
		for idx in xrange(0, self.vertexCount):
			v = self.vertexes[idx]
			e = util3d.AABB(v-off, v+off)
			q = tree.query(e)
			if len(q) < 1:
				e.idx = idx
				tree.insert(e)
			else:
				removeDict[idx] = q[0].idx
			if callback is not None and (idx % 100) == 0:
				callback(idx)
		#print "%f: " % (time.time() - t0), "Marked %d duplicate vertexes for removal." % (len(removeDict))

		faceList = []
		for idx in xrange(0, self.vertexCount, 3):
			f = [idx, idx + 1, idx + 2]
			if removeDict.has_key(f[0]):
				f[0] = removeDict[f[0]]
			if removeDict.has_key(f[1]):
				f[1] = removeDict[f[1]]
			if removeDict.has_key(f[2]):
				f[2] = removeDict[f[2]]
			faceList.append(f)
		
		#print "%f: " % (time.time() - t0), "Building face lists after vertex removal."
		vertexFaceList = []
		for idx in xrange(0, self.vertexCount):
			vertexFaceList.append([])
		for idx in xrange(0, len(faceList)):
			f = faceList[idx]
			vertexFaceList[f[0]].append(idx)
			vertexFaceList[f[1]].append(idx)
			vertexFaceList[f[2]].append(idx)
		
		#print "%f: " % (time.time() - t0), "Building parts."
		self._vertexFaceList = vertexFaceList
		self._faceList = faceList
		partList = []
		doneSet = set()
		for idx in xrange(0, len(faceList)):
			if not idx in doneSet:
				partList.append(self._createPartFromFacewalk(idx, doneSet))
		#print "%f: " % (time.time() - t0), "Split into %d parts" % (len(partList))
		self._vertexFaceList = None
		self._faceList = None
		return partList

	def _createPartFromFacewalk(self, startFaceIdx, doneSet):
		m = mesh()
		m._prepareVertexCount(self.vertexCount)
		todoList = [startFaceIdx]
		doneSet.add(startFaceIdx)
		while len(todoList) > 0:
			faceIdx = todoList.pop()
			self._partAddFacewalk(m, faceIdx, doneSet, todoList)
		return m

	def _partAddFacewalk(self, part, faceIdx, doneSet, todoList):
		f = self._faceList[faceIdx]
		v0 = self.vertexes[f[0]]
		v1 = self.vertexes[f[1]]
		v2 = self.vertexes[f[2]]
		part.addVertex(v0[0], v0[1], v0[2])
		part.addVertex(v1[0], v1[1], v1[2])
		part.addVertex(v2[0], v2[1], v2[2])
		for f1 in self._vertexFaceList[f[0]]:
			if f1 not in doneSet:
				todoList.append(f1)
				doneSet.add(f1)
		for f1 in self._vertexFaceList[f[1]]:
			if f1 not in doneSet:
				todoList.append(f1)
				doneSet.add(f1)
		for f1 in self._vertexFaceList[f[2]]:
			if f1 not in doneSet:
				todoList.append(f1)
				doneSet.add(f1)
