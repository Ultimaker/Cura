'''
Created on Jul 22, 2011

@author: Rio
'''

import blockrotation
from box import BoundingBox
from collections import defaultdict
from entity import Entity, TileEntity
import itertools
from logging import getLogger
import materials
from math import floor
from mclevelbase import ChunkMalformed, ChunkNotPresent, exhaust
import nbt
from numpy import argmax, swapaxes, zeros, zeros_like
import os.path

log = getLogger(__name__)

def computeChunkHeightMap(materials, blocks, HeightMap=None):
    """Computes the HeightMap array for a chunk, which stores the lowest
    y-coordinate of each column where the sunlight is still at full strength.
    The HeightMap array is indexed z,x contrary to the blocks array which is x,z,y.

    If HeightMap is passed, fills it with the result and returns it. Otherwise, returns a
    new array.
    """

    lightAbsorption = materials.lightAbsorption[blocks]
    heights = extractHeights(lightAbsorption)
    heights = heights.swapaxes(0, 1)
    if HeightMap is None:
        return heights.astype('uint8')
    else:
        HeightMap[:] = heights
        return HeightMap


def extractHeights(array):
    """ Given an array of bytes shaped (x, z, y), return the coordinates of the highest
    non-zero value in each y-column into heightMap
    """

    # The fastest way I've found to do this is to make a boolean array with >0,
    # then turn it upside down with ::-1 and use argmax to get the _first_ nonzero
    # from each column.

    w, h = array.shape[:2]
    heightMap = zeros((w, h), 'int16')

    heights = argmax((array > 0)[..., ::-1], 2)
    heights = array.shape[2] - heights

    # if the entire column is air, argmax finds the first air block and the result is a top height column
    # top height columns won't ever have air in the top block so we can find air columns by checking for both
    heights[(array[..., -1] == 0) & (heights == array.shape[2])] = 0

    heightMap[:] = heights

    return heightMap


def getSlices(box, height):
    """ call this method to iterate through a large slice of the world by
        visiting each chunk and indexing its data with a subslice.

    this returns an iterator, which yields 3-tuples containing:
    +  a pair of chunk coordinates (cx, cz),
    +  a x,z,y triplet of slices that can be used to index the AnvilChunk's data arrays,
    +  a x,y,z triplet representing the relative location of this subslice within the requested world slice.

    Note the different order of the coordinates between the 'slices' triplet
    and the 'offset' triplet. x,z,y ordering is used only
    to index arrays, since it reflects the order of the blocks in memory.
    In all other places, including an entity's 'Pos', the order is x,y,z.
    """

    # when yielding slices of chunks on the edge of the box, adjust the
    # slices by an offset
    minxoff, minzoff = box.minx - (box.mincx << 4), box.minz - (box.mincz << 4)
    maxxoff, maxzoff = box.maxx - (box.maxcx << 4) + 16, box.maxz - (box.maxcz << 4) + 16

    newMinY = 0
    if box.miny < 0:
        newMinY = -box.miny
    miny = max(0, box.miny)
    maxy = min(height, box.maxy)

    for cx in range(box.mincx, box.maxcx):
        localMinX = 0
        localMaxX = 16
        if cx == box.mincx:
            localMinX = minxoff

        if cx == box.maxcx - 1:
            localMaxX = maxxoff
        newMinX = localMinX + (cx << 4) - box.minx

        for cz in range(box.mincz, box.maxcz):
            localMinZ = 0
            localMaxZ = 16
            if cz == box.mincz:
                localMinZ = minzoff
            if cz == box.maxcz - 1:
                localMaxZ = maxzoff
            newMinZ = localMinZ + (cz << 4) - box.minz
            slices, point = (
                (slice(localMinX, localMaxX), slice(localMinZ, localMaxZ), slice(miny, maxy)),
                (newMinX, newMinY, newMinZ)
            )

            yield (cx, cz), slices, point


