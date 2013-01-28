from __future__ import absolute_import

import time
import math

import numpy
numpy.seterr(all='ignore')

from Cura.util import util3d

class mesh(object):
	def __init__(self):
		self.vertexes = None
		self.matrix = numpy.matrix([[1,0,0], [0,1,0], [0,0,1]], numpy.float32);
		self.vertexCount = 0

	def addVertex(self, x, y, z):
		n = self.vertexCount
		self.vertexes[n][0] = x
		self.vertexes[n][1] = y
		self.vertexes[n][2] = z
		self.vertexCount += 1
	
	def _prepareVertexCount(self, vertexNumber):
		#Set the amount of faces before loading data in them. This way we can create the numpy arrays before we fill them.
		self.vertexes = numpy.zeros((vertexNumber, 3), numpy.float32)
		self.normal = numpy.zeros((vertexNumber, 3), numpy.float32)
		self.vertexCount = 0

	def _postProcessAfterLoad(self):
		self.processMatrix()
		self._calculateNormals()

	def processMatrix(self):
		transformedVertexes = (numpy.matrix(self.vertexes, copy = False) * self.matrix).getA()
		self.transformedMin = transformedVertexes.min(0)
		self.transformedMax = transformedVertexes.max(0)
		self.transformedSize = self.transformedMax - self.transformedMin

		#Calculate the boundery circle
		center = self.transformedMin + self.transformedSize / 2.0
		self.bounderyCircleSize = round(math.sqrt(numpy.max(((transformedVertexes[::,0] - center[0]) * (transformedVertexes[::,0] - center[0])) + ((transformedVertexes[::,1] - center[1]) * (transformedVertexes[::,1] - center[1])) + ((transformedVertexes[::,2] - center[2]) * (transformedVertexes[::,2] - center[2])))), 3)

	def getMaximum(self):
		return self.transformedMax
	def getMinimum(self):
		return self.transformedMin
	def getSize(self):
		return self.transformedSize

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

