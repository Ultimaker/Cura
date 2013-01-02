'''
Created on Jul 22, 2011

@author: Rio
'''

import copy
from datetime import datetime
import itertools
from logging import getLogger
from math import floor
import os
import re
import random
import shutil
import struct
import time
import traceback
import weakref
import zlib
import sys

import blockrotation
from box import BoundingBox
from entity import Entity, TileEntity
from faces import FaceXDecreasing, FaceXIncreasing, FaceZDecreasing, FaceZIncreasing
from level import LightedChunk, EntityLevel, computeChunkHeightMap, MCLevel, ChunkBase
from materials import alphaMaterials
from mclevelbase import ChunkMalformed, ChunkNotPresent, exhaust, PlayerNotFound
import nbt
from numpy import array, clip, maximum, zeros
from regionfile import MCRegionFile

log = getLogger(__name__)


DIM_NETHER = -1
DIM_END = 1

__all__ = ["ZeroChunk", "AnvilChunk", "ChunkedLevelMixin", "MCInfdevOldLevel", "MCAlphaDimension", "ZipSchematic"]
_zeros = {}

class SessionLockLost(IOError):
    pass



def ZeroChunk(height=512):
    z = _zeros.get(height)
    if z is None:
        z = _zeros[height] = _ZeroChunk(height)
    return z


class _ZeroChunk(ChunkBase):
    " a placebo for neighboring-chunk routines "

    def __init__(self, height=512):
        zeroChunk = zeros((16, 16, height), 'uint8')
        whiteLight = zeroChunk + 15
        self.Blocks = zeroChunk
        self.BlockLight = whiteLight
        self.SkyLight = whiteLight
        self.Data = zeroChunk


def unpackNibbleArray(dataArray):
    s = dataArray.shape
    unpackedData = zeros((s[0], s[1], s[2] * 2), dtype='uint8')

    unpackedData[:, :, ::2] = dataArray
    unpackedData[:, :, ::2] &= 0xf
    unpackedData[:, :, 1::2] = dataArray
    unpackedData[:, :, 1::2] >>= 4
    return unpackedData


def packNibbleArray(unpackedData):
    packedData = array(unpackedData.reshape(16, 16, unpackedData.shape[2] / 2, 2))
    packedData[..., 1] <<= 4
    packedData[..., 1] |= packedData[..., 0]
    return array(packedData[:, :, :, 1])

def sanitizeBlocks(chunk):
    # change grass to dirt where needed so Minecraft doesn't flip out and die
    grass = chunk.Blocks == chunk.materials.Grass.ID
    grass |= chunk.Blocks == chunk.materials.Dirt.ID
    badgrass = grass[:, :, 1:] & grass[:, :, :-1]

    chunk.Blocks[:, :, :-1][badgrass] = chunk.materials.Dirt.ID

    # remove any thin snow layers immediately above other thin snow layers.
    # minecraft doesn't flip out, but it's almost never intended
    if hasattr(chunk.materials, "SnowLayer"):
        snowlayer = chunk.Blocks == chunk.materials.SnowLayer.ID
        badsnow = snowlayer[:, :, 1:] & snowlayer[:, :, :-1]

        chunk.Blocks[:, :, 1:][badsnow] = chunk.materials.Air.ID


class AnvilChunkData(object):
    """ This is the chunk data backing an AnvilChunk. Chunk data is retained by the MCInfdevOldLevel until its
    AnvilChunk is no longer used, then it is either cached in memory, discarded, or written to disk according to
    resource limits.

    AnvilChunks are stored in a WeakValueDictionary so we can find out when they are no longer used by clients. The
    AnvilChunkData for an unused chunk may safely be discarded or written out to disk. The client should probably
     not keep references to a whole lot of chunks or else it will run out of memory.
    """
    def __init__(self, world, chunkPosition, root_tag = None, create = False):
        self.chunkPosition = chunkPosition
        self.world = world
        self.root_tag = root_tag
        self.dirty = False

        self.Blocks = zeros((16, 16, world.Height), 'uint8')  # xxx uint16?
        self.Data = zeros((16, 16, world.Height), 'uint8')
        self.BlockLight = zeros((16, 16, world.Height), 'uint8')
        self.SkyLight = zeros((16, 16, world.Height), 'uint8')
        self.SkyLight[:] = 15


        if create:
            self._create()
        else:
            self._load(root_tag)

    def _create(self):
        (cx, cz) = self.chunkPosition
        chunkTag = nbt.TAG_Compound()
        chunkTag.name = ""

        levelTag = nbt.TAG_Compound()
        chunkTag["Level"] = levelTag

        levelTag["HeightMap"] = nbt.TAG_Int_Array(zeros((16, 16), 'uint32').newbyteorder())
        levelTag["TerrainPopulated"] = nbt.TAG_Byte(1)
        levelTag["xPos"] = nbt.TAG_Int(cx)
        levelTag["zPos"] = nbt.TAG_Int(cz)

        levelTag["LastUpdate"] = nbt.TAG_Long(0)

        levelTag["Entities"] = nbt.TAG_List()
        levelTag["TileEntities"] = nbt.TAG_List()

        self.root_tag = chunkTag

        self.dirty = True

    def _load(self, root_tag):
        self.root_tag = root_tag

        for sec in self.root_tag["Level"].pop("Sections", []):
            y = sec["Y"].value * 16
            for name in "Blocks", "Data", "SkyLight", "BlockLight":
                arr = getattr(self, name)
                secarray = sec[name].value
                if name == "Blocks":
                    secarray.shape = (16, 16, 16)
                else:
                    secarray.shape = (16, 16, 8)
                    secarray = unpackNibbleArray(secarray)

                arr[..., y:y + 16] = secarray.swapaxes(0, 2)


    def savedTagData(self):
        """ does not recalculate any data or light """

        log.debug(u"Saving chunk: {0}".format(self))
        sanitizeBlocks(self)

        sections = nbt.TAG_List()
        for y in range(0, self.world.Height, 16):
            section = nbt.TAG_Compound()

            Blocks = self.Blocks[..., y:y + 16].swapaxes(0, 2)
            Data = self.Data[..., y:y + 16].swapaxes(0, 2)
            BlockLight = self.BlockLight[..., y:y + 16].swapaxes(0, 2)
            SkyLight = self.SkyLight[..., y:y + 16].swapaxes(0, 2)

            if (not Blocks.any() and
                not BlockLight.any() and
                (SkyLight == 15).all()):
                continue

            Data = packNibbleArray(Data)
            BlockLight = packNibbleArray(BlockLight)
            SkyLight = packNibbleArray(SkyLight)

            section['Blocks'] = nbt.TAG_Byte_Array(array(Blocks))
            section['Data'] = nbt.TAG_Byte_Array(array(Data))
            section['BlockLight'] = nbt.TAG_Byte_Array(array(BlockLight))
            section['SkyLight'] = nbt.TAG_Byte_Array(array(SkyLight))

            section["Y"] = nbt.TAG_Byte(y / 16)
            sections.append(section)

        self.root_tag["Level"]["Sections"] = sections
        data = self.root_tag.save(compressed=False)
        del self.root_tag["Level"]["Sections"]

        log.debug(u"Saved chunk {0}".format(self))
        return data

    @property
    def materials(self):
        return self.world.materials


