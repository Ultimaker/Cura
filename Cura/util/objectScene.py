__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"
import random
import numpy

from Cura.util import profile
from Cura.util import polygon

class _objectOrder(object):
	def __init__(self, order, todo):
		self.order = order
		self.todo = todo

class _objectOrderFinder(object):
	def __init__(self, scene, offset, leftToRight, frontToBack, gantryHeight):
		self._scene = scene
		self._offset = offset - numpy.array([0.1,0.1])
		self._objs = scene.objects()
		self._leftToRight = leftToRight
		self._frontToBack = frontToBack
		initialList = []
		for n in xrange(0, len(self._objs)):
			if scene.checkPlatform(self._objs[n]):
				initialList.append(n)
		for n in initialList:
			if self._objs[n].getSize()[2] > gantryHeight and len(initialList) > 1:
				self.order = None
				return
		if len(initialList) == 0:
			self.order = []
			return


		self._hitMap = [None] * (max(initialList)+1)
		for a in initialList:
			self._hitMap[a] = [False] * (max(initialList)+1)
			for b in initialList:
				self._hitMap[a][b] = self._checkHit(a, b)

		#Check if we have 2 files that overlap so that they can never be printed one at a time.
		for a in initialList:
			if self._hitMap[a][b] and self._hitMap[b][a]:
				self.order = None
				return

		initialList.sort(self._objIdxCmp)

		n = 0
		self._todo = [_objectOrder([], initialList)]
		while len(self._todo) > 0:
			n += 1
			current = self._todo.pop()
			#print len(self._todo), len(current.order), len(initialList), current.order
			for addIdx in current.todo:
				if not self._checkHitFor(addIdx, current.order) and not self._checkBlocks(addIdx, current.todo):
					todoList = current.todo[:]
					todoList.remove(addIdx)
					order = current.order[:] + [addIdx]
					if len(todoList) == 0:
						self._todo = None
						self.order = order
						return
					self._todo.append(_objectOrder(order, todoList))
		self.order = None

	def _objIdxCmp(self, a, b):
		scoreA = sum(self._hitMap[a])
		scoreB = sum(self._hitMap[b])
		return scoreA - scoreB

	def _checkHitFor(self, addIdx, others):
		for idx in others:
			if self._hitMap[addIdx][idx]:
				return True
		return False

	def _checkBlocks(self, addIdx, others):
		for idx in others:
			if addIdx != idx and self._hitMap[idx][addIdx]:
				return True
		return False

	#Check if printing one object will cause printhead colission with other object.
	def _checkHit(self, addIdx, idx):
		obj = self._scene._objectList[idx]
		addObj = self._scene._objectList[addIdx]
		return polygon.polygonCollision(obj._headAreaHull + obj.getPosition(), addObj._boundaryHull + addObj.getPosition())

