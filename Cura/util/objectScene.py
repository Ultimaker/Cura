import random
import numpy

class Scene():
	def __init__(self):
		self._objectList = []
		self._sizeOffsets = numpy.array([3.0,3.0], numpy.float32)
		self._machineSize = numpy.array([100,100,100], numpy.float32)
		self._headOffsets = numpy.array([18.0,18.0], numpy.float32)

	def setMachineSize(self, machineSize):
		self._machineSize = machineSize

	def objects(self):
		return self._objectList

	def add(self, obj):
		self._findFreePositionFor(obj)
		self._objectList.append(obj)
		self.pushFree()

	def remove(self, obj):
		self._objectList.remove(obj)

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
			posList.append(p + s * ( 1, 1))
			posList.append(p + s * ( 0, 1))
			posList.append(p + s * (-1, 1))
			posList.append(p + s * ( 1, 0))
			posList.append(p + s * (-1, 0))
			posList.append(p + s * ( 1,-1))
			posList.append(p + s * ( 0,-1))
			posList.append(p + s * (-1,-1))

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
