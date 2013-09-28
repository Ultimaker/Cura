from __future__ import absolute_import
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import math
import re
import sys
import numpy
from xml.etree import ElementTree

def applyTransformString(matrix, transform):
	s = transform.find('(')
	e = transform.find(')')
	if s < 0 or e < 0:
		print 'Unknown transform: %s' % (transform)
		return matrix
	tag = transform[:s]
	data = map(float, re.split('[ \t,]+', transform[s+1:e].strip()))
	if tag == 'matrix' and len(data) == 6:
		return matrix * numpy.matrix([[data[0],data[1],0],[data[2],data[3],0],[data[4],data[5],1]], numpy.float64)
	elif tag == 'translate' and len(data) == 1:
		return matrix * numpy.matrix([[1,0,data[0]],[0,1,0],[0,0,1]], numpy.float64)
	elif tag == 'translate' and len(data) == 2:
		return matrix * numpy.matrix([[1,0,0],[0,1,0],[data[0],data[1],1]], numpy.float64)
	elif tag == 'scale' and len(data) == 1:
		return matrix * numpy.matrix([[data[0],0,0],[0,data[0],0],[0,0,1]], numpy.float64)
	elif tag == 'scale' and len(data) == 2:
		return matrix * numpy.matrix([[data[0],0,0],[0,data[1],0],[0,0,1]], numpy.float64)
	elif tag == 'rotate' and len(data) == 1:
		r = math.radians(data[0])
		return matrix * numpy.matrix([[math.cos(r),math.sin(r),0],[-math.sin(r),math.cos(r),0],[0,0,1]], numpy.float64)
	elif tag == 'skewX' and len(data) == 1:
		return matrix * numpy.matrix([[1,0,0],[math.tan(data[0]),1,0],[0,0,1]], numpy.float64)
	elif tag == 'skewY' and len(data) == 1:
		return matrix * numpy.matrix([[1,math.tan(data[0]),0],[0,1,0],[0,0,1]], numpy.float64)
	print 'Unknown transform: %s' % (transform)
	return matrix