class AnvilChunk(LightedChunk):
    """ This is a 16x16xH chunk in an (infinite) world.
    The properties Blocks, Data, SkyLight, BlockLight, and Heightmap
    are ndarrays containing the respective blocks in the chunk file.
    Each array is indexed [x,z,y].  The Data, Skylight, and BlockLight
    arrays are automatically unpacked from nibble arrays into byte arrays
    for better handling.
    """

    def __init__(self, chunkData):
        self.world = chunkData.world
        self.chunkPosition = chunkData.chunkPosition
        self.chunkData = chunkData


    def savedTagData(self):
        return self.chunkData.savedTagData()


    def __str__(self):
        return u"AnvilChunk, coords:{0}, world: {1}, D:{2}, L:{3}".format(self.chunkPosition, self.world.displayName, self.dirty, self.needsLighting)

    @property
    def needsLighting(self):
        return self.chunkPosition in self.world.chunksNeedingLighting

    @needsLighting.setter
    def needsLighting(self, value):
        if value:
            self.world.chunksNeedingLighting.add(self.chunkPosition)
        else:
            self.world.chunksNeedingLighting.discard(self.chunkPosition)

    def generateHeightMap(self):
        if self.world.dimNo == DIM_NETHER:
            self.HeightMap[:] = 0
        else:
            computeChunkHeightMap(self.materials, self.Blocks, self.HeightMap)

    def addEntity(self, entityTag):

        def doubleize(name):
            # This is needed for compatibility with Indev levels. Those levels use TAG_Float for entity motion and pos
            if name in entityTag:
                m = entityTag[name]
                entityTag[name] = nbt.TAG_List([nbt.TAG_Double(i.value) for i in m])

        doubleize("Motion")
        doubleize("Position")

        self.dirty = True
        return super(AnvilChunk, self).addEntity(entityTag)

    def removeEntitiesInBox(self, box):
        self.dirty = True
        return super(AnvilChunk, self).removeEntitiesInBox(box)

    def removeTileEntitiesInBox(self, box):
        self.dirty = True
        return super(AnvilChunk, self).removeTileEntitiesInBox(box)

    # --- AnvilChunkData accessors ---

    @property
    def root_tag(self):
        return self.chunkData.root_tag

    @property
    def dirty(self):
        return self.chunkData.dirty

    @dirty.setter
    def dirty(self, val):
        self.chunkData.dirty = val

    # --- Chunk attributes ---

    @property
    def materials(self):
        return self.world.materials

    @property
    def Blocks(self):
        return self.chunkData.Blocks

    @property
    def Data(self):
        return self.chunkData.Data

    @property
    def SkyLight(self):
        return self.chunkData.SkyLight

    @property
    def BlockLight(self):
        return self.chunkData.BlockLight

    @property
    def Biomes(self):
        return self.root_tag["Level"]["Biomes"].value.reshape((16, 16))

    @property
    def HeightMap(self):
        return self.root_tag["Level"]["HeightMap"].value.reshape((16, 16))

    @property
    def Entities(self):
        return self.root_tag["Level"]["Entities"]

    @property
    def TileEntities(self):
        return self.root_tag["Level"]["TileEntities"]

    @property
    def TerrainPopulated(self):
        return self.root_tag["Level"]["TerrainPopulated"].value

    @TerrainPopulated.setter
    def TerrainPopulated(self, val):
        """True or False. If False, the game will populate the chunk with
        ores and vegetation on next load"""
        self.root_tag["Level"]["TerrainPopulated"].value = val
        self.dirty = True


base36alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"


def decbase36(s):
    return int(s, 36)


def base36(n):
    global base36alphabet

    n = int(n)
    if 0 == n:
        return '0'
    neg = ""
    if n < 0:
        neg = "-"
        n = -n

    work = []

    while n:
        n, digit = divmod(n, 36)
        work.append(base36alphabet[digit])

    return neg + ''.join(reversed(work))


def deflate(data):
    # zobj = zlib.compressobj(6,zlib.DEFLATED,-zlib.MAX_WBITS,zlib.DEF_MEM_LEVEL,0)
    # zdata = zobj.compress(data)
    # zdata += zobj.flush()
    # return zdata
    return zlib.compress(data)


def inflate(data):
    return zlib.decompress(data)


