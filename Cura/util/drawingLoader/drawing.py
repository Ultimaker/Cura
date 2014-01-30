__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import math
import numpy

class Node(object):
	LINE = 0
	ARC = 1
	CURVE = 2

	def __init__(self, type, position):
		self.type = type
		self.position = position

class LineNode(Node):
	def __init__(self, position):
		super(LineNode, self).__init__(Node.LINE, position)

class ArcNode(Node):
	def __init__(self, position, rotation, radius, large, sweep):
		super(ArcNode, self).__init__(Node.ARC, position)
		self.rotation = rotation
		self.radius = radius
		self.large = large
		self.sweep = sweep

class Path(object):
	def __init__(self, x, y, matrix=numpy.matrix(numpy.identity(3, numpy.float64))):
		self._matrix = matrix
		self._relMatrix = numpy.matrix([[matrix[0,0],matrix[1,0]],[matrix[0,1],matrix[1,1]]], numpy.float64)
		self._startPoint = self._m(complex(x, y))
		self._nodes = []
		self._isClosed = False

	def addLineTo(self, x, y):
		self._nodes.append(LineNode(self._m(complex(x, y))))

	def addArcTo(self, x, y, rotation, rx, ry, large, sweep):
		self._nodes.append(ArcNode(self._m(complex(x, y)), rotation, self._r(complex(rx, ry)), large, sweep))

	def addCurveTo(self, x, y, cp1x, cp1y, cp2x, cp2y):
		node = Node(Node.CURVE, self._m(complex(x, y)))
		node.cp1 = self._m(complex(cp1x, cp1y))
		node.cp2 = self._m(complex(cp2x, cp2y))
		self._nodes.append(node)

	def isClosed(self):
		return self._isClosed

	def closePath(self):
		if abs(self._nodes[-1].position - self._startPoint) > 0.01:
			self._nodes.append(Node(Node.LINE, self._startPoint))
		self._isClosed = True

	def getArcInfo(self, node):
		p1 = self._startPoint
		if self._nodes[0] != node:
			p1 = self._nodes[self._nodes.index(node) - 1].position

		p2 = node.position
		if abs(p1 - p2) < 0.0001:
			return p1, 0.0, math.pi, complex(0.0, 0.0)
		rot = math.radians(node.rotation)
		r = node.radius

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

		if rx2*y1alt2+ry2*x1alt2 == 0.0:
			f = 0
		else:
			f = math.sqrt((rx2*ry2 - rx2*y1alt2 - ry2*x1alt2) / (rx2*y1alt2+ry2*x1alt2))
		if node.large == node.sweep:
			f = -f
		cAlt = f * complex(r.real*p1alt.imag/r.imag, -r.imag*p1alt.real/r.real)

		c = cAlt + (p1 + p2) / 2 #TODO: apply rot

		a1 = math.atan2((p1alt.imag - cAlt.imag) / r.imag, (p1alt.real - cAlt.real) / r.real)
		a2 = math.atan2((p2alt.imag - cAlt.imag) / r.imag, (p2alt.real - cAlt.real) / r.real)

		large = abs(a2 - a1) > math.pi
		if large != node.large:
			if a1 < a2:
				a1 += math.pi * 2
			else:
				a2 += math.pi * 2

		return c, a1, a2, r

	def getPoints(self, accuracy = 1.0):
		pointList = [(self._startPoint, -1)]
		p1 = self._startPoint
		idx = -1
		for node in self._nodes:
			idx += 1
			if node.type == Node.LINE:
				p1 = node.position
				pointList.append((p1, idx))
			elif node.type == Node.ARC:
				p2 = node.position
				c, a1, a2, r = self.getArcInfo(node)

				pCenter = c + complex(math.cos(a1 + 0.5*(a2-a1)) * r.real, math.sin(a1 + 0.5*(a2-a1)) * r.imag)
				dist = abs(pCenter - p1) + abs(pCenter - p2)
				segments = int(dist / accuracy) + 1
				for n in xrange(1, segments):
					p = c + complex(math.cos(a1 + n*(a2-a1)/segments) * r.real, math.sin(a1 + n*(a2-a1)/segments) * r.imag)
					pointList.append((p, idx))

				pointList.append((p2, idx))
				p1 = p2
			elif node.type == Node.CURVE:
				p2 = node.position
				cp1 = node.cp1
				cp2 = node.cp2

				pCenter = p1*0.5*0.5*0.5 + cp1*3.0*0.5*0.5*0.5 + cp2*3.0*0.5*0.5*0.5 + p2*0.5*0.5*0.5
				dist = abs(pCenter - p1) + abs(pCenter - p2)
				segments = int(dist / accuracy) + 1
				for n in xrange(1, segments):
					f = n / float(segments)
					g = 1.0-f
					point = p1*g*g*g + cp1*3.0*g*g*f + cp2*3.0*g*f*f + p2*f*f*f
					pointList.append((point, idx))

				pointList.append((p2, idx))
				p1 = p2

		return pointList

	#getSVGPath returns an SVG path string. Ths path string is not perfect when matrix transformations are involved.
	def getSVGPath(self):
		p0 = self._startPoint
		ret = 'M %f %f ' % (p0.real, p0.imag)
		for node in self._nodes:
			if node.type == Node.LINE:
				p0 = node.position
				ret += 'L %f %f' % (p0.real, p0.imag)
			elif node.type == Node.ARC:
				p0 = node.position
				radius = node.radius
				ret += 'A %f %f 0 %d %d %f %f' % (radius.real, radius.imag, 1 if node.large else 0, 1 if node.sweep else 0, p0.real, p0.imag)
			elif node.type == Node.CURVE:
				p0 = node.position
				cp1 = node.cp1
				cp2 = node.cp2
				ret += 'C %f %f %f %f %f %f' % (cp1.real, cp1.imag, cp2.real, cp2.imag, p0.real, p0.imag)

		return ret

	def getPathString(self):
		ret = '%f %f' % (self._startPoint.real, self._startPoint.imag)
		for node in self._nodes:
			if node.type == Node.LINE:
				ret += '|L %f %f' % (node.position.real, node.position.imag)
			elif node.type == Node.ARC:
				ret += '|A %f %f %f %f %d %d' % (node.position.real, node.position.imag, node.radius.real, node.radius.imag, 1 if node.large else 0, 1 if node.sweep else 0)
			elif node.type == Node.CURVE:
				ret += '|C %f %f %f %f %f %f' % (node.position.real, node.position.imag, node.cp1.real, node.cp1.imag, node.cp2.real, node.cp2.imag)
		return ret

	def _m(self, p):
		tmp = numpy.matrix([p.real, p.imag, 1], numpy.float64) * self._matrix
		return complex(tmp[0,0], tmp[0,1])

	def _r(self, p):
		tmp = numpy.matrix([p.real, p.imag], numpy.float64) * self._relMatrix
		return complex(tmp[0,0], tmp[0,1])