class MCLevel(object):
    """ MCLevel is an abstract class providing many routines to the different level types,
    including a common copyEntitiesFrom built on class-specific routines, and
    a dummy getChunk/allChunks for the finite levels.

    MCLevel subclasses must have Width, Length, and Height attributes.  The first two are always zero for infinite levels.
    Subclasses must also have Blocks, and optionally Data and BlockLight.
    """

    ### common to Creative, Survival and Indev. these routines assume
    ### self has Width, Height, Length, and Blocks

    materials = materials.classicMaterials
    isInfinite = False

    root_tag = None

    Height = None
    Length = None
    Width = None

    players = ["Player"]
    dimNo = 0
    parentWorld = None
    world = None

    @classmethod
    def isLevel(cls, filename):
        """Tries to find out whether the given filename can be loaded
        by this class.  Returns True or False.

        Subclasses should implement _isLevel, _isDataLevel, or _isTagLevel.
        """
        if hasattr(cls, "_isLevel"):
            return cls._isLevel(filename)

        with file(filename) as f:
            data = f.read()

        if hasattr(cls, "_isDataLevel"):
            return cls._isDataLevel(data)

        if hasattr(cls, "_isTagLevel"):
            try:
                root_tag = nbt.load(filename, data)
            except:
                return False

            return cls._isTagLevel(root_tag)

        return False

    def getWorldBounds(self):
        return BoundingBox((0, 0, 0), self.size)

    @property
    def displayName(self):
        return os.path.basename(self.filename)

    @property
    def size(self):
        "Returns the level's dimensions as a tuple (X,Y,Z)"
        return self.Width, self.Height, self.Length

    @property
    def bounds(self):
        return BoundingBox((0, 0, 0), self.size)

    def close(self):
        pass

    # --- Entity Methods ---
    def addEntity(self, entityTag):
        pass

    def addEntities(self, entities):
        pass

    def tileEntityAt(self, x, y, z):
        return None

    def addTileEntity(self, entityTag):
        pass

    def getEntitiesInBox(self, box):
        return []

    def getTileEntitiesInBox(self, box):
        return []

    def removeEntitiesInBox(self, box):
        pass

    def removeTileEntitiesInBox(self, box):
        pass

    @property
    def chunkCount(self):
        return (self.Width + 15 >> 4) * (self.Length + 15 >> 4)

    @property
    def allChunks(self):
        """Returns a synthetic list of chunk positions (xPos, zPos), to fake
        being a chunked level format."""
        return itertools.product(xrange(0, self.Width + 15 >> 4), xrange(0, self.Length + 15 >> 4))

    def getChunks(self, chunks=None):
        """ pass a list of chunk coordinate tuples to get an iterator yielding
        AnvilChunks. pass nothing for an iterator of every chunk in the level.
        the chunks are automatically loaded."""
        if chunks is None:
            chunks = self.allChunks
        return (self.getChunk(cx, cz) for (cx, cz) in chunks if self.containsChunk(cx, cz))

    def _getFakeChunkEntities(self, cx, cz):
        """Returns Entities, TileEntities"""
        return nbt.TAG_List(), nbt.TAG_List()

    def getChunk(self, cx, cz):
        """Synthesize a FakeChunk object representing the chunk at the given
        position. Subclasses override fakeBlocksForChunk and fakeDataForChunk
        to fill in the chunk arrays"""

        f = FakeChunk()
        f.world = self
        f.chunkPosition = (cx, cz)

        f.Blocks = self.fakeBlocksForChunk(cx, cz)

        f.Data = self.fakeDataForChunk(cx, cz)

        whiteLight = zeros_like(f.Blocks)
        whiteLight[:] = 15

        f.BlockLight = whiteLight
        f.SkyLight = whiteLight

        f.Entities, f.TileEntities = self._getFakeChunkEntities(cx, cz)

        f.root_tag = nbt.TAG_Compound()

        return f

    def getAllChunkSlices(self):
        slices = (slice(None), slice(None), slice(None),)
        box = self.bounds
        x, y, z = box.origin

        for cpos in self.allChunks:
            xPos, zPos = cpos
            try:
                chunk = self.getChunk(xPos, zPos)
            except (ChunkMalformed, ChunkNotPresent):
                continue

            yield (chunk, slices, (xPos * 16 - x, 0, zPos * 16 - z))

    def _getSlices(self, box):
        if box == self.bounds:
            log.info("All chunks selected! Selecting %s chunks instead of %s", self.chunkCount, box.chunkCount)
            y = box.miny
            slices = slice(0, 16), slice(0, 16), slice(0, box.maxy)

            def getAllSlices():
                for cPos in self.allChunks:
                    x, z = cPos
                    x *= 16
                    z *= 16
                    x -= box.minx
                    z -= box.minz
                    yield cPos, slices, (x, y, z)
            return getAllSlices()
        else:
            return getSlices(box, self.Height)

    def getChunkSlices(self, box):
        return ((self.getChunk(*cPos), slices, point)
                for cPos, slices, point in self._getSlices(box)
                if self.containsChunk(*cPos))

    def containsPoint(self, x, y, z):
        return (x, y, z) in self.bounds

    def containsChunk(self, cx, cz):
        bounds = self.bounds
        return ((bounds.mincx <= cx < bounds.maxcx) and
                (bounds.mincz <= cz < bounds.maxcz))

    def fakeBlocksForChunk(self, cx, cz):
        # return a 16x16xH block array for rendering.  Alpha levels can
        # just return the chunk data.  other levels need to reorder the
        # indices and return a slice of the blocks.

        cxOff = cx << 4
        czOff = cz << 4
        b = self.Blocks[cxOff:cxOff + 16, czOff:czOff + 16, 0:self.Height, ]
        # (w, l, h) = b.shape
        # if w<16 or l<16:
        #    b = resize(b, (16,16,h) )
        return b

    def fakeDataForChunk(self, cx, cz):
        # Data is emulated for flexibility
        cxOff = cx << 4
        czOff = cz << 4

        if hasattr(self, "Data"):
            return self.Data[cxOff:cxOff + 16, czOff:czOff + 16, 0:self.Height, ]

        else:
            return zeros(shape=(16, 16, self.Height), dtype='uint8')

    # --- Block accessors ---
    def skylightAt(self, *args):
        return 15

    def setSkylightAt(self, *args):
        pass

    def setBlockDataAt(self, x, y, z, newdata):
        pass

    def blockDataAt(self, x, y, z):
        return 0

    def blockLightAt(self, x, y, z):
        return 15

    def blockAt(self, x, y, z):
        if (x, y, z) not in self.bounds:
            return 0
        return self.Blocks[x, z, y]

    def setBlockAt(self, x, y, z, blockID):
        if (x, y, z) not in self.bounds:
            return 0
        self.Blocks[x, z, y] = blockID

    # --- Fill and Replace ---

    from block_fill import fillBlocks, fillBlocksIter

    # --- Transformations ---
    def rotateLeft(self):
        self.Blocks = swapaxes(self.Blocks, 1, 0)[:, ::-1, :]  # x=z; z=-x
        pass

    def roll(self):
        self.Blocks = swapaxes(self.Blocks, 2, 0)[:, :, ::-1]  # x=y; y=-x
        pass

    def flipVertical(self):
        self.Blocks = self.Blocks[:, :, ::-1]  # y=-y
        pass

    def flipNorthSouth(self):
        self.Blocks = self.Blocks[::-1, :, :]  # x=-x
        pass

    def flipEastWest(self):
        self.Blocks = self.Blocks[:, ::-1, :]  # z=-z
        pass

    # --- Copying ---

    from block_copy import copyBlocksFrom, copyBlocksFromIter


    def saveInPlace(self):
        self.saveToFile(self.filename)

    # --- Player Methods ---
    def setPlayerPosition(self, pos, player="Player"):
        pass

    def getPlayerPosition(self, player="Player"):
        return 8, self.Height * 0.75, 8

    def getPlayerDimension(self, player="Player"):
        return 0

    def setPlayerDimension(self, d, player="Player"):
        return

    def setPlayerSpawnPosition(self, pos, player=None):
        pass

    def playerSpawnPosition(self, player=None):
        return self.getPlayerPosition()

    def setPlayerOrientation(self, yp, player="Player"):
        pass

    def getPlayerOrientation(self, player="Player"):
        return -45., 0.

    # --- Dummy Lighting Methods ---
    def generateLights(self, dirtyChunks=None):
        pass

    def generateLightsIter(self, dirtyChunks=None):
        yield 0


