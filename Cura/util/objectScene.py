"""
The objectScene module contain a objectScene class,
this class contains a group of printableObjects that are located on the build platform.

The objectScene handles the printing order of these objects, and if they collide.
"""
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"
import random
import numpy

from Cura.util import profile
from Cura.util import polygon

class _objectOrder(object):
	"""
	Internal object used by the _objectOrderFinder to keep track of a possible order in which to print objects.
	"""
	def __init__(self, order, todo):
		"""
		:param order:	List of indexes in which to print objects, ordered by printing order.
		:param todo: 	List of indexes which are not yet inserted into the order list.
		"""
		self.order = order
		self.todo = todo

class _objectOrderFinder(object):
	"""
	Internal object used by the Scene class to figure out in which order to print objects.
	"""
	def __init__(self, scene, leftToRight, frontToBack, gantryHeight):
		self._scene = scene
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
			for b in initialList:
				if a != b and self._hitMap[a][b] and self._hitMap[b][a]:
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
		return polygon.polygonCollision(obj._boundaryHull + obj.getPosition(), addObj._headAreaHull + addObj.getPosition())

class Scene(object):
	"""
	The scene class keep track of an collection of objects on a build platform and their state.
	It can figure out in which order to print them (if any) and if an object can be printed at all.
	"""
	def __init__(self):
		self._objectList = []
		self._sizeOffsets = numpy.array([0.0,0.0], numpy.float32)
		self._machineSize = numpy.array([100,100,100], numpy.float32)
		self._headSizeOffsets = numpy.array([18.0,18.0], numpy.float32)
		self._minExtruderCount = None
		self._extruderOffset = [numpy.array([0,0], numpy.float32)] * 4

		#Print order variables
		self._leftToRight = False
		self._frontToBack = True
		self._gantryHeight = 60
		self._oneAtATime = True

	# update the physical machine dimensions
	def updateMachineDimensions(self):
		self._machineSize = numpy.array([profile.getMachineSettingFloat('machine_width'), profile.getMachineSettingFloat('machine_depth'), profile.getMachineSettingFloat('machine_height')])
		self._machinePolygons = profile.getMachineSizePolygons()
		self.updateHeadSize()

	# Size offsets are offsets caused by brim, skirt, etc.
	def updateSizeOffsets(self, force=False):
		newOffsets = numpy.array(profile.calculateObjectSizeOffsets(), numpy.float32)
		minExtruderCount = profile.minimalExtruderCount()
		if not force and numpy.array_equal(self._sizeOffsets, newOffsets) and self._minExtruderCount == minExtruderCount:
			return
		self._sizeOffsets = newOffsets
		self._minExtruderCount = minExtruderCount

		extends = [numpy.array([[-newOffsets[0],-newOffsets[1]],[ newOffsets[0],-newOffsets[1]],[ newOffsets[0], newOffsets[1]],[-newOffsets[0], newOffsets[1]]], numpy.float32)]
		for n in xrange(1, 4):
			headOffset = numpy.array([[0, 0], [-profile.getMachineSettingFloat('extruder_offset_x%d' % (n)), -profile.getMachineSettingFloat('extruder_offset_y%d' % (n))]], numpy.float32)
			extends.append(polygon.minkowskiHull(extends[n-1], headOffset))
		if minExtruderCount > 1:
			extends[0] = extends[1]

		for obj in self._objectList:
			obj.setPrintAreaExtends(extends[len(obj._meshList) - 1])

	#size of the printing head.
	def updateHeadSize(self, obj = None):
		xMin = profile.getMachineSettingFloat('extruder_head_size_min_x')
		xMax = profile.getMachineSettingFloat('extruder_head_size_max_x')
		yMin = profile.getMachineSettingFloat('extruder_head_size_min_y')
		yMax = profile.getMachineSettingFloat('extruder_head_size_max_y')
		gantryHeight = profile.getMachineSettingFloat('extruder_head_size_height')

		self._leftToRight = xMin < xMax
		self._frontToBack = yMin < yMax
		self._headSizeOffsets[0] = min(xMin, xMax)
		self._headSizeOffsets[1] = min(yMin, yMax)
		self._gantryHeight = gantryHeight
		self._oneAtATime = self._gantryHeight > 0 and profile.getPreference('oneAtATime') == 'True'
		for obj in self._objectList:
			if obj.getSize()[2] > self._gantryHeight:
				self._oneAtATime = False

		headArea = numpy.array([[-xMin,-yMin],[ xMax,-yMin],[ xMax, yMax],[-xMin, yMax]], numpy.float32)

		if obj is None:
			for obj in self._objectList:
				obj.setHeadArea(headArea, self._headSizeOffsets)
		else:
			obj.setHeadArea(headArea, self._headSizeOffsets)

	def isOneAtATime(self):
		return self._oneAtATime

	def setExtruderOffset(self, extruderNr, offsetX, offsetY):
		self._extruderOffset[extruderNr] = numpy.array([offsetX, offsetY], numpy.float32)

	def objects(self):
		return self._objectList

	#Add new object to print area
	def add(self, obj):
		if numpy.max(obj.getSize()[0:2]) > numpy.max(self._machineSize[0:2]) * 2.5:
			scale = numpy.max(self._machineSize[0:2]) * 2.5 / numpy.max(obj.getSize()[0:2])
			matrix = [[scale,0,0], [0, scale, 0], [0, 0, scale]]
			obj.applyMatrix(numpy.matrix(matrix, numpy.float64))
		self._findFreePositionFor(obj)
		self._objectList.append(obj)
		self.updateHeadSize(obj)
		self.updateSizeOffsets(True)
		self.pushFree(obj)

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
		self.pushFree(obj1)

	def pushFree(self, staticObj = None):
		if staticObj is None:
			for obj in self._objectList:
				self.pushFree(obj)
			return
		if not self.checkPlatform(staticObj):
			return
		pushList = []
		for obj in self._objectList:
			if obj == staticObj or not self.checkPlatform(obj):
				continue
			if self._oneAtATime:
				v = polygon.polygonCollisionPushVector(obj._headAreaMinHull + obj.getPosition(), staticObj._boundaryHull + staticObj.getPosition())
			else:
				v = polygon.polygonCollisionPushVector(obj._boundaryHull + obj.getPosition(), staticObj._boundaryHull + staticObj.getPosition())
			if type(v) is bool:
				continue
			obj.setPosition(obj.getPosition() + v * 1.01)
			pushList.append(obj)
		for obj in pushList:
			self.pushFree(obj)

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
			order = _objectOrderFinder(self, self._leftToRight, self._frontToBack, self._gantryHeight).order
		else:
			order = None
		return order

	#Check if two objects are hitting each-other (+ head space).
	def _checkHit(self, a, b):
		if a == b:
			return False
		if self._oneAtATime:
			return polygon.polygonCollision(a._headAreaMinHull + a.getPosition(), b._boundaryHull + b.getPosition())
		else:
			return polygon.polygonCollision(a._boundaryHull + a.getPosition(), b._boundaryHull + b.getPosition())

	def checkPlatform(self, obj):
		area = obj._printAreaHull + obj.getPosition()
		if obj.getSize()[2] > self._machineSize[2]:
			return False
		if not polygon.fullInside(area, self._machinePolygons[0]):
			return False
		#Check the "no go zones"
		for poly in self._machinePolygons[1:]:
			if polygon.polygonCollision(poly, area):
				return False
		return True

	def _findFreePositionFor(self, obj):
		posList = []
		for a in self._objectList:
			p = a.getPosition()
			if self._oneAtATime:
				s = (a.getSize()[0:2] + obj.getSize()[0:2]) / 2 + self._sizeOffsets + self._headSizeOffsets + numpy.array([4,4], numpy.float32)
			else:
				s = (a.getSize()[0:2] + obj.getSize()[0:2]) / 2 + numpy.array([4,4], numpy.float32)
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
