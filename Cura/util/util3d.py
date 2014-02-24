"""
The util3d module a vector class to work with 3D points. All the basic math operators have been overloaded to work on this object.
This module is deprecated and only used by the SplitModels function.

Use numpy arrays instead to work with vectors.
"""
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import math

class Vector3(object):
	""" 3D vector object. """
	def __init__(self, x=0.0, y=0.0, z=0.0):
		"""Create a new 3D vector"""
		self.x = x
		self.y = y
		self.z = z

	def __copy__(self):
		return Vector3(self.x, self.y, self.z)

	def copy(self):
		return Vector3(self.x, self.y, self.z)

	def __repr__(self):
		return 'V[%s, %s, %s]' % ( self.x, self.y, self.z )

	def __add__(self, v):
		return Vector3( self.x + v.x, self.y + v.y, self.z + v.z )

	def __sub__(self, v):
		return Vector3( self.x - v.x, self.y - v.y, self.z - v.z )

	def __mul__(self, v):
		return Vector3( self.x * v, self.y * v, self.z * v )

	def __div__(self, v):
		return Vector3( self.x / v, self.y / v, self.z / v )
	__truediv__ = __div__

	def __neg__(self):
		return Vector3( - self.x, - self.y, - self.z )

	def __iadd__(self, v):
		self.x += v.x
		self.y += v.y
		self.z += v.z
		return self

	def __isub__(self, v):
		self.x += v.x
		self.y += v.y
		self.z += v.z
		return self

	def __imul__(self, v):
		self.x *= v
		self.y *= v
		self.z *= v
		return self

	def __idiv__(self, v):
		self.x /= v
		self.y /= v
		self.z /= v
		return self

	def almostEqual(self, v):
		return (abs(self.x - v.x) + abs(self.y - v.y) + abs(self.z - v.z)) < 0.00001
	
	def cross(self, v):
		return Vector3(self.y * v.z - self.z * v.y, -self.x * v.z + self.z * v.x, self.x * v.y - self.y * v.x)

	def vsize(self):
		return math.sqrt( self.x * self.x + self.y * self.y + self.z * self.z )

	def normalize(self):
		f = self.vsize()
		if f != 0.0:
			self.x /= f
			self.y /= f
			self.z /= f

	def min(self, v):
		return Vector3(min(self.x, v.x), min(self.y, v.y), min(self.z, v.z))

	def max(self, v):
		return Vector3(max(self.x, v.x), max(self.y, v.y), max(self.z, v.z))