class EntityLevel(MCLevel):
    """Abstract subclass of MCLevel that adds default entity behavior"""

    def getEntitiesInBox(self, box):
        """Returns a list of references to entities in this chunk, whose positions are within box"""
        return [ent for ent in self.Entities if Entity.pos(ent) in box]

    def getTileEntitiesInBox(self, box):
        """Returns a list of references to tile entities in this chunk, whose positions are within box"""
        return [ent for ent in self.TileEntities if TileEntity.pos(ent) in box]

    def removeEntitiesInBox(self, box):

        newEnts = []
        for ent in self.Entities:
            if Entity.pos(ent) in box:
                continue
            newEnts.append(ent)

        entsRemoved = len(self.Entities) - len(newEnts)
        log.debug("Removed {0} entities".format(entsRemoved))

        self.Entities.value[:] = newEnts

        return entsRemoved

    def removeTileEntitiesInBox(self, box):

        if not hasattr(self, "TileEntities"):
            return
        newEnts = []
        for ent in self.TileEntities:
            if TileEntity.pos(ent) in box:
                continue
            newEnts.append(ent)

        entsRemoved = len(self.TileEntities) - len(newEnts)
        log.debug("Removed {0} tile entities".format(entsRemoved))

        self.TileEntities.value[:] = newEnts

        return entsRemoved

    def addEntities(self, entities):
        for e in entities:
            self.addEntity(e)

    def addEntity(self, entityTag):
        assert isinstance(entityTag, nbt.TAG_Compound)
        self.Entities.append(entityTag)
        self._fakeEntities = None

    def tileEntityAt(self, x, y, z):
        entities = []
        for entityTag in self.TileEntities:
            if TileEntity.pos(entityTag) == [x, y, z]:
                entities.append(entityTag)

        if len(entities) > 1:
            log.info("Multiple tile entities found: {0}".format(entities))
        if len(entities) == 0:
            return None

        return entities[0]

    def addTileEntity(self, tileEntityTag):
        assert isinstance(tileEntityTag, nbt.TAG_Compound)

        def differentPosition(a):

            return not ((tileEntityTag is a) or TileEntity.pos(a) == TileEntity.pos(tileEntityTag))

        self.TileEntities.value[:] = filter(differentPosition, self.TileEntities)

        self.TileEntities.append(tileEntityTag)
        self._fakeEntities = None

    _fakeEntities = None

    def _getFakeChunkEntities(self, cx, cz):
        """distribute entities into sublists based on fake chunk position
        _fakeEntities keys are (cx, cz) and values are (Entities, TileEntities)"""
        if self._fakeEntities is None:
            self._fakeEntities = defaultdict(lambda: (nbt.TAG_List(), nbt.TAG_List()))
            for i, e in enumerate((self.Entities, self.TileEntities)):
                for ent in e:
                    x, y, z = [Entity, TileEntity][i].pos(ent)
                    ecx, ecz = map(lambda x: (int(floor(x)) >> 4), (x, z))

                    self._fakeEntities[ecx, ecz][i].append(ent)

        return self._fakeEntities[cx, cz]


