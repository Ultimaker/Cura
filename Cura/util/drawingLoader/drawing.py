from __future__ import absolute_import
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import math
import numpy

class Drawing(object):
	def __init__(self):
		self.paths = []

	def addPath(self, x, y, matrix=numpy.matrix(numpy.identity(3, numpy.float64))):
		p = Path(x, y, matrix)
		self.paths.append(p)
		return p

	def _postProcessPaths(self):
		for path in self.paths:
			if not path.isClosed():
				if abs(self._nodes[-1]['p'] - self._startPoint) < 0.001:
					self._isClosed = True

	def saveAsHtml(self, filename):
		f = open(filename, "w")

		posMax = complex(-1000, -1000)
		posMin = complex( 1000,  1000)
		for path in self.paths:
			points = path.getPoints()
			for p in points:
				if p.real > posMax.real:
					posMax = complex(p.real, posMax.imag)
				if p.imag > posMax.imag:
					posMax = complex(posMax.real, p.imag)
				if p.real < posMin.real:
					posMin = complex(p.real, posMin.imag)
				if p.imag < posMin.imag:
					posMin = complex(posMin.real, p.imag)

		f.write("<!DOCTYPE html><html><body>\n")
		f.write("<svg xmlns=\"http://www.w3.org/2000/svg\" version=\"1.1\" style='width:%dpx;height:%dpx'>\n" % ((posMax - posMin).real, (posMax - posMin).imag))
		f.write("<g fill-rule='evenodd' style=\"fill: gray; stroke:black;stroke-width:2\">\n")
		f.write("<path d=\"")
		for path in self.paths:
			points = path.getPoints()
			f.write("M %f %f " % (points[0].real - posMin.real, points[0].imag - posMin.imag))
			for point in points[1:]:
				f.write("L %f %f " % (point.real - posMin.real, point.imag - posMin.imag))
		f.write("\"/>")
		f.write("</g>\n")

		f.write("<g style=\"fill: none; stroke:red;stroke-width:1\">\n")
		f.write("<path d=\"")
		for path in self.paths:
			f.write(path.getSVGPath())
		f.write("\"/>")
		f.write("</g>\n")

		f.write("</svg>\n")
		f.write("</body></html>")
		f.close()

class Path(object):
	LINE = 0
	ARC = 1
	CURVE = 2

	def __init__(self, x, y, matrix=numpy.matrix(numpy.identity(3, numpy.float64))):
		self._matrix = matrix
		self._relMatrix = numpy.matrix([[matrix[0,0],matrix[1,0]],[matrix[0,1],matrix[1,1]]], numpy.float64)
		self._startPoint = self._m(complex(x, y))
		self._nodes = []
		self._isClosed = False

	def addLineTo(self, x, y):
		self._nodes.append({'type': Path.LINE, 'p': self._m(complex(x, y))})

	def addArcTo(self, x, y, rot, rx, ry, large, sweep):
		self._nodes.append({
			'type': Path.ARC,
			'p': self._m(complex(x, y)),
			'rot': rot,
			'radius': self._r(complex(rx, ry)),
			'large': large,
			'sweep': sweep
		})

	def addCurveTo(self, x, y, cp1x, cp1y, cp2x, cp2y):
		self._nodes.append({
			'type': Path.CURVE,
			'p': self._m(complex(x, y)),
			'cp1': self._m(complex(cp1x, cp1y)),
			'cp2': self._m(complex(cp2x, cp2y))
		})

	def isClosed(self):
		return self._isClosed

	def closePath(self):
		self._nodes.append({'type': Path.LINE, 'p': self._startPoint})
		self._isClosed = True

	def getPoints(self, accuracy = 1):
		pointList = [self._startPoint]
		p1 = self._startPoint
		for p in self._nodes:
			if p['type'] == Path.LINE:
				p1 = p['p']
				pointList.append(p1)
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

				large = abs(a2 - a1) > math.pi
				if large != p['large']:
					if a1 < a2:
						a1 += math.pi * 2
					else:
						a2 += math.pi * 2

				pCenter = c + complex(math.cos(a1 + 0.5*(a2-a1)) * r.real, math.sin(a1 + 0.5*(a2-a1)) * r.imag)
				dist = abs(pCenter - p1) + abs(pCenter - p2)
				segments = int(dist / accuracy) + 1
				for n in xrange(1, segments):
					pointList.append(c + complex(math.cos(a1 + n*(a2-a1)/segments) * r.real, math.sin(a1 + n*(a2-a1)/segments) * r.imag))

				pointList.append(p2)
				p1 = p2
			elif p['type'] == Path.CURVE:
				p2 = p['p']
				cp1 = p['cp1']
				cp2 = p['cp2']

				pCenter = p1*0.5*0.5*0.5 + cp1*3.0*0.5*0.5*0.5 + cp2*3.0*0.5*0.5*0.5 + p2*0.5*0.5*0.5
				dist = abs(pCenter - p1) + abs(pCenter - p2)
				segments = int(dist / accuracy) + 1
				for n in xrange(1, segments):
					f = n / float(segments)
					g = 1.0-f
					point = p1*g*g*g + cp1*3.0*g*g*f + cp2*3.0*g*f*f + p2*f*f*f
					pointList.append(point)

				pointList.append(p2)
				p1 = p['p']

		return pointList

	#getSVGPath returns an SVG path string. Ths path string is not perfect when matrix transformations are involved.
	def getSVGPath(self):
		p0 = self._startPoint
		ret = 'M %f %f ' % (p0.real, p0.imag)
		for p in self._nodes:
			if p['type'] == Path.LINE:
				p0 = p['p']
				ret += 'L %f %f' % (p0.real, p0.imag)
			elif p['type'] == Path.ARC:
				p0 = p['p']
				radius = p['radius']
				ret += 'A %f %f 0 %d %d %f %f' % (radius.real, radius.imag, 1 if p['large'] else 0, 1 if p['sweep'] else 0, p0.real, p0.imag)
			elif p['type'] == Path.CURVE:
				p0 = p['p']
				cp1 = p['cp1']
				cp2 = p['cp2']
				ret += 'C %f %f %f %f %f %f' % (cp1.real, cp1.imag, cp2.real, cp2.imag, p0.real, p0.imag)

		return ret

	def _m(self, p):
		tmp = numpy.matrix([p.real, p.imag, 1], numpy.float64) * self._matrix
		return complex(tmp[0,0], tmp[0,1])

	def _r(self, p):
		tmp = numpy.matrix([p.real, p.imag], numpy.float64) * self._relMatrix
		return complex(tmp[0,0], tmp[0,1])
