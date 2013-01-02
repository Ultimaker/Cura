from collections import namedtuple
import itertools

_Vector = namedtuple("_Vector", ("x", "y", "z"))

class Vector(_Vector):

    __slots__ = ()

    def __add__(self, other):
        return Vector(self[0] + other[0], self[1] + other[1], self[2] + other[2])
    def __sub__(self, other):
        return Vector(self[0] - other[0], self[1] - other[1], self[2] - other[2])
    def __mul__(self, other):
        return Vector(self[0] * other[0], self[1] * other[1], self[2] * other[2])

class BoundingBox (object):
    type = int

    def __init__(self, origin=(0, 0, 0), size=(0, 0, 0)):
        if isinstance(origin, BoundingBox):
            self._origin = origin._origin
            self._size = origin._size
        else:
            self._origin, self._size = Vector(*(self.type(a) for a in origin)), Vector(*(self.type(a) for a in size))

    def __repr__(self):
        return "BoundingBox({0}, {1})".format(self.origin, self.size)

    @property
    def origin(self):
        "The smallest position in the box"
        return self._origin

    @property
    def size(self):
        "The size of the box"
        return self._size

    @property
    def width(self):
        "The dimension along the X axis"
        return self._size.x

    @property
    def height(self):
        "The dimension along the Y axis"
        return self._size.y

    @property
    def length(self):
        "The dimension along the Z axis"
        return self._size.z

    @property
    def minx(self):
        return self.origin.x

    @property
    def miny(self):
        return self.origin.y

    @property
    def minz(self):
        return self.origin.z

    @property
    def maxx(self):
        return self.origin.x + self.size.x

    @property
    def maxy(self):
        return self.origin.y + self.size.y

    @property
    def maxz(self):
        return self.origin.z + self.size.z

    @property
    def maximum(self):
        "The largest point of the box; origin plus size."
        return self._origin + self._size

    @property
    def volume(self):
        "The volume of the box in blocks"
        return self.size.x * self.size.y * self.size.z

    @property
    def positions(self):
        """iterate through all of the positions within this selection box"""
        return itertools.product(
            xrange(self.minx, self.maxx),
            xrange(self.miny, self.maxy),
            xrange(self.minz, self.maxz)
        )

    def intersect(self, box):
        """
        Return a box containing the area self and box have in common. Box will have zero volume
         if there is no common area.
        """
        if (self.minx > box.maxx or self.maxx < box.minx or
            self.miny > box.maxy or self.maxy < box.miny or
            self.minz > box.maxz or self.maxz < box.minz):
            #Zero size intersection.
            return BoundingBox()

        origin = Vector(
            max(self.minx, box.minx),
            max(self.miny, box.miny),
            max(self.minz, box.minz),
        )
        maximum = Vector(
            min(self.maxx, box.maxx),
            min(self.maxy, box.maxy),
            min(self.maxz, box.maxz),
        )

        #print "Intersect of {0} and {1}: {2}".format(self, box, newbox)
        return BoundingBox(origin, maximum - origin)

    def union(self, box):
        """
        Return a box large enough to contain both self and box.
        """
        origin = Vector(
            min(self.minx, box.minx),
            min(self.miny, box.miny),
            min(self.minz, box.minz),
        )
        maximum = Vector(
            max(self.maxx, box.maxx),
            max(self.maxy, box.maxy),
            max(self.maxz, box.maxz),
        )
        return BoundingBox(origin, maximum - origin)

    def expand(self, dx, dy=None, dz=None):
        """
        Return a new box with boundaries expanded by dx, dy, dz.
        If only dx is passed, expands by dx in all dimensions.
        """
        if dz is None:
            dz = dx
        if dy is None:
            dy = dx

        origin = self.origin - (dx, dy, dz)
        size = self.size + (dx * 2, dy * 2, dz * 2)

        return BoundingBox(origin, size)

    def __contains__(self, pos):
        x, y, z = pos
        if x < self.minx or x >= self.maxx:
            return False
        if y < self.miny or y >= self.maxy:
            return False
        if z < self.minz or z >= self.maxz:
            return False

        return True

    def __cmp__(self, b):
        return cmp((self.origin, self.size), (b.origin, b.size))


    # --- Chunk positions ---

    @property
    def mincx(self):
        "The smallest chunk position contained in this box"
        return self.origin.x >> 4

    @property
    def mincz(self):
        "The smallest chunk position contained in this box"
        return self.origin.z >> 4

    @property
    def maxcx(self):
        "The largest chunk position contained in this box"
        return ((self.origin.x + self.size.x - 1) >> 4) + 1

    @property
    def maxcz(self):
        "The largest chunk position contained in this box"
        return ((self.origin.z + self.size.z - 1) >> 4) + 1

    def chunkBox(self, level):
        """Returns this box extended to the chunk boundaries of the given level"""
        box = self
        return BoundingBox((box.mincx << 4, 0, box.mincz << 4),
                           (box.maxcx - box.mincx << 4, level.Height, box.maxcz - box.mincz << 4))

    @property
    def chunkPositions(self):
        #iterate through all of the chunk positions within this selection box
        return itertools.product(xrange(self.mincx, self.maxcx), xrange(self.mincz, self.maxcz))

    @property
    def chunkCount(self):
        return (self.maxcx - self.mincx) * (self.maxcz - self.mincz)

    @property
    def isChunkAligned(self):
        return (self.origin.x & 0xf == 0) and (self.origin.z & 0xf == 0)

class FloatBox (BoundingBox):
    type = float