class ChunkBase(EntityLevel):
    dirty = False
    needsLighting = False

    chunkPosition = NotImplemented
    Blocks = Data = SkyLight = BlockLight = HeightMap = NotImplemented  # override these!

    Width = Length = 16

    @property
    def Height(self):
        return self.world.Height

    @property
    def bounds(self):
        cx, cz = self.chunkPosition
        return BoundingBox((cx << 4, 0, cz << 4), self.size)


    def chunkChanged(self, needsLighting=True):
        self.dirty = True
        self.needsLighting = needsLighting or self.needsLighting

    @property
    def materials(self):
        return self.world.materials


    def getChunkSlicesForBox(self, box):
        """
         Given a BoundingBox enclosing part of the world, return a smaller box enclosing the part of this chunk
         intersecting the given box, and a tuple of slices that can be used to select the corresponding parts
         of this chunk's block and data arrays.
        """
        bounds = self.bounds
        localBox = box.intersect(bounds)

        slices = (
            slice(localBox.minx - bounds.minx, localBox.maxx - bounds.minx),
            slice(localBox.minz - bounds.minz, localBox.maxz - bounds.minz),
            slice(localBox.miny - bounds.miny, localBox.maxy - bounds.miny),
        )
        return localBox, slices


class FakeChunk(ChunkBase):
    @property
    def HeightMap(self):
        if hasattr(self, "_heightMap"):
            return self._heightMap

        self._heightMap = computeChunkHeightMap(self.materials, self.Blocks)
        return self._heightMap


class LightedChunk(ChunkBase):
    def generateHeightMap(self):
        computeChunkHeightMap(self.materials, self.Blocks, self.HeightMap)

    def chunkChanged(self, calcLighting=True):
        """ You are required to call this function after you are done modifying
        the chunk. Pass False for calcLighting if you know your changes will
        not change any lights."""

        self.dirty = True
        self.needsLighting = calcLighting or self.needsLighting
        self.generateHeightMap()
        if calcLighting:
            self.genFastLights()

    def genFastLights(self):
        self.SkyLight[:] = 0
        if self.world.dimNo in (-1, 1):
            return  # no light in nether or the end

        blocks = self.Blocks
        la = self.world.materials.lightAbsorption
        skylight = self.SkyLight
        heightmap = self.HeightMap

        for x, z in itertools.product(xrange(16), xrange(16)):

            skylight[x, z, heightmap[z, x]:] = 15
            lv = 15
            for y in reversed(range(heightmap[z, x])):
                lv -= (la[blocks[x, z, y]] or 1)

                if lv <= 0:
                    break
                skylight[x, z, y] = lv
