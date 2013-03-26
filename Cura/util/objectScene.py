import random
import numpy

class Scene():
	def __init__(self):
		self._objectList = []
		self._sizeOffsets = numpy.array([3.0,3.0], numpy.float32)
		self._machineSize = numpy.array([100,100,100], numpy.float32)

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
		while self._pushFree():
			pass

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
				distance = (a.getSize()[axis] + b.getSize()[axis]) / 2 + 0.1 + self._sizeOffsets[axis] * 2
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
		if abs(posDiff[0]) < (a.getSize()[0] + b.getSize()[0]) / 2 + self._sizeOffsets[0] * 2 and abs(posDiff[1]) < (a.getSize()[1] + b.getSize()[1]) / 2 + self._sizeOffsets[1] * 2:
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
			s = (a.getSize()[0:2] + obj.getSize()[0:2]) / 2 + self._sizeOffsets * 2
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
