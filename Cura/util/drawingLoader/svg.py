__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import math
import re
import sys
import numpy
from xml.etree import ElementTree

from Cura.util.drawingLoader import drawing

def applyTransformString(matrix, transform):
	while transform != '':
		if transform[0] == ',':
			transform = transform[1:].strip()
		s = transform.find('(')
		e = transform.find(')')
		if s < 0 or e < 0:
			print 'Unknown transform: %s' % (transform)
			return matrix
		tag = transform[:s]
		data = map(float, re.split('[ \t,]+', transform[s+1:e].strip()))
		if tag == 'matrix' and len(data) == 6:
			matrix = numpy.matrix([[data[0],data[1],0],[data[2],data[3],0],[data[4],data[5],1]], numpy.float64) * matrix
		elif tag == 'translate' and len(data) == 1:
			matrix = numpy.matrix([[1,0,data[0]],[0,1,0],[0,0,1]], numpy.float64) * matrix
		elif tag == 'translate' and len(data) == 2:
			matrix = numpy.matrix([[1,0,0],[0,1,0],[data[0],data[1],1]], numpy.float64) * matrix
		elif tag == 'scale' and len(data) == 1:
			matrix = numpy.matrix([[data[0],0,0],[0,data[0],0],[0,0,1]], numpy.float64) * matrix
		elif tag == 'scale' and len(data) == 2:
			matrix = numpy.matrix([[data[0],0,0],[0,data[1],0],[0,0,1]], numpy.float64) * matrix
		elif tag == 'rotate' and len(data) == 1:
			r = math.radians(data[0])
			matrix = numpy.matrix([[math.cos(r),math.sin(r),0],[-math.sin(r),math.cos(r),0],[0,0,1]], numpy.float64) * matrix
		elif tag == 'rotate' and len(data) == 3:
			matrix = numpy.matrix([[1,0,0],[0,1,0],[data[1],data[2],1]], numpy.float64) * matrix
			r = math.radians(data[0])
			matrix = numpy.matrix([[math.cos(r),math.sin(r),0],[-math.sin(r),math.cos(r),0],[0,0,1]], numpy.float64) * matrix
			matrix = numpy.matrix([[1,0,0],[0,1,0],[-data[1],-data[2],1]], numpy.float64) * matrix
		elif tag == 'skewX' and len(data) == 1:
			matrix = numpy.matrix([[1,0,0],[math.tan(data[0]),1,0],[0,0,1]], numpy.float64) * matrix
		elif tag == 'skewY' and len(data) == 1:
			matrix = numpy.matrix([[1,math.tan(data[0]),0],[0,1,0],[0,0,1]], numpy.float64) * matrix
		else:
			print 'Unknown transform: %s' % (transform)
			return matrix
		transform = transform[e+1:].strip()
	return matrix

def toFloat(f):
	f = re.search('^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?', f).group(0)
	return float(f)

