from __future__ import absolute_import

import math

from Cura.util import profile

class gcodeGenerator(object):
	def __init__(self):
		self._feedPrint = profile.getProfileSettingFloat('print_speed') * 60
		self._feedTravel = profile.getProfileSettingFloat('travel_speed') * 60
		self._feedRetract = profile.getProfileSettingFloat('retraction_speed') * 60
		filamentRadius = profile.getProfileSettingFloat('filament_diameter') / 2
		filamentArea = math.pi * filamentRadius * filamentRadius
		self._ePerMM = (profile.getProfileSettingFloat('nozzle_size') * 0.1) / filamentArea
		self._eValue = 0.0
		self._x = 0
		self._y = 0
		self._z = 0

		self._list = ['G92 E0']

	def setExtrusionRate(self, lineWidth, layerHeight):
		filamentRadius = profile.getProfileSettingFloat('filament_diameter') / 2
		filamentArea = math.pi * filamentRadius * filamentRadius
		self._ePerMM = (lineWidth * layerHeight) / filamentArea

	def home(self):
		self._x = 0
		self._y = 0
		self._z = 0
		self._list += ['G28']

	def addMove(self, x=None, y=None, z=None):
		cmd = "G0 "
		if x is not None:
			cmd += "X%f " % (x)
			self._x = x
		if y is not None:
			cmd += "Y%f " % (y)
			self._y = y
		if z is not None:
			cmd += "Z%f " % (z)
			self._z = z
		cmd += "F%d" % (self._feedTravel)
		self._list += [cmd]

	def addPrime(self, amount=5):
		self._eValue += amount
		self._list += ['G1 E%f F%f' % (self._eValue, self._feedRetract)]

	def addRetract(self, amount=5):
		self._eValue -= amount
		self._list += ['G1 E%f F%f' % (self._eValue, self._feedRetract)]

	def addExtrude(self, x=None, y=None, z=None):
		cmd = "G1 "
		oldX = self._x
		oldY = self._y
		if x is not None:
			cmd += "X%f " % (x)
			self._x = x
		if y is not None:
			cmd += "Y%f " % (y)
			self._y = y
		if z is not None:
			cmd += "Z%f " % (z)
			self._z = z
		self._eValue += math.sqrt((self._x - oldX) * (self._x - oldX) + (self._y - oldY) * (self._y - oldY)) * self._ePerMM
		cmd += "E%f F%d" % (self._eValue, self._feedPrint)
		self._list += [cmd]

	def addCmd(self, cmd):
		self._list += [cmd]

	def list(self):
		return self._list