class ChunkedLevelMixin(MCLevel):
    def blockLightAt(self, x, y, z):
        if y < 0 or y >= self.Height:
            return 0
        zc = z >> 4
        xc = x >> 4

        xInChunk = x & 0xf
        zInChunk = z & 0xf
        ch = self.getChunk(xc, zc)

        return ch.BlockLight[xInChunk, zInChunk, y]

    def setBlockLightAt(self, x, y, z, newLight):
        if y < 0 or y >= self.Height:
            return 0
        zc = z >> 4
        xc = x >> 4

        xInChunk = x & 0xf
        zInChunk = z & 0xf

        ch = self.getChunk(xc, zc)
        ch.BlockLight[xInChunk, zInChunk, y] = newLight
        ch.chunkChanged(False)

    def blockDataAt(self, x, y, z):
        if y < 0 or y >= self.Height:
            return 0
        zc = z >> 4
        xc = x >> 4

        xInChunk = x & 0xf
        zInChunk = z & 0xf

        try:
            ch = self.getChunk(xc, zc)
        except ChunkNotPresent:
            return 0

        return ch.Data[xInChunk, zInChunk, y]

    def setBlockDataAt(self, x, y, z, newdata):
        if y < 0 or y >= self.Height:
            return 0
        zc = z >> 4
        xc = x >> 4

        xInChunk = x & 0xf
        zInChunk = z & 0xf

        try:
            ch = self.getChunk(xc, zc)
        except ChunkNotPresent:
            return 0

        ch.Data[xInChunk, zInChunk, y] = newdata
        ch.dirty = True
        ch.needsLighting = True

    def blockAt(self, x, y, z):
        """returns 0 for blocks outside the loadable chunks.  automatically loads chunks."""
        if y < 0 or y >= self.Height:
            return 0

        zc = z >> 4
        xc = x >> 4
        xInChunk = x & 0xf
        zInChunk = z & 0xf

        try:
            ch = self.getChunk(xc, zc)
        except ChunkNotPresent:
            return 0

        return ch.Blocks[xInChunk, zInChunk, y]

    def setBlockAt(self, x, y, z, blockID):
        """returns 0 for blocks outside the loadable chunks.  automatically loads chunks."""
        if y < 0 or y >= self.Height:
            return 0

        zc = z >> 4
        xc = x >> 4
        xInChunk = x & 0xf
        zInChunk = z & 0xf

        try:
            ch = self.getChunk(xc, zc)
        except ChunkNotPresent:
            return 0

        ch.Blocks[xInChunk, zInChunk, y] = blockID
        ch.dirty = True
        ch.needsLighting = True

    def skylightAt(self, x, y, z):

        if y < 0 or y >= self.Height:
            return 0
        zc = z >> 4
        xc = x >> 4

        xInChunk = x & 0xf
        zInChunk = z & 0xf

        ch = self.getChunk(xc, zc)

        return ch.SkyLight[xInChunk, zInChunk, y]

    def setSkylightAt(self, x, y, z, lightValue):
        if y < 0 or y >= self.Height:
            return 0
        zc = z >> 4
        xc = x >> 4

        xInChunk = x & 0xf
        zInChunk = z & 0xf

        ch = self.getChunk(xc, zc)
        skyLight = ch.SkyLight

        oldValue = skyLight[xInChunk, zInChunk, y]

        ch.chunkChanged(False)
        if oldValue < lightValue:
            skyLight[xInChunk, zInChunk, y] = lightValue
        return oldValue < lightValue

    createChunk = NotImplemented



    def generateLights(self, dirtyChunkPositions=None):
        return exhaust(self.generateLightsIter(dirtyChunkPositions))

    def generateLightsIter(self, dirtyChunkPositions=None):
        """ dirtyChunks may be an iterable yielding (xPos,zPos) tuples
        if none, generate lights for all chunks that need lighting
        """

        startTime = datetime.now()

        if dirtyChunkPositions is None:
            dirtyChunkPositions = self.chunksNeedingLighting
        else:
            dirtyChunkPositions = (c for c in dirtyChunkPositions if self.containsChunk(*c))

        dirtyChunkPositions = sorted(dirtyChunkPositions)

        maxLightingChunks = getattr(self, 'loadedChunkLimit', 400)

        log.info(u"Asked to light {0} chunks".format(len(dirtyChunkPositions)))
        chunkLists = [dirtyChunkPositions]

        def reverseChunkPosition((cx, cz)):
            return cz, cx

        def splitChunkLists(chunkLists):
            newChunkLists = []
            for l in chunkLists:

                # list is already sorted on x position, so this splits into left and right

                smallX = l[:len(l) / 2]
                bigX = l[len(l) / 2:]

                # sort halves on z position
                smallX = sorted(smallX, key=reverseChunkPosition)
                bigX = sorted(bigX, key=reverseChunkPosition)

                # add quarters to list

                newChunkLists.append(smallX[:len(smallX) / 2])
                newChunkLists.append(smallX[len(smallX) / 2:])

                newChunkLists.append(bigX[:len(bigX) / 2])
                newChunkLists.append(bigX[len(bigX) / 2:])

            return newChunkLists

        while len(chunkLists[0]) > maxLightingChunks:
            chunkLists = splitChunkLists(chunkLists)

        if len(chunkLists) > 1:
            log.info(u"Using {0} batches to conserve memory.".format(len(chunkLists)))
        # batchSize = min(len(a) for a in chunkLists)
        estimatedTotals = [len(a) * 32 for a in chunkLists]
        workDone = 0

        for i, dc in enumerate(chunkLists):
            log.info(u"Batch {0}/{1}".format(i, len(chunkLists)))

            dc = sorted(dc)
            workTotal = sum(estimatedTotals)
            t = 0
            for c, t, p in self._generateLightsIter(dc):

                yield c + workDone, t + workTotal - estimatedTotals[i], p

            estimatedTotals[i] = t
            workDone += t

        timeDelta = datetime.now() - startTime

        if len(dirtyChunkPositions):
            log.info(u"Completed in {0}, {1} per chunk".format(timeDelta, dirtyChunkPositions and timeDelta / len(dirtyChunkPositions) or 0))

        return

    def _generateLightsIter(self, dirtyChunkPositions):
        la = array(self.materials.lightAbsorption)
        clip(la, 1, 15, la)

        dirtyChunks = set(self.getChunk(*cPos) for cPos in dirtyChunkPositions)

        workDone = 0
        workTotal = len(dirtyChunks) * 29

        progressInfo = (u"Lighting {0} chunks".format(len(dirtyChunks)))
        log.info(progressInfo)

        for i, chunk in enumerate(dirtyChunks):

            chunk.chunkChanged()
            yield i, workTotal, progressInfo
            assert chunk.dirty and chunk.needsLighting

        workDone += len(dirtyChunks)
        workTotal = len(dirtyChunks)

        for ch in list(dirtyChunks):
            # relight all blocks in neighboring chunks in case their light source disappeared.
            cx, cz = ch.chunkPosition
            for dx, dz in itertools.product((-1, 0, 1), (-1, 0, 1)):
                try:
                    ch = self.getChunk(cx + dx, cz + dz)
                except (ChunkNotPresent, ChunkMalformed):
                    continue
                dirtyChunks.add(ch)
                ch.dirty = True

        dirtyChunks = sorted(dirtyChunks, key=lambda x: x.chunkPosition)
        workTotal += len(dirtyChunks) * 28

        for i, chunk in enumerate(dirtyChunks):
            chunk.BlockLight[:] = self.materials.lightEmission[chunk.Blocks]
            chunk.dirty = True

        zeroChunk = ZeroChunk(self.Height)
        zeroChunk.BlockLight[:] = 0
        zeroChunk.SkyLight[:] = 0

        startingDirtyChunks = dirtyChunks

        oldLeftEdge = zeros((1, 16, self.Height), 'uint8')
        oldBottomEdge = zeros((16, 1, self.Height), 'uint8')
        oldChunk = zeros((16, 16, self.Height), 'uint8')
        if self.dimNo in (-1, 1):
            lights = ("BlockLight",)
        else:
            lights = ("BlockLight", "SkyLight")
        log.info(u"Dispersing light...")

        def clipLight(light):
            # light arrays are all uint8 by default, so when results go negative
            # they become large instead.  reinterpret as signed int using view()
            # and then clip to range
            light.view('int8').clip(0, 15, light)

        for j, light in enumerate(lights):
            zerochunkLight = getattr(zeroChunk, light)
            newDirtyChunks = list(startingDirtyChunks)

            work = 0

            for i in range(14):
                if len(newDirtyChunks) == 0:
                    workTotal -= len(startingDirtyChunks) * (14 - i)
                    break

                progressInfo = u"{0} Pass {1}: {2} chunks".format(light, i, len(newDirtyChunks))
                log.info(progressInfo)

