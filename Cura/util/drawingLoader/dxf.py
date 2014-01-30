__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import math
import re
import sys
import numpy
from xml.etree import ElementTree

from Cura.util.drawingLoader import drawing

class DXF(drawing.Drawing):
	def __init__(self, filename):
		super(DXF, self).__init__()
		self._lastLine = None
		self._polyLine = None

		entityType = 'NONE'
		sectionName = 'NONE'
		activeObject = None
		f = open(filename, "r")
		while True:
			groupCode = f.readline().strip()
			if groupCode == '':
				break
			groupCode = int(groupCode)
			value = f.readline().strip()
			if groupCode == 0:
				if entityType == 'SECTION':
					sectionName = activeObject[2][0]
				elif entityType == 'ENDSEC':
					sectionName = 'NONE'
				elif sectionName == 'ENTITIES':
					self._checkForNewPath(entityType, activeObject)
				elif activeObject is not None:
					pass
					#print sectionName, entityType, activeObject
				entityType = value
				activeObject = {}
			else:
				if groupCode in activeObject:
					activeObject[groupCode].append(value)
				else:
					activeObject[groupCode] = [value]
		if sectionName == 'ENTITIES':
			self._checkForNewPath(entityType, activeObject)
		f.close()

		self._postProcessPaths()

	def _checkForNewPath(self, type, obj):
		if type == 'LINE':
			if self._lastLine is not None and self._lastLinePoint == complex(float(obj[10][0]), float(obj[20][0])):
				self._lastLine.addLineTo(float(obj[11][0]), float(obj[21][0]))
			else:
				p = self.addPath(float(obj[10][0]), float(obj[20][0]))
				p.addLineTo(float(obj[11][0]), float(obj[21][0]))
				self._lastLine = p
			self._lastLinePoint = complex(float(obj[11][0]), float(obj[21][0]))
		elif type == 'POLYLINE':
			self._polyLine = None
		elif type == 'VERTEX':
			if self._polyLine is None:
				self._polyLine = self.addPath(float(obj[10][0]), float(obj[20][0]))
			else:
				self._polyLine.addLineTo(float(obj[10][0]), float(obj[20][0]))
		elif type == 'LWPOLYLINE':
			p = self.addPath(float(obj[10][0]), float(obj[20][0]))
			for n in xrange(1, len(obj[10])):
				p.addLineTo(float(obj[10][n]), float(obj[20][n]))
			self._lastLine = p
		elif type == 'SPLINE':
			p = self.addPath(float(obj[10][0]), float(obj[20][0]))
			for n in xrange(1, len(obj[10])):
				p.addLineTo(float(obj[10][n]), float(obj[20][n]))
			self._lastLine = p
		else:
			print 'type=%s' % type
			for k in obj.keys():
				print k, obj[k]

if __name__ == '__main__':
	for n in xrange(1, len(sys.argv)):
		print 'File: %s' % (sys.argv[n])
		dxf = DXF(sys.argv[n])

	dxf.saveAsHtml("test_export.html")

