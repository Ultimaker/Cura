from level import FakeChunk
import logging
from materials import pocketMaterials
from mclevelbase import ChunkNotPresent, notclosing
from nbt import TAG_List
from numpy import array, fromstring, zeros
import os
import struct

# values are usually little-endian, unlike Minecraft PC

logger = logging.getLogger(__file__)


class PocketChunksFile(object):
    holdFileOpen = False  # if False, reopens and recloses the file on each access
    SECTOR_BYTES = 4096
    CHUNK_HEADER_SIZE = 4

    @property
    def file(self):
        openfile = lambda: file(self.path, "rb+")
        if PocketChunksFile.holdFileOpen:
            if self._file is None:
                self._file = openfile()
            return notclosing(self._file)
        else:
            return openfile()

    def close(self):
        if PocketChunksFile.holdFileOpen:
            self._file.close()
            self._file = None

    def __init__(self, path):
        self.path = path
        self._file = None
        if not os.path.exists(path):
            file(path, "w").close()

        with self.file as f:

            filesize = os.path.getsize(path)
            if filesize & 0xfff:
                filesize = (filesize | 0xfff) + 1
                f.truncate(filesize)

            if filesize == 0:
                filesize = self.SECTOR_BYTES
                f.truncate(filesize)

            f.seek(0)
            offsetsData = f.read(self.SECTOR_BYTES)

            self.freeSectors = [True] * (filesize / self.SECTOR_BYTES)
            self.freeSectors[0] = False

            self.offsets = fromstring(offsetsData, dtype='<u4')

        needsRepair = False

        for index, offset in enumerate(self.offsets):
            sector = offset >> 8
            count = offset & 0xff

            for i in xrange(sector, sector + count):
                if i >= len(self.freeSectors):
                    # raise RegionMalformed("Region file offset table points to sector {0} (past the end of the file)".format(i))
                    print  "Region file offset table points to sector {0} (past the end of the file)".format(i)
                    needsRepair = True
                    break
                if self.freeSectors[i] is False:
                    logger.debug("Double-allocated sector number %s (offset %s @ %s)", i, offset, index)
                    needsRepair = True
                self.freeSectors[i] = False

        if needsRepair:
            self.repair()

        logger.info("Found region file {file} with {used}/{total} sectors used and {chunks} chunks present".format(
             file=os.path.basename(path), used=self.usedSectors, total=self.sectorCount, chunks=self.chunkCount))

    @property
    def usedSectors(self):
        return len(self.freeSectors) - sum(self.freeSectors)

    @property
    def sectorCount(self):
        return len(self.freeSectors)

    @property
    def chunkCount(self):
        return sum(self.offsets > 0)

    def repair(self):
        pass