class Scene(object):
	def __init__(self):
		self._objectList = []
		self._sizeOffsets = numpy.array([0.0,0.0], numpy.float32)
		self._machineSize = numpy.array([100,100,100], numpy.float32)
		self._headSizeOffsets = numpy.array([18.0,18.0], numpy.float32)
		self._extruderOffset = [numpy.array([0,0], numpy.float32)] * 4

		#Print order variables
		self._leftToRight = False
		self._frontToBack = True
		self._gantryHeight = 60
		self._oneAtATime = True

	# Physical (square) machine size.
	def setMachineSize(self, machineSize):
		self._machineSize = machineSize

	# Size offsets are offsets caused by brim, skirt, etc.
	def updateSizeOffsets(self, force=False):
		newOffsets = numpy.array(profile.calculateObjectSizeOffsets(), numpy.float32)
		if not force and numpy.array_equal(self._sizeOffsets, newOffsets):
			return
		self._sizeOffsets = newOffsets

		extends = numpy.array([[-newOffsets[0],-newOffsets[1]],[ newOffsets[0],-newOffsets[1]],[ newOffsets[0], newOffsets[1]],[-newOffsets[0], newOffsets[1]]], numpy.float32)
		for obj in self._objectList:
			obj.setPrintAreaExtends(extends)

	#size of the printing head.
	def setHeadSize(self, xMin, xMax, yMin, yMax, gantryHeight):
		self._leftToRight = xMin < xMax
		self._frontToBack = yMin < yMax
		self._headSizeOffsets[0] = min(xMin, xMax)
		self._headSizeOffsets[1] = min(yMin, yMax)
		self._gantryHeight = gantryHeight
		self._oneAtATime = self._gantryHeight > 0

		headArea = numpy.array([[-xMin,-yMin],[ xMax,-yMin],[ xMax, yMax],[-xMin, yMax]], numpy.float32)
		for obj in self._objectList:
			obj.setHeadArea(headArea)

	def setExtruderOffset(self, extruderNr, offsetX, offsetY):
		self._extruderOffset[extruderNr] = numpy.array([offsetX, offsetY], numpy.float32)

	def getObjectExtend(self):
		return self._sizeOffsets + self._headSizeOffsets

	def objects(self):
		return self._objectList

	#Add new object to print area
	def add(self, obj):
		self._findFreePositionFor(obj)
		self._objectList.append(obj)
		self.pushFree()
		if numpy.max(obj.getSize()[0:2]) > numpy.max(self._machineSize[0:2]) * 2.5:
			scale = numpy.max(self._machineSize[0:2]) * 2.5 / numpy.max(obj.getSize()[0:2])
			matrix = [[scale,0,0], [0, scale, 0], [0, 0, scale]]
			obj.applyMatrix(numpy.matrix(matrix, numpy.float64))
		self.updateSizeOffsets(True)

	def remove(self, obj):
		self._objectList.remove(obj)

	#Dual(multiple) extrusion merge
	def merge(self, obj1, obj2):
		self.remove(obj2)
		obj1._meshList += obj2._meshList
		for m in obj2._meshList:
			m._obj = obj1
		obj1.processMatrix()
		obj1.setPosition((obj1.getPosition() + obj2.getPosition()) / 2)
		self.pushFree()

	def pushFree(self):
		n = 1000
		while self._pushFree():
			n -= 1
			if n < 0:
				return

	def arrangeAll(self):
		oldList = self._objectList
		self._objectList = []
		for obj in oldList:
			obj.setPosition(numpy.array([0,0], numpy.float32))
			self.add(obj)

	def centerAll(self):
		minPos = numpy.array([9999999,9999999], numpy.float32)
		maxPos = numpy.array([-9999999,-9999999], numpy.float32)
		for obj in self._objectList:
			pos = obj.getPosition()
			size = obj.getSize()
			minPos[0] = min(minPos[0], pos[0] - size[0] / 2)
			minPos[1] = min(minPos[1], pos[1] - size[1] / 2)
			maxPos[0] = max(maxPos[0], pos[0] + size[0] / 2)
			maxPos[1] = max(maxPos[1], pos[1] + size[1] / 2)
		offset = -(maxPos + minPos) / 2
		for obj in self._objectList:
			obj.setPosition(obj.getPosition() + offset)

	def printOrder(self):
		if self._oneAtATime:
			order = _objectOrderFinder(self, self._headSizeOffsets + self._sizeOffsets, self._leftToRight, self._frontToBack, self._gantryHeight).order
		else:
			order = None
		return order

	def _pushFree(self):
		for a in self._objectList:
			for b in self._objectList:
				if a == b:
					continue
				v = polygon.polygonCollisionPushVector(a._boundaryHull + a.getPosition(), b._boundaryHull + b.getPosition())
				if type(v) is bool:
					continue
				a.setPosition(a.getPosition() + v / 2.0)
				b.setPosition(b.getPosition() - v / 2.0)
				return True
		return False

	#Check if two objects are hitting each-other (+ head space).
	def _checkHit(self, a, b):
		if a == b:
			return False
		if self._oneAtATime:
			return polygon.polygonCollision(a._headAreaHull + a.getPosition(), b._boundaryHull + b.getPosition())
		else:
			return polygon.polygonCollision(a._boundaryHull + a.getPosition(), b._boundaryHull + b.getPosition())

	def checkPlatform(self, obj):
		p = obj.getPosition()
		s = obj.getSize()[0:2] / 2 + self._sizeOffsets
		offsetLeft = 0.0
		offsetRight = 0.0
		offsetBack = 0.0
		offsetFront = 0.0
		extruderCount = len(obj._meshList)
		if profile.getProfileSetting('support_dual_extrusion') == 'Second extruder' and profile.getProfileSetting('support') != 'None':
			extruderCount = max(extruderCount, 2)
		for n in xrange(1, extruderCount):
			if offsetLeft < self._extruderOffset[n][0]:
				offsetLeft = self._extruderOffset[n][0]
			if offsetRight > self._extruderOffset[n][0]:
				offsetRight = self._extruderOffset[n][0]
			if offsetFront < self._extruderOffset[n][1]:
				offsetFront = self._extruderOffset[n][1]
			if offsetBack > self._extruderOffset[n][1]:
				offsetBack = self._extruderOffset[n][1]
		boundLeft = -self._machineSize[0] / 2 + offsetLeft
		boundRight = self._machineSize[0] / 2 + offsetRight
		boundFront = -self._machineSize[1] / 2 + offsetFront
		boundBack = self._machineSize[1] / 2 + offsetBack
		if p[0] - s[0] < boundLeft:
			return False
		if p[0] + s[0] > boundRight:
			return False
		if p[1] - s[1] < boundFront:
			return False
		if p[1] + s[1] > boundBack:
			return False

		#Do clip Check for UM2.
		machine = profile.getMachineSetting('machine_type')
		if machine == "ultimaker2":
			#lowerRight clip check
			if p[0] - s[0] < boundLeft + 25 and p[1] - s[1] < boundFront + 10:
				return False
			#UpperRight
			if p[0] - s[0] < boundLeft + 25 and p[1] + s[1] > boundBack - 10:
				return False
			#LowerLeft
			if p[0] + s[0] > boundRight - 25 and p[1] - s[1] < boundFront + 10:
				return False
			#UpperLeft
			if p[0] + s[0] > boundRight - 25 and p[1] + s[1] > boundBack - 10:
				return False
		return True

	def _findFreePositionFor(self, obj):
		posList = []
		for a in self._objectList:
			p = a.getPosition()
			s = (a.getSize()[0:2] + obj.getSize()[0:2]) / 2 + self._sizeOffsets + self._headSizeOffsets
			posList.append(p + s * ( 1.0, 1.0))
			posList.append(p + s * ( 0.0, 1.0))
			posList.append(p + s * (-1.0, 1.0))
			posList.append(p + s * ( 1.0, 0.0))
			posList.append(p + s * (-1.0, 0.0))
			posList.append(p + s * ( 1.0,-1.0))
			posList.append(p + s * ( 0.0,-1.0))
			posList.append(p + s * (-1.0,-1.0))

		best = None
		bestDist = None
		for p in posList:
			obj.setPosition(p)
			ok = True
			for a in self._objectList:
				if self._checkHit(a, obj):
					ok = False
					break
			if not ok:
				continue
			dist = numpy.linalg.norm(p)
			if not self.checkPlatform(obj):
				dist *= 3
			if best is None or dist < bestDist:
				best = p
				bestDist = dist
		if best is not None:
			obj.setPosition(best)
