import random
import numpy

class Scene():
	def __init__(self):
		self._objectList = []

	def objects(self):
		return self._objectList

	def add(self, obj):
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
				distance = (a.getSize()[axis] + b.getSize()[axis]) / 2 + 0.1
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
		if abs(posDiff[0]) < (a.getSize()[0] + b.getSize()[0]) / 2 and abs(posDiff[1]) < (a.getSize()[1] + b.getSize()[1]) / 2:
			return True
		return False