#                propagate light!
#                for each of the six cardinal directions, figure a new light value for
#                adjoining blocks by reducing this chunk's light by light absorption and fall off.
#                compare this new light value against the old light value and update with the maximum.
#
#                we calculate all chunks one step before moving to the next step, to ensure all gaps at chunk edges are filled.
#                we do an extra cycle because lights sent across edges may lag by one cycle.
#
#                xxx this can be optimized by finding the highest and lowest blocks
#                that changed after one pass, and only calculating changes for that
#                vertical slice on the next pass. newDirtyChunks would have to be a
#                list of (cPos, miny, maxy) tuples or a cPos : (miny, maxy) dict

                newDirtyChunks = set(newDirtyChunks)
                newDirtyChunks.discard(zeroChunk)

                dirtyChunks = sorted(newDirtyChunks, key=lambda x: x.chunkPosition)

                newDirtyChunks = list()

                for chunk in dirtyChunks:
                    (cx, cz) = chunk.chunkPosition
                    neighboringChunks = {}

                    for dir, dx, dz in ((FaceXDecreasing, -1, 0),
                                        (FaceXIncreasing, 1, 0),
                                        (FaceZDecreasing, 0, -1),
                                        (FaceZIncreasing, 0, 1)):
                        try:
                            neighboringChunks[dir] = self.getChunk(cx + dx, cz + dz)
                        except (ChunkNotPresent, ChunkMalformed):
                            neighboringChunks[dir] = zeroChunk
                        neighboringChunks[dir].dirty = True

                    chunkLa = la[chunk.Blocks]
                    chunkLight = getattr(chunk, light)
                    oldChunk[:] = chunkLight[:]

                    ### Spread light toward -X

                    nc = neighboringChunks[FaceXDecreasing]
                    ncLight = getattr(nc, light)
                    oldLeftEdge[:] = ncLight[15:16, :, 0:self.Height]  # save the old left edge

                    # left edge
                    newlight = (chunkLight[0:1, :, :self.Height] - la[nc.Blocks[15:16, :, 0:self.Height]])
                    clipLight(newlight)

                    maximum(ncLight[15:16, :, 0:self.Height], newlight, ncLight[15:16, :, 0:self.Height])

                    # chunk body
                    newlight = (chunkLight[1:16, :, 0:self.Height] - chunkLa[0:15, :, 0:self.Height])
                    clipLight(newlight)

                    maximum(chunkLight[0:15, :, 0:self.Height], newlight, chunkLight[0:15, :, 0:self.Height])

                    # right edge
                    nc = neighboringChunks[FaceXIncreasing]
                    ncLight = getattr(nc, light)

                    newlight = ncLight[0:1, :, :self.Height] - chunkLa[15:16, :, 0:self.Height]
                    clipLight(newlight)

                    maximum(chunkLight[15:16, :, 0:self.Height], newlight, chunkLight[15:16, :, 0:self.Height])

                    ### Spread light toward +X

                    # right edge
                    nc = neighboringChunks[FaceXIncreasing]
                    ncLight = getattr(nc, light)

                    newlight = (chunkLight[15:16, :, 0:self.Height] - la[nc.Blocks[0:1, :, 0:self.Height]])
                    clipLight(newlight)

                    maximum(ncLight[0:1, :, 0:self.Height], newlight, ncLight[0:1, :, 0:self.Height])

                    # chunk body
                    newlight = (chunkLight[0:15, :, 0:self.Height] - chunkLa[1:16, :, 0:self.Height])
                    clipLight(newlight)

                    maximum(chunkLight[1:16, :, 0:self.Height], newlight, chunkLight[1:16, :, 0:self.Height])

                    # left edge
                    nc = neighboringChunks[FaceXDecreasing]
                    ncLight = getattr(nc, light)

                    newlight = ncLight[15:16, :, :self.Height] - chunkLa[0:1, :, 0:self.Height]
                    clipLight(newlight)

                    maximum(chunkLight[0:1, :, 0:self.Height], newlight, chunkLight[0:1, :, 0:self.Height])

                    zerochunkLight[:] = 0  # zero the zero chunk after each direction
                    # so the lights it absorbed don't affect the next pass

                    # check if the left edge changed and dirty or compress the chunk appropriately
                    if (oldLeftEdge != ncLight[15:16, :, :self.Height]).any():
                        # chunk is dirty
                        newDirtyChunks.append(nc)

                    ### Spread light toward -Z

                    # bottom edge
                    nc = neighboringChunks[FaceZDecreasing]
                    ncLight = getattr(nc, light)
                    oldBottomEdge[:] = ncLight[:, 15:16, :self.Height]  # save the old bottom edge

                    newlight = (chunkLight[:, 0:1, :self.Height] - la[nc.Blocks[:, 15:16, :self.Height]])
                    clipLight(newlight)

                    maximum(ncLight[:, 15:16, :self.Height], newlight, ncLight[:, 15:16, :self.Height])

                    # chunk body
                    newlight = (chunkLight[:, 1:16, :self.Height] - chunkLa[:, 0:15, :self.Height])
                    clipLight(newlight)

                    maximum(chunkLight[:, 0:15, :self.Height], newlight, chunkLight[:, 0:15, :self.Height])

                    # top edge
                    nc = neighboringChunks[FaceZIncreasing]
                    ncLight = getattr(nc, light)

                    newlight = ncLight[:, 0:1, :self.Height] - chunkLa[:, 15:16, 0:self.Height]
                    clipLight(newlight)

                    maximum(chunkLight[:, 15:16, 0:self.Height], newlight, chunkLight[:, 15:16, 0:self.Height])

                    ### Spread light toward +Z

                    # top edge
                    nc = neighboringChunks[FaceZIncreasing]

                    ncLight = getattr(nc, light)

                    newlight = (chunkLight[:, 15:16, :self.Height] - la[nc.Blocks[:, 0:1, :self.Height]])
                    clipLight(newlight)

                    maximum(ncLight[:, 0:1, :self.Height], newlight, ncLight[:, 0:1, :self.Height])

                    # chunk body
                    newlight = (chunkLight[:, 0:15, :self.Height] - chunkLa[:, 1:16, :self.Height])
                    clipLight(newlight)

                    maximum(chunkLight[:, 1:16, :self.Height], newlight, chunkLight[:, 1:16, :self.Height])

                    # bottom edge
                    nc = neighboringChunks[FaceZDecreasing]
                    ncLight = getattr(nc, light)

                    newlight = ncLight[:, 15:16, :self.Height] - chunkLa[:, 0:1, 0:self.Height]
                    clipLight(newlight)

                    maximum(chunkLight[:, 0:1, 0:self.Height], newlight, chunkLight[:, 0:1, 0:self.Height])

                    zerochunkLight[:] = 0

                    if (oldBottomEdge != ncLight[:, 15:16, :self.Height]).any():
                        newDirtyChunks.append(nc)

                    newlight = (chunkLight[:, :, 0:self.Height - 1] - chunkLa[:, :, 1:self.Height])
                    clipLight(newlight)
                    maximum(chunkLight[:, :, 1:self.Height], newlight, chunkLight[:, :, 1:self.Height])

                    newlight = (chunkLight[:, :, 1:self.Height] - chunkLa[:, :, 0:self.Height - 1])
                    clipLight(newlight)
                    maximum(chunkLight[:, :, 0:self.Height - 1], newlight, chunkLight[:, :, 0:self.Height - 1])

                    if (oldChunk != chunkLight).any():
                        newDirtyChunks.append(chunk)

                    work += 1
                    yield workDone + work, workTotal, progressInfo

                workDone += work
                workTotal -= len(startingDirtyChunks)
                workTotal += work

                work = 0

        for ch in startingDirtyChunks:
            ch.needsLighting = False


def TagProperty(tagName, tagType, default_or_func=None):
    def getter(self):
        if tagName not in self.root_tag["Data"]:
            if hasattr(default_or_func, "__call__"):
                default = default_or_func(self)
            else:
                default = default_or_func

            self.root_tag["Data"][tagName] = tagType(default)
        return self.root_tag["Data"][tagName].value

    def setter(self, val):
        self.root_tag["Data"][tagName] = tagType(value=val)

    return property(getter, setter)

class AnvilWorldFolder(object):
    def __init__(self, filename):
        if not os.path.exists(filename):
            os.mkdir(filename)

        elif not os.path.isdir(filename):
            raise IOError, "AnvilWorldFolder: Not a folder: %s" % filename

        self.filename = filename
        self.regionFiles = {}

    # --- File paths ---

    def getFilePath(self, path):
        path = path.replace("/", os.path.sep)
        return os.path.join(self.filename, path)

    def getFolderPath(self, path):
        path = self.getFilePath(path)
        if not os.path.exists(path):
            os.makedirs(path)

        return path

    # --- Region files ---

    def getRegionFilename(self, rx, rz):
        return os.path.join(self.getFolderPath("region"), "r.%s.%s.%s" % (rx, rz, "mca"))

    def getRegionFile(self, rx, rz):
        regionFile = self.regionFiles.get((rx, rz))
        if regionFile:
            return regionFile
        regionFile = MCRegionFile(self.getRegionFilename(rx, rz), (rx, rz))
        self.regionFiles[rx, rz] = regionFile
        return regionFile

    def getRegionForChunk(self, cx, cz):
        rx = cx >> 5
        rz = cz >> 5
        return self.getRegionFile(rx, rz)

    def closeRegions(self):
        for rf in self.regionFiles.values():
            rf.close()

        self.regionFiles = {}

    # --- Chunks and chunk listing ---

    def tryLoadRegionFile(self, filepath):
        filename = os.path.basename(filepath)
        bits = filename.split('.')
        if len(bits) < 4 or bits[0] != 'r' or bits[3] != "mca":
            return None

        try:
            rx, rz = map(int, bits[1:3])
        except ValueError:
            return None

        return MCRegionFile(filepath, (rx, rz))

    def findRegionFiles(self):
        regionDir = self.getFolderPath("region")

        regionFiles = os.listdir(regionDir)
        for filename in regionFiles:
            yield os.path.join(regionDir, filename)

    def listChunks(self):
        chunks = set()

        for filepath in self.findRegionFiles():
            regionFile = self.tryLoadRegionFile(filepath)
            if regionFile is None:
                continue

            if regionFile.offsets.any():
                rx, rz = regionFile.regionCoords
                self.regionFiles[rx, rz] = regionFile

                for index, offset in enumerate(regionFile.offsets):
                    if offset:
                        cx = index & 0x1f
                        cz = index >> 5

                        cx += rx << 5
                        cz += rz << 5

                        chunks.add((cx, cz))
            else:
                log.info(u"Removing empty region file {0}".format(filepath))
                regionFile.close()
                os.unlink(regionFile.path)

        return chunks

    def containsChunk(self, cx, cz):
        rx = cx >> 5
        rz = cz >> 5
        if not os.path.exists(self.getRegionFilename(rx, rz)):
            return False

        return self.getRegionForChunk(cx, cz).containsChunk(cx, cz)

    def deleteChunk(self, cx, cz):
        r = cx >> 5, cz >> 5
        rf = self.getRegionFile(*r)
        if rf:
            rf.setOffset(cx & 0x1f, cz & 0x1f, 0)
            if (rf.offsets == 0).all():
                rf.close()
                os.unlink(rf.path)
                del self.regionFiles[r]

    def readChunk(self, cx, cz):
        if not self.containsChunk(cx, cz):
            raise ChunkNotPresent((cx, cz))

        return self.getRegionForChunk(cx, cz).readChunk(cx, cz)

    def saveChunk(self, cx, cz, data):
        regionFile = self.getRegionForChunk(cx, cz)
        regionFile.saveChunk(cx, cz, data)

    def copyChunkFrom(self, worldFolder, cx, cz):
        fromRF = worldFolder.getRegionForChunk(cx, cz)
        rf = self.getRegionForChunk(cx, cz)
        rf.copyChunkFrom(fromRF, cx, cz)

