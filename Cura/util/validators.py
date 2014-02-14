"""
Setting validators.
These are the validators for various profile settings, each validator can be attached to a setting.
The validators can be queried to see if the setting is valid.
There are 3 possible outcomes:
	Valid	- No problems found
	Warning - The value is valid, but not recommended
	Error	- The value is not a proper number, out of range, or some other way wrong.
"""
from __future__ import division
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import types
import math

SUCCESS = 0
WARNING = 1
ERROR   = 2

class validFloat(object):
	"""
	Checks if the given value in the setting is a valid float. An invalid float is an error condition.
	And supports a minimum and/or maximum value. The min/max values are error conditions.
	If the value == min or max then this is also an error.
	"""
	def __init__(self, setting, minValue = None, maxValue = None):
		self.setting = setting
		self.setting._validators.append(self)
		self.minValue = minValue
		self.maxValue = maxValue
	
	def validate(self):
		try:
			f = float(eval(self.setting.getValue().replace(',','.'), {}, {}))
			if self.minValue is not None and f < self.minValue:
				return ERROR, 'This setting should not be below ' + str(round(self.minValue, 3))
			if self.maxValue is not None and f > self.maxValue:
				return ERROR, 'This setting should not be above ' + str(self.maxValue)
			return SUCCESS, ''
		except (ValueError, SyntaxError, TypeError, NameError):
			return ERROR, '"' + str(self.setting.getValue()) + '" is not a valid number or expression'

class validInt(object):
	"""
	Checks if the given value in the setting is a valid integer. An invalid integer is an error condition.
	And supports a minimum and/or maximum value. The min/max values are error conditions.
	If the value == min or max then this is also an error.
	"""
	def __init__(self, setting, minValue = None, maxValue = None):
		self.setting = setting
		self.setting._validators.append(self)
		self.minValue = minValue
		self.maxValue = maxValue
	
	def validate(self):
		try:
			f = int(eval(self.setting.getValue(), {}, {}))
			if self.minValue is not None and f < self.minValue:
				return ERROR, 'This setting should not be below ' + str(self.minValue)
			if self.maxValue is not None and f > self.maxValue:
				return ERROR, 'This setting should not be above ' + str(self.maxValue)
			return SUCCESS, ''
		except (ValueError, SyntaxError, TypeError, NameError):
			return ERROR, '"' + str(self.setting.getValue()) + '" is not a valid whole number or expression'

class warningAbove(object):
	"""
	A validator to give off a warning if a value is equal or above a certain value.
	"""
	def __init__(self, setting, minValueForWarning, warningMessage):
		self.setting = setting
		self.setting._validators.append(self)
		self.minValueForWarning = minValueForWarning
		self.warningMessage = warningMessage
	
	def validate(self):
		try:
			f = float(eval(self.setting.getValue().replace(',','.'), {}, {}))
			if isinstance(self.minValueForWarning, types.FunctionType):
				if f >= self.minValueForWarning():
					return WARNING, self.warningMessage % (self.minValueForWarning())
			else:
				if f >= self.minValueForWarning:
					return WARNING, self.warningMessage
			return SUCCESS, ''
		except (ValueError, SyntaxError, TypeError):
			#We already have an error by the int/float validator in this case.
			return SUCCESS, ''

class warningBelow(object):
	"""
	A validator to give off a warning if a value is equal or below a certain value.
	"""
	def __init__(self, setting, minValueForWarning, warningMessage):
		self.setting = setting
		self.setting._validators.append(self)
		self.minValueForWarning = minValueForWarning
		self.warningMessage = warningMessage

	def validate(self):
		try:
			f = float(eval(self.setting.getValue().replace(',','.'), {}, {}))
			if isinstance(self.minValueForWarning, types.FunctionType):
				if f <= self.minValueForWarning():
					return WARNING, self.warningMessage % (self.minValueForWarning())
			else:
				if f <= self.minValueForWarning:
					return WARNING, self.warningMessage
			return SUCCESS, ''
		except (ValueError, SyntaxError, TypeError):
			#We already have an error by the int/float validator in this case.
			return SUCCESS, ''

class wallThicknessValidator(object):
	"""
	Special wall-thickness validator. The wall thickness is used to calculate the amount of shells and the thickness of the shells.
	But, on certain conditions the resulting wall-thickness is not really suitable for printing. The range in which this can happen is small.
	But better warn for it.
	"""
	def __init__(self, setting):
		self.setting = setting
		self.setting._validators.append(self)
	
	def validate(self):
		from Cura.util import profile
		try:
			wallThickness = profile.getProfileSettingFloat('wall_thickness')
			nozzleSize = profile.getProfileSettingFloat('nozzle_size')
			if wallThickness < 0.01:
				return SUCCESS, ''
			if wallThickness <= nozzleSize * 0.5:
				return ERROR, 'Trying to print walls thinner then the half of your nozzle size, this will not produce anything usable'
			if wallThickness <= nozzleSize * 0.85:
				return WARNING, 'Trying to print walls thinner then the 0.8 * nozzle size. Small chance that this will produce usable results'
			if wallThickness < nozzleSize:
				return SUCCESS, ''
			if nozzleSize <= 0:
				return ERROR, 'Incorrect nozzle size'
			
			lineCount = int(wallThickness / nozzleSize)
			lineWidth = wallThickness / lineCount
			lineWidthAlt = wallThickness / (lineCount + 1)
			if lineWidth >= nozzleSize * 1.5 and lineWidthAlt <= nozzleSize * 0.85:
				return WARNING, 'Current selected wall thickness results in a line thickness of ' + str(lineWidthAlt) + 'mm which is not recommended with your nozzle of ' + str(nozzleSize) + 'mm'
			return SUCCESS, ''
		except ValueError:
			#We already have an error by the int/float validator in this case.
			return SUCCESS, ''

class printSpeedValidator(object):
	"""
	Validate the printing speed by checking for a certain amount of volume per second.
	This is based on the fact that you can push 10mm3 per second trough an UM-Origonal nozzle.
	TODO: Update this code so it works better for different machine times with other feeders.
	"""
	def __init__(self, setting):
		self.setting = setting
		self.setting._validators.append(self)

	def validate(self):
		from Cura.util import profile
		try:
			nozzleSize = profile.getProfileSettingFloat('nozzle_size')
			layerHeight = profile.getProfileSettingFloat('layer_height')
			printSpeed = profile.getProfileSettingFloat('print_speed')
			
			printVolumePerMM = layerHeight * nozzleSize
			printVolumePerSecond = printVolumePerMM * printSpeed
			#Using 10mm3 per second with a 0.4mm nozzle (normal max according to Joergen Geerds)
			maxPrintVolumePerSecond = 10 / (math.pi*(0.2*0.2)) * (math.pi*(nozzleSize/2*nozzleSize/2))
			
			if printVolumePerSecond > maxPrintVolumePerSecond:
				return WARNING, 'You are trying to print more then %.1fmm^3 of filament per second. This might cause filament slipping. (You are printing at %0.1fmm^3 per second)' % (maxPrintVolumePerSecond, printVolumePerSecond)
			
			return SUCCESS, ''
		except ValueError:
			#We already have an error by the int/float validator in this case.
			return SUCCESS, ''
