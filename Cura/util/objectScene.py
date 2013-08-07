__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"
import random
import numpy

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

	def _checkHit(self, addIdx, idx):
		addPos = self._scene._objectList[addIdx].getPosition()
		addSize = self._scene._objectList[addIdx].getSize()
		pos = self._scene._objectList[idx].getPosition()
		size = self._scene._objectList[idx].getSize()

		if self._leftToRight:
			if addPos[0] - addSize[0] / 2 - self._offset[0] <= pos[0] + size[0] / 2:
				return False
		else:
			if addPos[0] + addSize[0] / 2 + self._offset[0] <= pos[0] - size[0] / 2:
				return False

		if self._frontToBack:
			if addPos[1] - addSize[1] / 2 - self._offset[1] >= pos[1] + size[1] / 2:
				return False
		else:
			if addPos[1] + addSize[1] / 2 + self._offset[1] >= pos[1] - size[1] / 2:
				return False

		return True

class Scene(object):
	def __init__(self):
		self._objectList = []
		self._sizeOffsets = numpy.array([0.0,0.0], numpy.float32)
		self._machineSize = numpy.array([100,100,100], numpy.float32)
		self._headOffsets = numpy.array([18.0,18.0], numpy.float32)
		self._leftToRight = False
		self._frontToBack = True
		self._gantryHeight = 60

	def setMachineSize(self, machineSize):
		self._machineSize = machineSize

	def setSizeOffsets(self, sizeOffsets):
		self._sizeOffsets = sizeOffsets

	def setHeadSize(self, xMin, xMax, yMin, yMax, gantryHeight):
		self._leftToRight = xMin < xMax
		self._frontToBack = yMin < yMax
		self._headOffsets[0] = min(xMin, xMax)
		self._headOffsets[1] = min(yMin, yMax)
		self._gantryHeight = gantryHeight

	def getObjectExtend(self):
		return self._sizeOffsets + self._headOffsets

	def objects(self):
		return self._objectList

	def add(self, obj):
		self._findFreePositionFor(obj)
		self._objectList.append(obj)
		self.pushFree()
		if numpy.max(obj.getSize()[0:2]) > numpy.max(self._machineSize[0:2]) * 2.5:
			scale = numpy.max(self._machineSize[0:2]) * 2.5 / numpy.max(obj.getSize()[0:2])
			matrix = [[scale,0,0], [0, scale, 0], [0, 0, scale]]
			obj.applyMatrix(numpy.matrix(matrix, numpy.float64))

	def remove(self, obj):
		self._objectList.remove(obj)

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
		order = _objectOrderFinder(self, self._headOffsets + self._sizeOffsets, self._leftToRight, self._frontToBack, self._gantryHeight).order
		return order

	def _pushFree(self):
		for a in self._objectList:
			for b in self._objectList:
				if not self._checkHit(a, b):
					continue
				posDiff = a.getPosition() - b.getPosition()
				if posDiff[0] == 0.0 and posDiff[1] == 0.0:
					posDiff[1] = 1.0
				if abs(posDiff[0]) > abs(posDiff[1]):
					axis = 0
				else:
					axis = 1
				aPos = a.getPosition()
				bPos = b.getPosition()
				center = (aPos[axis] + bPos[axis]) / 2
				distance = (a.getSize()[axis] + b.getSize()[axis]) / 2 + 0.1 + self._sizeOffsets[axis] + self._headOffsets[axis]
				if posDiff[axis] < 0:
					distance = -distance
				aPos[axis] = center + distance / 2
				bPos[axis] = center - distance / 2
				a.setPosition(aPos)
				b.setPosition(bPos)
				return True
		return False

	def _checkHit(self, a, b):
		if a == b:
			return False
		posDiff = a.getPosition() - b.getPosition()
		if abs(posDiff[0]) < (a.getSize()[0] + b.getSize()[0]) / 2 + self._sizeOffsets[0] + self._headOffsets[0]:
			if abs(posDiff[1]) < (a.getSize()[1] + b.getSize()[1]) / 2 + self._sizeOffsets[1] + self._headOffsets[1]:
				return True
		return False

	def checkPlatform(self, obj):
		p = obj.getPosition()
		s = obj.getSize()[0:2] / 2 + self._sizeOffsets
		if p[0] - s[0] < -self._machineSize[0] / 2:
			return False
		if p[0] + s[0] > self._machineSize[0] / 2:
			return False
		if p[1] - s[1] < -self._machineSize[1] / 2:
			return False
		if p[1] + s[1] > self._machineSize[1] / 2:
			return False
		return True

	def _findFreePositionFor(self, obj):
		posList = []
		for a in self._objectList:
			p = a.getPosition()
			s = (a.getSize()[0:2] + obj.getSize()[0:2]) / 2 + self._sizeOffsets + self._headOffsets
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