class MCInfdevOldLevel(ChunkedLevelMixin, EntityLevel):

    def __init__(self, filename=None, create=False, random_seed=None, last_played=None, readonly=False):
        """
        Load an Alpha level from the given filename. It can point to either
        a level.dat or a folder containing one. If create is True, it will
        also create the world using the random_seed and last_played arguments.
        If they are none, a random 64-bit seed will be selected for RandomSeed
        and long(time.time() * 1000) will be used for LastPlayed.

        If you try to create an existing world, its level.dat will be replaced.
        """

        self.Length = 0
        self.Width = 0
        self.Height = 256

        self.playerTagCache = {}
        self.players = []
        assert not (create and readonly)

        if os.path.basename(filename) in ("level.dat", "level.dat_old"):
            filename = os.path.dirname(filename)

        if not os.path.exists(filename):
            if not create:
                raise IOError('File not found')

            os.mkdir(filename)

        if not os.path.isdir(filename):
            raise IOError('File is not a Minecraft Alpha world')


        self.worldFolder = AnvilWorldFolder(filename)
        self.filename = self.worldFolder.getFilePath("level.dat")
        self.readonly = readonly
        if not readonly:
            self.acquireSessionLock()

            workFolderPath = self.worldFolder.getFolderPath("##MCEDIT.TEMP##")
            if os.path.exists(workFolderPath):
                # xxxxxxx Opening a world a second time deletes the first world's work folder and crashes when the first
                # world tries to read a modified chunk from the work folder. This mainly happens when importing a world
                # into itself after modifying it.
                shutil.rmtree(workFolderPath, True)

            self.unsavedWorkFolder = AnvilWorldFolder(workFolderPath)

        # maps (cx, cz) pairs to AnvilChunk
        self._loadedChunks = weakref.WeakValueDictionary()

        # maps (cx, cz) pairs to AnvilChunkData
        self._loadedChunkData = {}

        self.chunksNeedingLighting = set()
        self._allChunks = None
        self.dimensions = {}

        self.loadLevelDat(create, random_seed, last_played)

        assert self.version == self.VERSION_ANVIL, "Pre-Anvil world formats are not supported (for now)"


        self.playersFolder = self.worldFolder.getFolderPath("players")
        self.players = [x[:-4] for x in os.listdir(self.playersFolder) if x.endswith(".dat")]
        if "Player" in self.root_tag["Data"]:
            self.players.append("Player")

        self.preloadDimensions()

    # --- Load, save, create ---

    def _create(self, filename, random_seed, last_played):

        # create a new level
        root_tag = nbt.TAG_Compound()
        root_tag["Data"] = nbt.TAG_Compound()
        root_tag["Data"]["SpawnX"] = nbt.TAG_Int(0)
        root_tag["Data"]["SpawnY"] = nbt.TAG_Int(2)
        root_tag["Data"]["SpawnZ"] = nbt.TAG_Int(0)

        if last_played is None:
            last_played = long(time.time() * 1000)
        if random_seed is None:
            random_seed = long(random.random() * 0xffffffffffffffffL) - 0x8000000000000000L

        self.root_tag = root_tag
        root_tag["Data"]['version'] = nbt.TAG_Int(self.VERSION_ANVIL)

        self.LastPlayed = long(last_played)
        self.RandomSeed = long(random_seed)
        self.SizeOnDisk = 0
        self.Time = 1
        self.LevelName = os.path.basename(self.worldFolder.filename)

        ### if singleplayer:

        self.createPlayer("Player")

    def acquireSessionLock(self):
        lockfile = self.worldFolder.getFilePath("session.lock")
        self.initTime = int(time.time() * 1000)
        with file(lockfile, "wb") as f:
            f.write(struct.pack(">q", self.initTime))


    def checkSessionLock(self):
        if self.readonly:
            raise SessionLockLost, "World is opened read only."

        lockfile = self.worldFolder.getFilePath("session.lock")
        try:
            (lock, ) = struct.unpack(">q", file(lockfile, "rb").read())
        except struct.error:
            lock = -1
        if lock != self.initTime:
            raise SessionLockLost, "Session lock lost. This world is being accessed from another location."

    def loadLevelDat(self, create=False, random_seed=None, last_played=None):

        if create:
            self._create(self.filename, random_seed, last_played)
            self.saveInPlace()
        else:
            try:
                self.root_tag = nbt.load(self.filename)
            except Exception, e:
                filename_old = self.worldFolder.getFilePath("level.dat_old")
                log.info("Error loading level.dat, trying level.dat_old ({0})".format(e))
                try:
                    self.root_tag = nbt.load(filename_old)
                    log.info("level.dat restored from backup.")
                    self.saveInPlace()
                except Exception, e:
                    traceback.print_exc()
                    print repr(e)
                    log.info("Error loading level.dat_old. Initializing with defaults.")
                    self._create(self.filename, random_seed, last_played)

    def saveInPlace(self):
        if self.readonly:
            raise IOError, "World is opened read only."

        self.checkSessionLock()

        for level in self.dimensions.itervalues():
            level.saveInPlace(True)

        dirtyChunkCount = 0
        for chunk in self._loadedChunkData.itervalues():
            cx, cz = chunk.chunkPosition
            if chunk.dirty:
                data = chunk.savedTagData()
                dirtyChunkCount += 1
                self.worldFolder.saveChunk(cx, cz, data)
                chunk.dirty = False

        for cx, cz in self.unsavedWorkFolder.listChunks():
            if (cx, cz) not in self._loadedChunkData:
                data = self.unsavedWorkFolder.readChunk(cx, cz)
                self.worldFolder.saveChunk(cx, cz, data)
                dirtyChunkCount += 1


        self.unsavedWorkFolder.closeRegions()
        shutil.rmtree(self.unsavedWorkFolder.filename, True)
        os.mkdir(self.unsavedWorkFolder.filename)

        for path, tag in self.playerTagCache.iteritems():
            tag.save(path)

        self.playerTagCache.clear()

        self.root_tag.save(self.filename)
        log.info(u"Saved {0} chunks (dim {1})".format(dirtyChunkCount, self.dimNo))

    def unload(self):
        """
        Unload all chunks and close all open filehandles.
        """
        self.worldFolder.closeRegions()
        if not self.readonly:
            self.unsavedWorkFolder.closeRegions()

        self._allChunks = None
        self._loadedChunks.clear()
        self._loadedChunkData.clear()

    def close(self):
        """
        Unload all chunks and close all open filehandles. Discard any unsaved data.
        """
        self.unload()
        try:
            self.checkSessionLock()
            shutil.rmtree(self.unsavedWorkFolder.filename, True)
        except SessionLockLost:
            pass

    # --- Resource limits ---

    loadedChunkLimit = 400

    # --- Constants ---

    GAMETYPE_SURVIVAL = 0
    GAMETYPE_CREATIVE = 1

    VERSION_MCR = 19132
    VERSION_ANVIL = 19133

    # --- Instance variables  ---

    materials = alphaMaterials
    isInfinite = True
    parentWorld = None
    dimNo = 0
    Height = 256
    _bounds = None

    # --- NBT Tag variables ---

    SizeOnDisk = TagProperty('SizeOnDisk', nbt.TAG_Long, 0)
    RandomSeed = TagProperty('RandomSeed', nbt.TAG_Long, 0)
    Time = TagProperty('Time', nbt.TAG_Long, 0)  # Age of the world in ticks. 20 ticks per second; 24000 ticks per day.
    LastPlayed = TagProperty('LastPlayed', nbt.TAG_Long, lambda self: long(time.time() * 1000))

    LevelName = TagProperty('LevelName', nbt.TAG_String, lambda self: self.displayName)

    MapFeatures = TagProperty('MapFeatures', nbt.TAG_Byte, 1)

    GameType = TagProperty('GameType', nbt.TAG_Int, 0)  # 0 for survival, 1 for creative

    version = TagProperty('version', nbt.TAG_Int, VERSION_ANVIL)

    # --- World info ---

    def __str__(self):
        return "MCInfdevOldLevel(\"%s\")" % os.path.basename(self.worldFolder.filename)

    @property
    def displayName(self):
        # shortname = os.path.basename(self.filename)
        # if shortname == "level.dat":
        shortname = os.path.basename(os.path.dirname(self.filename))

        return shortname

    @property
    def bounds(self):
        if self._bounds is None:
            self._bounds = self.getWorldBounds()
        return self._bounds

    def getWorldBounds(self):
        if self.chunkCount == 0:
            return BoundingBox((0, 0, 0), (0, 0, 0))

        allChunks = array(list(self.allChunks))
        mincx = (allChunks[:, 0]).min()
        maxcx = (allChunks[:, 0]).max()
        mincz = (allChunks[:, 1]).min()
        maxcz = (allChunks[:, 1]).max()

        origin = (mincx << 4, 0, mincz << 4)
        size = ((maxcx - mincx + 1) << 4, self.Height, (maxcz - mincz + 1) << 4)

        return BoundingBox(origin, size)

    @property
    def size(self):
        return self.bounds.size

    # --- Format detection ---

    @classmethod
    def _isLevel(cls, filename):

        if os.path.exists(os.path.join(filename, "chunks.dat")):
            return False  # exclude Pocket Edition folders

        if not os.path.isdir(filename):
            f = os.path.basename(filename)
            if f not in ("level.dat", "level.dat_old"):
                return False
            filename = os.path.dirname(filename)

        files = os.listdir(filename)
        if "level.dat" in files or "level.dat_old" in files:
            return True

        return False

    # --- Dimensions ---

    def preloadDimensions(self):
        worldDirs = os.listdir(self.worldFolder.filename)

        for dirname in worldDirs:
            if dirname.startswith("DIM"):
                try:
                    dimNo = int(dirname[3:])
                    log.info("Found dimension {0}".format(dirname))
                    dim = MCAlphaDimension(self, dimNo)
                    self.dimensions[dimNo] = dim
                except Exception, e:
                    log.error(u"Error loading dimension {0}: {1}".format(dirname, e))

    def getDimension(self, dimNo):
        if self.dimNo != 0:
            return self.parentWorld.getDimension(dimNo)

        if dimNo in self.dimensions:
            return self.dimensions[dimNo]
        dim = MCAlphaDimension(self, dimNo, create=True)
        self.dimensions[dimNo] = dim
        return dim

    # --- Region I/O ---

    def preloadChunkPositions(self):
        log.info(u"Scanning for regions...")
        self._allChunks = self.worldFolder.listChunks()
        if not self.readonly:
            self._allChunks.update(self.unsavedWorkFolder.listChunks())
        self._allChunks.update(self._loadedChunkData.iterkeys())

    def getRegionForChunk(self, cx, cz):
        return self.worldFolder.getRegionFile(cx, cz)

    # --- Chunk I/O ---

    def dirhash(self, n):
        return self.dirhashes[n % 64]

    def _dirhash(self):
        n = self
        n = n % 64
        s = u""
        if n >= 36:
            s += u"1"
            n -= 36
        s += u"0123456789abcdefghijklmnopqrstuvwxyz"[n]

        return s

    dirhashes = [_dirhash(n) for n in range(64)]

    def _oldChunkFilename(self, cx, cz):
        return self.worldFolder.getFilePath("%s/%s/c.%s.%s.dat" % (self.dirhash(cx), self.dirhash(cz), base36(cx), base36(cz)))

    def extractChunksInBox(self, box, parentFolder):
        for cx, cz in box.chunkPositions:
            if self.containsChunk(cx, cz):
                self.extractChunk(cx, cz, parentFolder)

    def extractChunk(self, cx, cz, parentFolder):
        if not os.path.exists(parentFolder):
            os.mkdir(parentFolder)

        chunkFilename = self._oldChunkFilename(cx, cz)
        outputFile = os.path.join(parentFolder, os.path.basename(chunkFilename))

        chunk = self.getChunk(cx, cz)

        chunk.root_tag.save(outputFile)

    @property
    def chunkCount(self):
        """Returns the number of chunks in the level. May initiate a costly
        chunk scan."""
        if self._allChunks is None:
            self.preloadChunkPositions()
        return len(self._allChunks)

    @property
    def allChunks(self):
        """Iterates over (xPos, zPos) tuples, one for each chunk in the level.
        May initiate a costly chunk scan."""
        if self._allChunks is None:
            self.preloadChunkPositions()
        return self._allChunks.__iter__()

    def copyChunkFrom(self, world, cx, cz):
        """
        Copy a chunk from world into the same chunk position in self.
        """
        assert isinstance(world, MCInfdevOldLevel)
        if self.readonly:
            raise IOError, "World is opened read only."
        self.checkSessionLock()

        destChunk = self._loadedChunks.get((cx, cz))
        sourceChunk = world._loadedChunks.get((cx, cz))

        if sourceChunk:
            if destChunk:
                log.debug("Both chunks loaded. Using block copy.")
                # Both chunks loaded. Use block copy.
                self.copyBlocksFrom(world, destChunk.bounds, destChunk.bounds.origin)
                return
            else:
                log.debug("Source chunk loaded. Saving into work folder.")

                # Only source chunk loaded. Discard destination chunk and save source chunk in its place.
                self._loadedChunkData.pop((cx, cz), None)
                self.unsavedWorkFolder.saveChunk(cx, cz, sourceChunk.savedTagData())
                return
        else:
            if destChunk:
                log.debug("Destination chunk loaded. Using block copy.")
                # Only destination chunk loaded. Use block copy.
                self.copyBlocksFrom(world, destChunk.bounds, destChunk.bounds.origin)
            else:
                log.debug("No chunk loaded. Using world folder.copyChunkFrom")
                # Neither chunk loaded. Copy via world folders.
                self._loadedChunkData.pop((cx, cz), None)

                # If the source chunk is dirty, write it to the work folder.
                chunkData = world._loadedChunkData.pop((cx, cz), None)
                if chunkData and chunkData.dirty:
                    data = chunkData.savedTagData()
                    world.unsavedWorkFolder.saveChunk(cx, cz, data)

                if world.unsavedWorkFolder.containsChunk(cx, cz):
                    sourceFolder = world.unsavedWorkFolder
                else:
                    sourceFolder = world.worldFolder

                self.unsavedWorkFolder.copyChunkFrom(sourceFolder, cx, cz)

    def _getChunkBytes(self, cx, cz):
        if not self.readonly and self.unsavedWorkFolder.containsChunk(cx, cz):
            return self.unsavedWorkFolder.readChunk(cx, cz)
        else:
            return self.worldFolder.readChunk(cx, cz)

    def _getChunkData(self, cx, cz):
        chunkData = self._loadedChunkData.get((cx, cz))
        if chunkData is not None: return chunkData

        try:
            data = self._getChunkBytes(cx, cz)
            root_tag = nbt.load(buf=data)
            chunkData = AnvilChunkData(self, (cx, cz), root_tag)
        except (MemoryError, ChunkNotPresent):
            raise
        except Exception, e:
            raise ChunkMalformed, "Chunk {0} had an error: {1!r}".format((cx, cz), e), sys.exc_info()[2]

        if not self.readonly and self.unsavedWorkFolder.containsChunk(cx, cz):
            chunkData.dirty = True

        self._storeLoadedChunkData(chunkData)

        return chunkData

    def _storeLoadedChunkData(self, chunkData):
        if len(self._loadedChunkData) > self.loadedChunkLimit:
            # Try to find a chunk to unload. The chunk must not be in _loadedChunks, which contains only chunks that
            # are in use by another object. If the chunk is dirty, save it to the temporary folder.
            if not self.readonly:
                self.checkSessionLock()
            for (ocx, ocz), oldChunkData in self._loadedChunkData.items():
                if (ocx, ocz) not in self._loadedChunks:
                    if oldChunkData.dirty and not self.readonly:
                        data = oldChunkData.savedTagData()
                        self.unsavedWorkFolder.saveChunk(ocx, ocz, data)

                    del self._loadedChunkData[ocx, ocz]
                    break

        self._loadedChunkData[chunkData.chunkPosition] = chunkData

    def getChunk(self, cx, cz):
        """ read the chunk from disk, load it, and return it."""

        chunk = self._loadedChunks.get((cx, cz))
        if chunk is not None:
            return chunk

        chunkData = self._getChunkData(cx, cz)
        chunk = AnvilChunk(chunkData)

        self._loadedChunks[cx, cz] = chunk
        return chunk

    def markDirtyChunk(self, cx, cz):
        self.getChunk(cx, cz).chunkChanged()

    def markDirtyBox(self, box):
        for cx, cz in box.chunkPositions:
            self.markDirtyChunk(cx, cz)

    def listDirtyChunks(self):
        for cPos, chunkData in self._loadedChunkData.iteritems():
            if chunkData.dirty:
                yield cPos

    # --- HeightMaps ---

    def heightMapAt(self, x, z):
        zc = z >> 4
        xc = x >> 4
        xInChunk = x & 0xf
        zInChunk = z & 0xf

        ch = self.getChunk(xc, zc)

        heightMap = ch.HeightMap

        return heightMap[zInChunk, xInChunk]  # HeightMap indices are backwards

    # --- Entities and TileEntities ---

    def addEntity(self, entityTag):
        assert isinstance(entityTag, nbt.TAG_Compound)
        x, y, z = map(lambda x: int(floor(x)), Entity.pos(entityTag))

        try:
            chunk = self.getChunk(x >> 4, z >> 4)
        except (ChunkNotPresent, ChunkMalformed):
            return None
            # raise Error, can't find a chunk?
        chunk.addEntity(entityTag)
        chunk.dirty = True

    def tileEntityAt(self, x, y, z):
        chunk = self.getChunk(x >> 4, z >> 4)
        return chunk.tileEntityAt(x, y, z)

    def addTileEntity(self, tileEntityTag):
        assert isinstance(tileEntityTag, nbt.TAG_Compound)
        if not 'x' in tileEntityTag:
            return
        x, y, z = TileEntity.pos(tileEntityTag)

        try:
            chunk = self.getChunk(x >> 4, z >> 4)
        except (ChunkNotPresent, ChunkMalformed):
            return
            # raise Error, can't find a chunk?
        chunk.addTileEntity(tileEntityTag)
        chunk.dirty = True

    def getEntitiesInBox(self, box):
        entities = []
        for chunk, slices, point in self.getChunkSlices(box):
            entities += chunk.getEntitiesInBox(box)

        return entities

    def removeEntitiesInBox(self, box):
        count = 0
        for chunk, slices, point in self.getChunkSlices(box):
            count += chunk.removeEntitiesInBox(box)

        log.info("Removed {0} entities".format(count))
        return count

    def removeTileEntitiesInBox(self, box):
        count = 0
        for chunk, slices, point in self.getChunkSlices(box):
            count += chunk.removeTileEntitiesInBox(box)

        log.info("Removed {0} tile entities".format(count))
        return count

    # --- Chunk manipulation ---

    def containsChunk(self, cx, cz):
        if self._allChunks is not None:
            return (cx, cz) in self._allChunks
        if (cx, cz) in self._loadedChunkData:
            return True

        return self.worldFolder.containsChunk(cx, cz)

    def containsPoint(self, x, y, z):
        if y < 0 or y > 127:
            return False
        return self.containsChunk(x >> 4, z >> 4)

    def createChunk(self, cx, cz):
        if self.containsChunk(cx, cz):
            raise ValueError("{0}:Chunk {1} already present!".format(self, (cx, cz)))
        if self._allChunks is not None:
            self._allChunks.add((cx, cz))

        self._storeLoadedChunkData(AnvilChunkData(self, (cx, cz), create=True))
        self._bounds = None

    def createChunks(self, chunks):

        i = 0
        ret = []
        for cx, cz in chunks:
            i += 1
            if not self.containsChunk(cx, cz):
                ret.append((cx, cz))
                self.createChunk(cx, cz)
            assert self.containsChunk(cx, cz), "Just created {0} but it didn't take".format((cx, cz))
            if i % 100 == 0:
                log.info(u"Chunk {0}...".format(i))

        log.info("Created {0} chunks.".format(len(ret)))

        return ret

    def createChunksInBox(self, box):
        log.info(u"Creating {0} chunks in {1}".format((box.maxcx - box.mincx) * (box.maxcz - box.mincz), ((box.mincx, box.mincz), (box.maxcx, box.maxcz))))
        return self.createChunks(box.chunkPositions)

    def deleteChunk(self, cx, cz):
        self.worldFolder.deleteChunk(cx, cz)
        if self._allChunks is not None:
            self._allChunks.discard((cx, cz))

        self._bounds = None


    def deleteChunksInBox(self, box):
        log.info(u"Deleting {0} chunks in {1}".format((box.maxcx - box.mincx) * (box.maxcz - box.mincz), ((box.mincx, box.mincz), (box.maxcx, box.maxcz))))
        i = 0
        ret = []
        for cx, cz in itertools.product(xrange(box.mincx, box.maxcx), xrange(box.mincz, box.maxcz)):
            i += 1
            if self.containsChunk(cx, cz):
                self.deleteChunk(cx, cz)
                ret.append((cx, cz))

            assert not self.containsChunk(cx, cz), "Just deleted {0} but it didn't take".format((cx, cz))

            if i % 100 == 0:
                log.info(u"Chunk {0}...".format(i))

        return ret

    # --- Player and spawn manipulation ---

    def playerSpawnPosition(self, player=None):
        """
        xxx if player is None then it gets the default spawn position for the world
        if player hasn't used a bed then it gets the default spawn position
        """
        dataTag = self.root_tag["Data"]
        if player is None:
            playerSpawnTag = dataTag
        else:
            playerSpawnTag = self.getPlayerTag(player)

        return [playerSpawnTag.get(i, dataTag[i]).value for i in ("SpawnX", "SpawnY", "SpawnZ")]

    def setPlayerSpawnPosition(self, pos, player=None):
        """ xxx if player is None then it sets the default spawn position for the world """
        if player is None:
            playerSpawnTag = self.root_tag["Data"]
        else:
            playerSpawnTag = self.getPlayerTag(player)
        for name, val in zip(("SpawnX", "SpawnY", "SpawnZ"), pos):
            playerSpawnTag[name] = nbt.TAG_Int(val)

    def getPlayerPath(self, player):
        assert player != "Player"
        return os.path.join(self.playersFolder, "%s.dat" % player)

    def getPlayerTag(self, player="Player"):
        if player == "Player":
            if player in self.root_tag["Data"]:
                # single-player world
                return self.root_tag["Data"]["Player"]
            raise PlayerNotFound(player)
        else:
            playerFilePath = self.getPlayerPath(player)
            if os.path.exists(playerFilePath):
                # multiplayer world, found this player
                playerTag = self.playerTagCache.get(playerFilePath)
                if playerTag is None:
                    playerTag = nbt.load(playerFilePath)
                    self.playerTagCache[playerFilePath] = playerTag
                return playerTag
            else:
                raise PlayerNotFound(player)

    def getPlayerDimension(self, player="Player"):
        playerTag = self.getPlayerTag(player)
        if "Dimension" not in playerTag:
            return 0
        return playerTag["Dimension"].value

    def setPlayerDimension(self, d, player="Player"):
        playerTag = self.getPlayerTag(player)
        if "Dimension" not in playerTag:
            playerTag["Dimension"] = nbt.TAG_Int(0)
        playerTag["Dimension"].value = d

    def setPlayerPosition(self, pos, player="Player"):
        posList = nbt.TAG_List([nbt.TAG_Double(p) for p in pos])
        playerTag = self.getPlayerTag(player)

        playerTag["Pos"] = posList

    def getPlayerPosition(self, player="Player"):
        playerTag = self.getPlayerTag(player)
        posList = playerTag["Pos"]

        pos = map(lambda x: x.value, posList)
        return pos

    def setPlayerOrientation(self, yp, player="Player"):
        self.getPlayerTag(player)["Rotation"] = nbt.TAG_List([nbt.TAG_Float(p) for p in yp])

    def getPlayerOrientation(self, player="Player"):
        """ returns (yaw, pitch) """
        yp = map(lambda x: x.value, self.getPlayerTag(player)["Rotation"])
        y, p = yp
        if p == 0:
            p = 0.000000001
        if p == 180.0:
            p -= 0.000000001
        yp = y, p
        return array(yp)

    def setPlayerAbilities(self, gametype, player="Player"):
        playerTag = self.getPlayerTag(player)

        # Check for the Abilities tag.  It will be missing in worlds from before
        # Beta 1.9 Prerelease 5.
        if not 'abilities' in playerTag:
            playerTag['abilities'] = nbt.TAG_Compound()

        # Assumes creative (1) is the only mode with these abilities set,
        # which is true for now.  Future game modes may not hold this to be
        # true, however.
        if gametype == 1:
            playerTag['abilities']['instabuild'] = nbt.TAG_Byte(1)
            playerTag['abilities']['mayfly'] = nbt.TAG_Byte(1)
            playerTag['abilities']['invulnerable'] = nbt.TAG_Byte(1)
        else:
            playerTag['abilities']['flying'] = nbt.TAG_Byte(0)
            playerTag['abilities']['instabuild'] = nbt.TAG_Byte(0)
            playerTag['abilities']['mayfly'] = nbt.TAG_Byte(0)
            playerTag['abilities']['invulnerable'] = nbt.TAG_Byte(0)

    def setPlayerGameType(self, gametype, player="Player"):
        playerTag = self.getPlayerTag(player)
        # This annoyingly works differently between single- and multi-player.
        if player == "Player":
            self.GameType = gametype
            self.setPlayerAbilities(gametype, player)
        else:
            playerTag['playerGameType'] = nbt.TAG_Int(gametype)
            self.setPlayerAbilities(gametype, player)

    def getPlayerGameType(self, player="Player"):
        if player == "Player":
            return self.GameType
        else:
            playerTag = self.getPlayerTag(player)
            return playerTag["playerGameType"].value

    def createPlayer(self, playerName):
        if playerName == "Player":
            playerTag = self.root_tag["Data"].setdefault(playerName, nbt.TAG_Compound())
        else:
            playerTag = nbt.TAG_Compound()

        playerTag['Air'] = nbt.TAG_Short(300)
        playerTag['AttackTime'] = nbt.TAG_Short(0)
        playerTag['DeathTime'] = nbt.TAG_Short(0)
        playerTag['Fire'] = nbt.TAG_Short(-20)
        playerTag['Health'] = nbt.TAG_Short(20)
        playerTag['HurtTime'] = nbt.TAG_Short(0)
        playerTag['Score'] = nbt.TAG_Int(0)
        playerTag['FallDistance'] = nbt.TAG_Float(0)
        playerTag['OnGround'] = nbt.TAG_Byte(0)

        playerTag["Inventory"] = nbt.TAG_List()

        playerTag['Motion'] = nbt.TAG_List([nbt.TAG_Double(0) for i in range(3)])
        playerTag['Pos'] = nbt.TAG_List([nbt.TAG_Double([0.5, 2.8, 0.5][i]) for i in range(3)])
        playerTag['Rotation'] = nbt.TAG_List([nbt.TAG_Float(0), nbt.TAG_Float(0)])

        if playerName != "Player":
            if self.readonly:
                raise IOError, "World is opened read only."
            self.checkSessionLock()
            playerTag.save(self.getPlayerPath(playerName))


