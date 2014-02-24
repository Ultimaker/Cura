"""
The polygon module has functions that assist in working with 2D convex polygons.
"""
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import numpy

def convexHull(pointList):
	""" Create a convex hull from a list of points. """
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
	if len(points) < 1:
		return numpy.zeros((0, 2), numpy.float32)
	if len(points) < 2:
		return numpy.array(points, numpy.float32)

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

	return numpy.array(upper + lower, numpy.float32)

def minkowskiHull(a, b):
	"""Calculate the minkowski hull of 2 convex polygons"""
	points = numpy.zeros((len(a) * len(b), 2))
	for n in xrange(0, len(a)):
		for m in xrange(0, len(b)):
			points[n * len(b) + m] = a[n] + b[m]
	return convexHull(points.copy())

def projectPoly(poly, normal):
	"""
	Project a convex polygon on a given normal.
	A projection of a convex polygon on a infinite line is a finite line.
	Give the min and max value on the normal line.
	"""
	pMin = numpy.dot(normal, poly[0])
	pMax = pMin
	for n in xrange(1 , len(poly)):
		p = numpy.dot(normal, poly[n])
		pMin = min(pMin, p)
		pMax = max(pMax, p)
	return pMin, pMax

def polygonCollision(polyA, polyB):
	""" Check if convexy polygon A and B collide, return True if this is the case. """
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

def polygonCollisionPushVector(polyA, polyB):
	""" Check if convex polygon A and B collide, return the vector of penetration if this is the case, else return False. """
	retSize = 10000000.0
	ret = False
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
		size = min(bMax, bMax) - max(aMin, bMin)
		if size < retSize:
			ret = normal * (size + 0.1)
			retSize = size
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
		size = min(bMax, bMax) - max(aMin, bMin)
		if size < retSize:
			ret = normal * -(size + 0.1)
			retSize = size
	return ret

def fullInside(polyA, polyB):
	"""
	Check if convex polygon A is completely inside of convex polygon B.
	"""
	for n in xrange(0, len(polyA)):
		p0 = polyA[n-1]
		p1 = polyA[n]
		normal = (p1 - p0)[::-1]
		normal[1] = -normal[1]
		normal /= numpy.linalg.norm(normal)
		aMin, aMax = projectPoly(polyA, normal)
		bMin, bMax = projectPoly(polyB, normal)
		if aMax > bMax:
			return False
		if aMin < bMin:
			return False
	for n in xrange(0, len(polyB)):
		p0 = polyB[n-1]
		p1 = polyB[n]
		normal = (p1 - p0)[::-1]
		normal[1] = -normal[1]
		normal /= numpy.linalg.norm(normal)
		aMin, aMax = projectPoly(polyA, normal)
		bMin, bMax = projectPoly(polyB, normal)
		if aMax > bMax:
			return False
		if aMin < bMin:
			return False
	return True

def isLeft(a, b, c):
	""" Check if C is left of the infinite line from A to B """
	return ((b[0] - a[0])*(c[1] - a[1]) - (b[1] - a[1])*(c[0] - a[0])) > 0

def lineLineIntersection(p0, p1, p2, p3):
	""" Return the intersection of the infinite line trough points p0 and p1 and infinite line trough points p2 and p3. """
	A1 = p1[1] - p0[1]
	B1 = p0[0] - p1[0]
	C1 = A1*p0[0] + B1*p0[1]

	A2 = p3[1] - p2[1]
	B2 = p2[0] - p3[0]
	C2 = A2 * p2[0] + B2 * p2[1]

	det = A1*B2 - A2*B1
	if det == 0:
		return p0
	return [(B2*C1 - B1*C2)/det, (A1 * C2 - A2 * C1) / det]

def clipConvex(poly0, poly1):
	""" Cut the convex polygon 0 so that it completely fits in convex polygon 1, any part sticking out of polygon 1 is cut off """
	res = poly0
	for p1idx in xrange(0, len(poly1)):
		src = res
		res = []
		p0 = poly1[p1idx-1]
		p1 = poly1[p1idx]
		for n in xrange(0, len(src)):
			p = src[n]
			if not isLeft(p0, p1, p):
				if isLeft(p0, p1, src[n-1]):
					res.append(lineLineIntersection(p0, p1, src[n-1], p))
				res.append(p)
			elif not isLeft(p0, p1, src[n-1]):
				res.append(lineLineIntersection(p0, p1, src[n-1], p))
	return numpy.array(res, numpy.float32)