class Drawing(object):
	def __init__(self):
		self.paths = []

	def addPath(self, x, y, matrix=numpy.matrix(numpy.identity(3, numpy.float64))):
		p = Path(x, y, matrix)
		self.paths.append(p)
		return p

	def _postProcessPaths(self):
		for path1 in self.paths:
			if not path1.isClosed() and len(path1._nodes) > 0:
				for path2 in self.paths:
					if path1 != path2 and not path2.isClosed():
						if abs(path1._nodes[-1].position - path2._startPoint) < 0.001:
							path1._nodes += path2._nodes
							path2._nodes = []

		cleanList = []
		for path in self.paths:
			if len(path._nodes) < 1:
				cleanList.append(path)
		for path in cleanList:
			self.paths.remove(path)

		for path in self.paths:
			if not path.isClosed():
				if abs(path._nodes[-1].position - path._startPoint) < 0.001:
					path._isClosed = True
			if path.isClosed() and len(path._nodes) == 2 and path._nodes[0].type == Node.ARC and path._nodes[1].type == Node.ARC:
				if abs(path._nodes[0].radius - path._nodes[1].radius) < 0.001:
					pass
					#path._nodes = []

	def dumpToFile(self, file):
		file.write("%d\n" % (len(self.paths)))
		for path in self.paths:
			file.write("%s\n" % (path.getPathString()))

	def readFromFile(self, file):
		self.paths = []
		pathCount = int(file.readline())
		for n in xrange(0, pathCount):
			line = map(str.split, file.readline().strip().split('|'))
			path = Path(float(line[0][0]), float(line[0][1]))
			for item in line[1:]:
				if item[0] == 'L':
					path.addLineTo(float(item[1]), float(item[2]))
				elif item[0] == 'A':
					path.addArcTo(float(item[1]), float(item[2]), 0, float(item[3]), float(item[4]), int(item[5]) != 0, int(item[6]) != 0)
				elif item[0] == 'C':
					path.addCurveTo(float(item[1]), float(item[2]), float(item[3]), float(item[4]), float(item[5]), float(item[6]))
			self.paths.append(path)
		self._postProcessPaths()

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