class MCAlphaDimension (MCInfdevOldLevel):
    def __init__(self, parentWorld, dimNo, create=False):
        filename = parentWorld.worldFolder.getFolderPath("DIM" + str(int(dimNo)))

        self.parentWorld = parentWorld
        MCInfdevOldLevel.__init__(self, filename, create)
        self.dimNo = dimNo
        self.filename = parentWorld.filename
        self.players = self.parentWorld.players
        self.playersFolder = self.parentWorld.playersFolder
        self.playerTagCache = self.parentWorld.playerTagCache

    @property
    def root_tag(self):
        return self.parentWorld.root_tag

    def __str__(self):
        return u"MCAlphaDimension({0}, {1})".format(self.parentWorld, self.dimNo)

    def loadLevelDat(self, create=False, random_seed=None, last_played=None):
        pass

    def preloadDimensions(self):
        pass

    def _create(self, *args, **kw):
        pass

    def acquireSessionLock(self):
        pass

    def checkSessionLock(self):
        self.parentWorld.checkSessionLock()

    dimensionNames = {-1: "Nether", 1: "The End"}

    @property
    def displayName(self):
        return u"{0} ({1})".format(self.parentWorld.displayName,
                                   self.dimensionNames.get(self.dimNo, "Dimension %d" % self.dimNo))

    def saveInPlace(self, saveSelf=False):
        """saving the dimension will save the parent world, which will save any
         other dimensions that need saving.  the intent is that all of them can
         stay loaded at once for fast switching """

        if saveSelf:
            MCInfdevOldLevel.saveInPlace(self)
        else:
            self.parentWorld.saveInPlace()