class Path(object):
	LINE = 0
	ARC = 1
	CURVE = 2

	def __init__(self, x, y, matrix):
		self._matrix = matrix
		self._relMatrix = numpy.matrix([[matrix[0,0],matrix[0,1]], [matrix[1,0],matrix[1,1]]])
		self._startPoint = complex(x, y)
		self._points = []

	def addLineTo(self, x, y):
		self._points.append({'type': Path.LINE, 'p': complex(x, y)})

	def addArcTo(self, x, y, rot, rx, ry, large, sweep):
		self._points.append({
			'type': Path.ARC,
			'p': complex(x, y),
			'rot': rot,
			'radius': complex(rx, ry),
			'large': large,
			'sweep': sweep
		})

	def addCurveTo(self, x, y, cp1x, cp1y, cp2x, cp2y):
		self._points.append({
			'type': Path.CURVE,
			'p': complex(x, y),
			'cp1': complex(cp1x, cp1y),
			'cp2': complex(cp2x, cp2y)
		})

	def closePath(self):
		self._points.append({'type': Path.LINE, 'p': self._startPoint})

	def getPoints(self):
		pointList = [self._m(self._startPoint)]
		p1 = self._startPoint
		for p in self._points:
			if p['type'] == Path.LINE:
				p1 = p['p']
				pointList.append(self._m(p1))
			elif p['type'] == Path.ARC:
				p2 = p['p']
				rot = math.radians(p['rot'])
				r = p['radius']

				#http://www.w3.org/TR/SVG/implnote.html#ArcConversionEndpointToCenter
				diff = (p1 - p2) / 2
				p1alt = diff #TODO: apply rot
				p2alt = -diff #TODO: apply rot
				rx2 = r.real*r.real
				ry2 = r.imag*r.imag
				x1alt2 = p1alt.real*p1alt.real
				y1alt2 = p1alt.imag*p1alt.imag

				f = x1alt2 / rx2 + y1alt2 / ry2
				if f >= 1.0:
					r *= math.sqrt(f+0.000001)
					rx2 = r.real*r.real
					ry2 = r.imag*r.imag

				f = math.sqrt((rx2*ry2 - rx2*y1alt2 - ry2*x1alt2) / (rx2*y1alt2+ry2*x1alt2))
				if p['large'] == p['sweep']:
					f = -f
				cAlt = f * complex(r.real*p1alt.imag/r.imag, -r.imag*p1alt.real/r.real)

				c = cAlt + (p1 + p2) / 2 #TODO: apply rot

				a1 = math.atan2((p1alt.imag - cAlt.imag) / r.imag, (p1alt.real - cAlt.real) / r.real)
				a2 = math.atan2((p2alt.imag - cAlt.imag) / r.imag, (p2alt.real - cAlt.real) / r.real)

				#if a1 > a2:
				#	a2 += math.pi * 2
				large = abs(a2 - a1) > math.pi
				if large != p['large']:
					if a1 < a2:
						a1 += math.pi * 2
					else:
						a2 += math.pi * 2

				for n in xrange(0, 16):
					pointList.append(self._m(c + complex(math.cos(a1 + n*(a2-a1)/16) * r.real, math.sin(a1 + n*(a2-a1)/16) * r.imag)))

				pointList.append(self._m(p2))
				p1 = p2
			elif p['type'] == Path.CURVE:
				p1_ = self._m(p1)
				p2 = self._m(p['p'])
				cp1 = self._m(p['cp1'])
				cp2 = self._m(p['cp2'])

				for n in xrange(0, 10):
					f = n / 10.0
					g = 1.0-f
					point = p1_*g*g*g + cp1*3.0*g*g*f + cp2*3.0*g*f*f + p2*f*f*f
					pointList.append(point)

				pointList.append(p2)
				p1 = p['p']

		return pointList

	def getSVGPath(self):
		p0 = self._m(self._startPoint)
		ret = 'M %f %f ' % (p0.real, p0.imag)
		for p in self._points:
			if p['type'] == Path.LINE:
				p0 = self._m(p['p'])
				ret += 'L %f %f' % (p0.real, p0.imag)
			elif p['type'] == Path.ARC:
				p0 = self._m(p['p'])
				radius = p['radius']
				ret += 'A %f %f 0 %d %d %f %f' % (radius.real, radius.imag, p['large'], p['sweep'], p0.real, p0.imag)
			elif p['type'] == Path.CURVE:
				p0 = self._m(p['p'])
				cp1 = self._m(p['cp1'])
				cp2 = self._m(p['cp2'])
				ret += 'C %f %f %f %f %f %f' % (cp1.real, cp1.imag, cp2.real, cp2.imag, p0.real, p0.imag)

		return ret

	def _m(self, p):
		tmp = numpy.matrix([p.real, p.imag, 1], numpy.float64) * self._matrix
		return complex(tmp[0,0], tmp[0,1])
	def _r(self, p):
		tmp = numpy.matrix([p.real, p.imag], numpy.float64) * self._relMatrix
		return complex(tmp[0,0], tmp[0,1])