#        lostAndFound = {}
#        _freeSectors = [True] * len(self.freeSectors)
#        _freeSectors[0] = _freeSectors[1] = False
#        deleted = 0
#        recovered = 0
#        logger.info("Beginning repairs on {file} ({chunks} chunks)".format(file=os.path.basename(self.path), chunks=sum(self.offsets > 0)))
#        rx, rz = self.regionCoords
#        for index, offset in enumerate(self.offsets):
#            if offset:
#                cx = index & 0x1f
#                cz = index >> 5
#                cx += rx << 5
#                cz += rz << 5
#                sectorStart = offset >> 8
#                sectorCount = offset & 0xff
#                try:
#
#                    if sectorStart + sectorCount > len(self.freeSectors):
#                        raise RegionMalformed("Offset {start}:{end} ({offset}) at index {index} pointed outside of the file".format()
#                            start=sectorStart, end=sectorStart + sectorCount, index=index, offset=offset)
#
#                    compressedData = self._readChunk(cx, cz)
#                    if compressedData is None:
#                        raise RegionMalformed("Failed to read chunk data for {0}".format((cx, cz)))
#
#                    format, data = self.decompressSectors(compressedData)
#                    chunkTag = nbt.load(buf=data)
#                    lev = chunkTag["Level"]
#                    xPos = lev["xPos"].value
#                    zPos = lev["zPos"].value
#                    overlaps = False
#
#                    for i in xrange(sectorStart, sectorStart + sectorCount):
#                        if _freeSectors[i] is False:
#                            overlaps = True
#                        _freeSectors[i] = False
#
#
#                    if xPos != cx or zPos != cz or overlaps:
#                        lostAndFound[xPos, zPos] = (format, compressedData)
#
#                        if (xPos, zPos) != (cx, cz):
#                            raise RegionMalformed("Chunk {found} was found in the slot reserved for {expected}".format(found=(xPos, zPos), expected=(cx, cz)))
#                        else:
#                            raise RegionMalformed("Chunk {found} (in slot {expected}) has overlapping sectors with another chunk!".format(found=(xPos, zPos), expected=(cx, cz)))
#
#
#
#                except Exception, e:
#                    logger.info("Unexpected chunk data at sector {sector} ({exc})".format(sector=sectorStart, exc=e))
#                    self.setOffset(cx, cz, 0)
#                    deleted += 1
#
#        for cPos, (format, foundData) in lostAndFound.iteritems():
#            cx, cz = cPos
#            if self.getOffset(cx, cz) == 0:
#                logger.info("Found chunk {found} and its slot is empty, recovering it".format(found=cPos))
#                self._saveChunk(cx, cz, foundData[5:], format)
#                recovered += 1
#
#        logger.info("Repair complete. Removed {0} chunks, recovered {1} chunks, net {2}".format(deleted, recovered, recovered - deleted))
#


    def _readChunk(self, cx, cz):
        cx &= 0x1f
        cz &= 0x1f
        offset = self.getOffset(cx, cz)
        if offset == 0:
            return None

        sectorStart = offset >> 8
        numSectors = offset & 0xff
        if numSectors == 0:
            return None

        if sectorStart + numSectors > len(self.freeSectors):
            return None

        with self.file as f:
            f.seek(sectorStart * self.SECTOR_BYTES)
            data = f.read(numSectors * self.SECTOR_BYTES)
        assert(len(data) > 0)
        logger.debug("REGION LOAD %s,%s sector %s", cx, cz, sectorStart)
        return data

    def loadChunk(self, cx, cz, world):
        data = self._readChunk(cx, cz)
        if data is None:
            raise ChunkNotPresent((cx, cz, self))

        chunk = PocketChunk(cx, cz, data[4:], world)
        return chunk

    def saveChunk(self, chunk):
        cx, cz = chunk.chunkPosition

        cx &= 0x1f
        cz &= 0x1f
        offset = self.getOffset(cx, cz)
        sectorNumber = offset >> 8
        sectorsAllocated = offset & 0xff

        data = chunk._savedData()

        sectorsNeeded = (len(data) + self.CHUNK_HEADER_SIZE) / self.SECTOR_BYTES + 1
        if sectorsNeeded >= 256:
            return

        if sectorNumber != 0 and sectorsAllocated >= sectorsNeeded:
            logger.debug("REGION SAVE {0},{1} rewriting {2}b".format(cx, cz, len(data)))
            self.writeSector(sectorNumber, data, format)
        else:
            # we need to allocate new sectors

            # mark the sectors previously used for this chunk as free
            for i in xrange(sectorNumber, sectorNumber + sectorsAllocated):
                self.freeSectors[i] = True

            runLength = 0
            try:
                runStart = self.freeSectors.index(True)

                for i in range(runStart, len(self.freeSectors)):
                    if runLength:
                        if self.freeSectors[i]:
                            runLength += 1
                        else:
                            runLength = 0
                    elif self.freeSectors[i]:
                        runStart = i
                        runLength = 1

                    if runLength >= sectorsNeeded:
                        break
            except ValueError:
                pass

            # we found a free space large enough
            if runLength >= sectorsNeeded:
                logger.debug("REGION SAVE {0},{1}, reusing {2}b".format(cx, cz, len(data)))
                sectorNumber = runStart
                self.setOffset(cx, cz, sectorNumber << 8 | sectorsNeeded)
                self.writeSector(sectorNumber, data, format)
                self.freeSectors[sectorNumber:sectorNumber + sectorsNeeded] = [False] * sectorsNeeded

            else:
                # no free space large enough found -- we need to grow the
                # file

                logger.debug("REGION SAVE {0},{1}, growing by {2}b".format(cx, cz, len(data)))

                with self.file as f:
                    f.seek(0, 2)
                    filesize = f.tell()

                    sectorNumber = len(self.freeSectors)

                    assert sectorNumber * self.SECTOR_BYTES == filesize

                    filesize += sectorsNeeded * self.SECTOR_BYTES
                    f.truncate(filesize)

                self.freeSectors += [False] * sectorsNeeded

                self.setOffset(cx, cz, sectorNumber << 8 | sectorsNeeded)
                self.writeSector(sectorNumber, data, format)

    def writeSector(self, sectorNumber, data, format):
        with self.file as f:
            logger.debug("REGION: Writing sector {0}".format(sectorNumber))

            f.seek(sectorNumber * self.SECTOR_BYTES)
            f.write(struct.pack("<I", len(data) + self.CHUNK_HEADER_SIZE))  # // chunk length
            f.write(data)  # // chunk data
            # f.flush()

    def containsChunk(self, cx, cz):
        return self.getOffset(cx, cz) != 0

    def getOffset(self, cx, cz):
        cx &= 0x1f
        cz &= 0x1f
        return self.offsets[cx + cz * 32]

    def setOffset(self, cx, cz, offset):
        cx &= 0x1f
        cz &= 0x1f
        self.offsets[cx + cz * 32] = offset
        with self.file as f:
            f.seek(0)
            f.write(self.offsets.tostring())

    def chunkCoords(self):
        indexes = (i for (i, offset) in enumerate(self.offsets) if offset)
        coords = ((i % 32, i // 32) for i in indexes)
        return coords

from infiniteworld import ChunkedLevelMixin
from level import MCLevel, LightedChunk


class PocketWorld(ChunkedLevelMixin, MCLevel):
    Height = 128
    Length = 512
    Width = 512

    isInfinite = True  # Wrong. isInfinite actually means 'isChunked' and should be changed
    materials = pocketMaterials

    @property
    def allChunks(self):
        return list(self.chunkFile.chunkCoords())

    def __init__(self, filename):
        if not os.path.isdir(filename):
            filename = os.path.dirname(filename)
        self.filename = filename
        self.dimensions = {}

        self.chunkFile = PocketChunksFile(os.path.join(filename, "chunks.dat"))
        self._loadedChunks = {}

    def getChunk(self, cx, cz):
        for p in cx, cz:
            if not 0 <= p <= 31:
                raise ChunkNotPresent((cx, cz, self))

        c = self._loadedChunks.get((cx, cz))
        if c is None:
            c = self.chunkFile.loadChunk(cx, cz, self)
            self._loadedChunks[cx, cz] = c
        return c

    @classmethod
    def _isLevel(cls, filename):
        clp = ("chunks.dat", "level.dat")

        if not os.path.isdir(filename):
            f = os.path.basename(filename)
            if f not in clp:
                return False
            filename = os.path.dirname(filename)

        return all([os.path.exists(os.path.join(filename, f)) for f in clp])

    def saveInPlace(self):
        for chunk in self._loadedChunks.itervalues():
            if chunk.dirty:
                self.chunkFile.saveChunk(chunk)
                chunk.dirty = False

    def containsChunk(self, cx, cz):
        if cx > 31 or cz > 31 or cx < 0 or cz < 0:
            return False
        return self.chunkFile.getOffset(cx, cz) != 0

    @property
    def chunksNeedingLighting(self):
        for chunk in self._loadedChunks.itervalues():
            if chunk.needsLighting:
                yield chunk.chunkPosition

class PocketChunk(LightedChunk):
    HeightMap = FakeChunk.HeightMap

    Entities = TileEntities = property(lambda self: TAG_List())

    dirty = False
    filename = "chunks.dat"

    def __init__(self, cx, cz, data, world):
        self.chunkPosition = (cx, cz)
        self.world = world
        data = fromstring(data, dtype='uint8')

        self.Blocks, data = data[:32768], data[32768:]
        self.Data, data = data[:16384], data[16384:]
        self.SkyLight, data = data[:16384], data[16384:]
        self.BlockLight, data = data[:16384], data[16384:]
        self.DirtyColumns = data[:256]

        self.unpackChunkData()
        self.shapeChunkData()


    def unpackChunkData(self):
        for key in ('SkyLight', 'BlockLight', 'Data'):
            dataArray = getattr(self, key)
            dataArray.shape = (16, 16, 64)
            s = dataArray.shape
            # assert s[2] == self.world.Height / 2
            # unpackedData = insert(dataArray[...,newaxis], 0, 0, 3)

            unpackedData = zeros((s[0], s[1], s[2] * 2), dtype='uint8')

            unpackedData[:, :, ::2] = dataArray
            unpackedData[:, :, ::2] &= 0xf
            unpackedData[:, :, 1::2] = dataArray
            unpackedData[:, :, 1::2] >>= 4
            setattr(self, key, unpackedData)

    def shapeChunkData(self):
        chunkSize = 16
        self.Blocks.shape = (chunkSize, chunkSize, self.world.Height)
        self.SkyLight.shape = (chunkSize, chunkSize, self.world.Height)
        self.BlockLight.shape = (chunkSize, chunkSize, self.world.Height)
        self.Data.shape = (chunkSize, chunkSize, self.world.Height)
        self.DirtyColumns.shape = chunkSize, chunkSize

    def _savedData(self):
        def packData(dataArray):
            assert dataArray.shape[2] == self.world.Height

            data = array(dataArray).reshape(16, 16, self.world.Height / 2, 2)
            data[..., 1] <<= 4
            data[..., 1] |= data[..., 0]
            return array(data[:, :, :, 1])

        if self.dirty:
            # elements of DirtyColumns are bitfields. Each bit corresponds to a
            # 16-block segment of the column. We set all of the bits because
            # we only track modifications at the chunk level.
            self.DirtyColumns[:] = 255

        return "".join([self.Blocks.tostring(),
                       packData(self.Data).tostring(),
                       packData(self.SkyLight).tostring(),
                       packData(self.BlockLight).tostring(),
                       self.DirtyColumns.tostring(),
                       ])