class SVG(drawing.Drawing):
	def __init__(self, filename):
		super(SVG, self).__init__()
		self.tagProcess = {}
		self.tagProcess['rect'] = self._processRectTag
		self.tagProcess['line'] = self._processLineTag
		self.tagProcess['polyline'] = self._processPolylineTag
		self.tagProcess['polygon'] = self._processPolygonTag
		self.tagProcess['elipse'] = self._processPolygonTag
		self.tagProcess['circle'] = self._processCircleTag
		self.tagProcess['ellipse'] = self._processEllipseTag
		self.tagProcess['path'] = self._processPathTag
		self.tagProcess['use'] = self._processUseTag
		self.tagProcess['g'] = self._processGTag
		self.tagProcess['a'] = self._processGTag
		self.tagProcess['svg'] = self._processGTag
		self.tagProcess['text'] = None #No text implementation yet
		self.tagProcess['image'] = None
		self.tagProcess['metadata'] = None
		self.tagProcess['defs'] = None
		self.tagProcess['style'] = None
		self.tagProcess['marker'] = None
		self.tagProcess['desc'] = None
		self.tagProcess['filter'] = None
		self.tagProcess['linearGradient'] = None
		self.tagProcess['radialGradient'] = None
		self.tagProcess['pattern'] = None
		self.tagProcess['title'] = None
		self.tagProcess['animate'] = None
		self.tagProcess['animateColor'] = None
		self.tagProcess['animateTransform'] = None
		self.tagProcess['set'] = None
		self.tagProcess['script'] = None

		#From Inkscape
		self.tagProcess['namedview'] = None
		#From w3c testsuite
		self.tagProcess['SVGTestCase'] = None

		f = open(filename, "r")
		self._xml = ElementTree.parse(f)
		self._recursiveCount = 0
		matrix = numpy.matrix(numpy.identity(3, numpy.float64))
		matrix = applyTransformString(matrix, "scale(%f)" % (25.4/90.0)) #Per default convert with 90 dpi
		self._processGTag(self._xml.getroot(), matrix)
		self._xml = None
		f.close()

		self._postProcessPaths()

	def _processGTag(self, tag, baseMatrix):
		for e in tag:
			if e.get('transform') is None:
				matrix = baseMatrix
			else:
				matrix = applyTransformString(baseMatrix, e.get('transform'))
			tagName = e.tag[e.tag.find('}')+1:]
			if not tagName in self.tagProcess:
				print 'unknown tag: %s' % (tagName)
			elif self.tagProcess[tagName] is not None:
				self.tagProcess[tagName](e, matrix)

	def _processUseTag(self, tag, baseMatrix):
		if self._recursiveCount > 16:
			return
		self._recursiveCount += 1
		id = tag.get('{http://www.w3.org/1999/xlink}href')
		if id[0] == '#':
			for e in self._xml.findall(".//*[@id='%s']" % (id[1:])):
				if e.get('transform') is None:
					matrix = baseMatrix
				else:
					matrix = applyTransformString(baseMatrix, e.get('transform'))
				tagName = e.tag[e.tag.find('}')+1:]
				if not tagName in self.tagProcess:
					print 'unknown tag: %s' % (tagName)
				elif self.tagProcess[tagName] is not None:
					self.tagProcess[tagName](e, matrix)
		self._recursiveCount -= 1

	def _processLineTag(self, tag, matrix):
		x1 = toFloat(tag.get('x1', '0'))
		y1 = toFloat(tag.get('y1', '0'))
		x2 = toFloat(tag.get('x2', '0'))
		y2 = toFloat(tag.get('y2', '0'))
		p = self.addPath(x1, y1, matrix)
		p.addLineTo(x2, y2)

	def _processPolylineTag(self, tag, matrix):
		values = map(toFloat, re.split('[, \t]+', tag.get('points', '').strip()))
		p = self.addPath(values[0], values[1], matrix)
		for n in xrange(2, len(values)-1, 2):
			p.addLineTo(values[n], values[n+1])

	def _processPolygonTag(self, tag, matrix):
		values = map(toFloat, re.split('[, \t]+', tag.get('points', '').strip()))
		p = self.addPath(values[0], values[1], matrix)
		for n in xrange(2, len(values)-1, 2):
			p.addLineTo(values[n], values[n+1])
		p.closePath()

	def _processCircleTag(self, tag, matrix):
		cx = toFloat(tag.get('cx', '0'))
		cy = toFloat(tag.get('cy', '0'))
		r = toFloat(tag.get('r', '0'))
		p = self.addPath(cx-r, cy, matrix)
		p.addArcTo(cx+r, cy, 0, r, r, False, False)
		p.addArcTo(cx-r, cy, 0, r, r, False, False)

	def _processEllipseTag(self, tag, matrix):
		cx = toFloat(tag.get('cx', '0'))
		cy = toFloat(tag.get('cy', '0'))
		rx = toFloat(tag.get('rx', '0'))
		ry = toFloat(tag.get('rx', '0'))
		p = self.addPath(cx-rx, cy, matrix)
		p.addArcTo(cx+rx, cy, 0, rx, ry, False, False)
		p.addArcTo(cx-rx, cy, 0, rx, ry, False, False)

	def _processRectTag(self, tag, matrix):
		x = toFloat(tag.get('x', '0'))
		y = toFloat(tag.get('y', '0'))
		width = toFloat(tag.get('width', '0'))
		height = toFloat(tag.get('height', '0'))
		if width <= 0 or height <= 0:
			return
		rx = tag.get('rx')
		ry = tag.get('ry')
		if rx is not None or ry is not None:
			if ry is None:
				ry = rx
			if rx is None:
				rx = ry
			rx = float(rx)
			ry = float(ry)
			if rx > width / 2:
				rx = width / 2
			if ry > height / 2:
				ry = height / 2
		else:
			rx = 0.0
			ry = 0.0

		if rx > 0 and ry > 0:
			p = self.addPath(x+width-rx, y, matrix)
			p.addArcTo(x+width,y+ry, 0, rx, ry, False, True)
			p.addLineTo(x+width, y+height-ry)
			p.addArcTo(x+width-rx,y+height, 0, rx, ry, False, True)
			p.addLineTo(x+rx, y+height)
			p.addArcTo(x,y+height-ry, 0, rx, ry, False, True)
			p.addLineTo(x, y+ry)
			p.addArcTo(x+rx,y, 0, rx, ry, False, True)
			p.closePath()
		else:
			p = self.addPath(x, y, matrix)
			p.addLineTo(x,y+height)
			p.addLineTo(x+width,y+height)
			p.addLineTo(x+width,y)
			p.closePath()

	def _processPathTag(self, tag, matrix):
		pathString = tag.get('d', '').replace(',', ' ')
		x = 0
		y = 0
		c2x = 0
		c2y = 0
		path = None
		for command in re.findall('[a-df-zA-DF-Z][^a-df-zA-DF-Z]*', pathString):
			params = re.split(' +', command[1:].strip())
			if len(params) > 0 and params[0] == '':
				params = params[1:]
			if len(params) > 0 and params[-1] == '':
				params = params[:-1]
			params = map(toFloat, params)
			command = command[0]

			if command == 'm':
				x += params[0]
				y += params[1]
				path = self.addPath(x, y, matrix)
				params = params[2:]
				while len(params) > 1:
					x += params[0]
					y += params[1]
					params = params[2:]
					path.addLineTo(x, y)
				c2x, c2y = x, y
			elif command == 'M':
				x = params[0]
				y = params[1]
				path = self.addPath(x, y, matrix)
				params = params[2:]
				while len(params) > 1:
					x = params[0]
					y = params[1]
					params = params[2:]
					path.addLineTo(x, y)
				c2x, c2y = x, y
			elif command == 'l':
				while len(params) > 1:
					x += params[0]
					y += params[1]
					params = params[2:]
					path.addLineTo(x, y)
				c2x, c2y = x, y
			elif command == 'L':
				while len(params) > 1:
					x = params[0]
					y = params[1]
					params = params[2:]
					path.addLineTo(x, y)
				c2x, c2y = x, y
			elif command == 'h':
				x += params[0]
				path.addLineTo(x, y)
				c2x, c2y = x, y
			elif command == 'H':
				x = params[0]
				path.addLineTo(x, y)
				c2x, c2y = x, y
			elif command == 'v':
				y += params[0]
				path.addLineTo(x, y)
				c2x, c2y = x, y
			elif command == 'V':
				y = params[0]
				path.addLineTo(x, y)
				c2x, c2y = x, y
			elif command == 'a':
				while len(params) > 6:
					x += params[5]
					y += params[6]
					path.addArcTo(x, y, params[2], params[0], params[1], params[3] > 0, params[4] > 0)
					params = params[7:]
				c2x, c2y = x, y
			elif command == 'A':
				while len(params) > 6:
					x = params[5]
					y = params[6]
					path.addArcTo(x, y, params[2], params[0], params[1], params[3] > 0, params[4] > 0)
					params = params[7:]
				c2x, c2y = x, y
			elif command == 'c':
				while len(params) > 5:
					c1x = x + params[0]
					c1y = y + params[1]
					c2x = x + params[2]
					c2y = y + params[3]
					x += params[4]
					y += params[5]
					path.addCurveTo(x, y, c1x, c1y, c2x, c2y)
					params = params[6:]
			elif command == 'C':
				while len(params) > 5:
					c1x = params[0]
					c1y = params[1]
					c2x = params[2]
					c2y = params[3]
					x = params[4]
					y = params[5]
					path.addCurveTo(x, y, c1x, c1y, c2x, c2y)
					params = params[6:]
			elif command == 's':
				while len(params) > 3:
					c1x = x - (c2x - x)
					c1y = y - (c2y - y)
					c2x = x + params[0]
					c2y = y + params[1]
					x += params[2]
					y += params[3]
					path.addCurveTo(x, y, c1x, c1y, c2x, c2y)
					params = params[4:]
			elif command == 'S':
				while len(params) > 3:
					c1x = x - (c2x - x)
					c1y = y - (c2y - y)
					c2x = params[0]
					c2y = params[1]
					x = params[2]
					y = params[3]
					path.addCurveTo(x, y, c1x, c1y, c2x, c2y)
					params = params[4:]
			elif command == 'q':
				while len(params) > 3:
					c1x = x + params[0]
					c1y = y + params[1]
					c2x = c1x
					c2y = c1y
					x += params[2]
					y += params[3]
					path.addCurveTo(x, y, c1x, c1y, c2x, c2y)
					params = params[4:]
			elif command == 'Q':
				while len(params) > 3:
					c1x = params[0]
					c1y = params[1]
					c2x = c1x
					c2y = c1y
					x = params[2]
					y = params[3]
					path.addCurveTo(x, y, c1x, c1y, c2x, c2y)
					params = params[4:]
			elif command == 't':
				while len(params) > 1:
					c1x = x - (c2x - x)
					c1y = y - (c2y - y)
					c2x = c1x
					c2y = c1y
					x += params[0]
					y += params[1]
					path.addCurveTo(x, y, c1x, c1y, c2x, c2y)
					params = params[2:]
			elif command == 'T':
				while len(params) > 1:
					c1x = x - (c2x - x)
					c1y = y - (c2y - y)
					c2x = c1x
					c2y = c1y
					x = params[0]
					y = params[1]
					path.addCurveTo(x, y, c1x, c1y, c2x, c2y)
					params = params[2:]
			elif command == 'z' or command == 'Z':
				path.closePath()
				x = path._startPoint.real
				y = path._startPoint.imag
			else:
				print 'Unknown path command:', command, params


if __name__ == '__main__':
	for n in xrange(1, len(sys.argv)):
		print 'File: %s' % (sys.argv[n])
		svg = SVG(sys.argv[n])

	svg.saveAsHtml("test_export.html")