class SVG(object):
	def __init__(self, filename):
		self.tagProcess = {}
		self.tagProcess['rect'] = self._processRectTag
		self.tagProcess['line'] = self._processLineTag
		self.tagProcess['polyline'] = self._processPolylineTag
		self.tagProcess['polygon'] = self._processPolygonTag
		self.tagProcess['elipse'] = self._processPolygonTag
		self.tagProcess['circle'] = self._processCircleTag
		self.tagProcess['ellipse'] = self._processEllipseTag
		self.tagProcess['path'] = self._processPathTag
		self.tagProcess['g'] = self._processGTag
		self.tagProcess['a'] = self._processGTag
		self.tagProcess['text'] = None #No text implementation yet
		self.tagProcess['image'] = None
		self.tagProcess['metadata'] = None
		self.tagProcess['defs'] = None
		self.tagProcess['title'] = None
		self.tagProcess['animate'] = None
		self.tagProcess['set'] = None
		self.tagProcess['script'] = None

		#From Inkscape
		self.tagProcess['namedview'] = None
		#From w3c testsuite
		self.tagProcess['SVGTestCase'] = None

		self.paths = []
		f = open(filename, "r")
		self._processGTag(ElementTree.parse(f).getroot(), numpy.matrix(numpy.identity(3, numpy.float64)))
		f.close()

	def _processGTag(self, tag, baseMatrix):
		for e in tag:
			if e.get('transform') is None:
				matrix = baseMatrix
			else:
				matrix = applyTransformString(baseMatrix, e.get('transform'))
			tag = e.tag[e.tag.find('}')+1:]
			if not tag in self.tagProcess:
				print 'unknown tag: %s' % (tag)
			elif self.tagProcess[tag] is not None:
				self.tagProcess[tag](e, matrix)

	def _processLineTag(self, tag, matrix):
		x1 = float(tag.get('x1', 0))
		y1 = float(tag.get('y1', 0))
		x2 = float(tag.get('x2', 0))
		y2 = float(tag.get('y2', 0))
		p = Path(x1, y1, matrix)
		p.addLineTo(x2, y2)
		self.paths.append(p)

	def _processPolylineTag(self, tag, matrix):
		values = map(float, re.split('[, \t]+', tag.get('points', '').replace('-', ' -').strip()))
		p = Path(values[0], values[1], matrix)
		for n in xrange(2, len(values)-1, 2):
			p.addLineTo(values[n], values[n+1])
		self.paths.append(p)

	def _processPolygonTag(self, tag, matrix):
		values = map(float, re.split('[, \t]+', tag.get('points', '').replace('-', ' -').strip()))
		p = Path(values[0], values[1], matrix)
		for n in xrange(2, len(values)-1, 2):
			p.addLineTo(values[n], values[n+1])
		p.closePath()
		self.paths.append(p)

	def _processCircleTag(self, tag, matrix):
		cx = float(tag.get('cx', 0))
		cy = float(tag.get('cy', 0))
		r = float(tag.get('r', 0))
		p = Path(cx-r, cy, matrix)
		p.addArcTo(cx+r, cy, 0, r, r, False, False)
		p.addArcTo(cx-r, cy, 0, r, r, False, False)
		self.paths.append(p)

	def _processEllipseTag(self, tag, matrix):
		cx = float(tag.get('cx', 0))
		cy = float(tag.get('cy', 0))
		rx = float(tag.get('rx', 0))
		ry = float(tag.get('rx', 0))
		p = Path(cx-rx, cy, matrix)
		p.addArcTo(cx+rx, cy, 0, rx, ry, False, False)
		p.addArcTo(cx-rx, cy, 0, rx, ry, False, False)
		self.paths.append(p)

	def _processRectTag(self, tag, matrix):
		x = float(tag.get('x', 0))
		y = float(tag.get('y', 0))
		width = float(tag.get('width', 0))
		height = float(tag.get('height', 0))
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
			p = Path(x+rx, y, matrix)
			p.addLineTo(x+width-rx, y)
			p.addArcTo(x+width,y+ry, 0, rx, ry, False, True)
			p.addLineTo(x+width, y+height-ry)
			p.addArcTo(x+width-rx,y+height, 0, rx, ry, False, True)
			p.addLineTo(x+rx, y+height)
			p.addArcTo(x,y+height-ry, 0, rx, ry, False, True)
			p.addLineTo(x, y+ry)
			p.addArcTo(x+rx,y, 0, rx, ry, False, True)
			self.paths.append(p)
		else:
			p = Path(x, y, matrix)
			p.addLineTo(x,y+height)
			p.addLineTo(x+width,y+height)
			p.addLineTo(x+width,y)
			p.closePath()
			self.paths.append(p)

	def _processPathTag(self, tag, matrix):
		pathString = tag.get('d', '').replace(',', ' ').replace('-', ' -')
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
			params = map(float, params)
			command = command[0]

			if command == 'm':
				x += params[0]
				y += params[1]
				path = Path(x, y, matrix)
				self.paths.append(path)
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
				path = Path(x, y, matrix)
				self.paths.append(path)
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

	f = open("test_export.html", "w")

	f.write("<!DOCTYPE html><html><body>\n")
	f.write("<svg xmlns=\"http://www.w3.org/2000/svg\" version=\"1.1\" style='width:%dpx;height:%dpx'>\n" % (1000, 1000))
	f.write("<g fill-rule='evenodd' style=\"fill: gray; stroke:black;stroke-width:2\">\n")
	f.write("<path d=\"")
	for path in svg.paths:
		points = path.getPoints()
		f.write("M %f %f " % (points[0].real, points[0].imag))
		for point in points[1:]:
			f.write("L %f %f " % (point.real, point.imag))
	f.write("\"/>")
	f.write("</g>\n")

	f.write("<g style=\"fill: none; stroke:red;stroke-width:1\">\n")
	f.write("<path d=\"")
	for path in svg.paths:
		f.write(path.getSVGPath())
	f.write("\"/>")
	f.write("</g>\n")

	f.write("</svg>\n")
	f.write("</body></html>")
	f.close()

