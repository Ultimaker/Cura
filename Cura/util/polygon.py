__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import numpy

def convexHull(pointList):
	def _isRightTurn((p, q, r)):
		sum1 = q[0]*r[1] + p[0]*q[1] + r[0]*p[1]
		sum2 = q[0]*p[1] + r[0]*q[1] + p[0]*r[1]

		if sum1 - sum2 < 0:
			return 1
		else:
			return 0

	unique = {}
	for p in pointList:
		unique[p[0],p[1]] = 1

	points = unique.keys()
	points.sort()

	# Build upper half of the hull.
	upper = [points[0], points[1]]
	for p in points[2:]:
		upper.append(p)
		while len(upper) > 2 and not _isRightTurn(upper[-3:]):
			del upper[-2]

	# Build lower half of the hull.
	points = points[::-1]
	lower = [points[0], points[1]]
	for p in points[2:]:
		lower.append(p)
		while len(lower) > 2 and not _isRightTurn(lower[-3:]):
			del lower[-2]

	# Remove duplicates.
	del lower[0]
	del lower[-1]

	return numpy.array(upper + lower, numpy.float32) - numpy.array([0.0,0.0], numpy.float32)

def minkowskiHull(a, b):
	points = numpy.zeros((len(a) * len(b), 2))
	for n in xrange(0, len(a)):
		for m in xrange(0, len(b)):
			points[n * len(b) + m] = a[n] + b[m]
	return convexHull(points.copy())

def projectPoly(poly, normal):
	pMin = numpy.dot(normal, poly[0])
	pMax = pMin
	for n in xrange(1 , len(poly)):
		p = numpy.dot(normal, poly[n])
		pMin = min(pMin, p)
		pMax = max(pMax, p)
	return pMin, pMax

def polygonCollision(polyA, polyB):
	for n in xrange(0, len(polyA)):
		p0 = polyA[n-1]
		p1 = polyA[n]
		normal = (p1 - p0)[::-1]
		normal[1] = -normal[1]
		normal /= numpy.linalg.norm(normal)
		aMin, aMax = projectPoly(polyA, normal)
		bMin, bMax = projectPoly(polyB, normal)
		if aMin > bMax:
			return False
		if bMin > aMax:
			return False
	for n in xrange(0, len(polyB)):
		p0 = polyB[n-1]
		p1 = polyB[n]
		normal = (p1 - p0)[::-1]
		normal[1] = -normal[1]
		normal /= numpy.linalg.norm(normal)
		aMin, aMax = projectPoly(polyA, normal)
		bMin, bMax = projectPoly(polyB, normal)
		if aMin > bMax:
			return False
		if aMax < bMin:
			return False
	return True
