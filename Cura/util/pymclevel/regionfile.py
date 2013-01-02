import logging
import os
import struct
import zlib

from numpy import fromstring
from mclevelbase import notclosing, RegionMalformed, ChunkNotPresent
import nbt

log = logging.getLogger(__name__)

__author__ = 'Rio'

def deflate(data):
    return zlib.compress(data, 2)

def inflate(data):
    return zlib.decompress(data)


class MCRegionFile(object):
    holdFileOpen = False  # if False, reopens and recloses the file on each access

    @property
    def file(self):
        openfile = lambda: file(self.path, "rb+")
        if MCRegionFile.holdFileOpen:
            if self._file is None:
                self._file = openfile()
            return notclosing(self._file)
        else:
            return openfile()

    def close(self):
        if MCRegionFile.holdFileOpen:
            self._file.close()
            self._file = None

    def __del__(self):
        self.close()

    def __init__(self, path, regionCoords):
        self.path = path
        self.regionCoords = regionCoords
        self._file = None
        if not os.path.exists(path):
            file(path, "w").close()

        with self.file as f:

            filesize = os.path.getsize(path)
            if filesize & 0xfff:
                filesize = (filesize | 0xfff) + 1
                f.truncate(filesize)

            if filesize == 0:
                filesize = self.SECTOR_BYTES * 2
                f.truncate(filesize)

            f.seek(0)
            offsetsData = f.read(self.SECTOR_BYTES)
            modTimesData = f.read(self.SECTOR_BYTES)

            self.freeSectors = [True] * (filesize / self.SECTOR_BYTES)
            self.freeSectors[0:2] = False, False

            self.offsets = fromstring(offsetsData, dtype='>u4')
            self.modTimes = fromstring(modTimesData, dtype='>u4')

        needsRepair = False

        for offset in self.offsets:
            sector = offset >> 8
            count = offset & 0xff

            for i in xrange(sector, sector + count):
                if i >= len(self.freeSectors):
                    # raise RegionMalformed("Region file offset table points to sector {0} (past the end of the file)".format(i))
                    print  "Region file offset table points to sector {0} (past the end of the file)".format(i)
                    needsRepair = True
                    break
                if self.freeSectors[i] is False:
                    needsRepair = True
                self.freeSectors[i] = False

        if needsRepair:
            self.repair()

        log.info("Found region file {file} with {used}/{total} sectors used and {chunks} chunks present".format(
             file=os.path.basename(path), used=self.usedSectors, total=self.sectorCount, chunks=self.chunkCount))

    def __repr__(self):
        return "%s(\"%s\")" % (self.__class__.__name__, self.path)
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
        lostAndFound = {}
        _freeSectors = [True] * len(self.freeSectors)
        _freeSectors[0] = _freeSectors[1] = False
        deleted = 0
        recovered = 0
        log.info("Beginning repairs on {file} ({chunks} chunks)".format(file=os.path.basename(self.path), chunks=sum(self.offsets > 0)))
        rx, rz = self.regionCoords
        for index, offset in enumerate(self.offsets):
            if offset:
                cx = index & 0x1f
                cz = index >> 5
                cx += rx << 5
                cz += rz << 5
                sectorStart = offset >> 8
                sectorCount = offset & 0xff
                try:

                    if sectorStart + sectorCount > len(self.freeSectors):
                        raise RegionMalformed("Offset {start}:{end} ({offset}) at index {index} pointed outside of the file".format(
                            start=sectorStart, end=sectorStart + sectorCount, index=index, offset=offset))

                    data = self.readChunk(cx, cz)
                    if data is None:
                        raise RegionMalformed("Failed to read chunk data for {0}".format((cx, cz)))

                    chunkTag = nbt.load(buf=data)
                    lev = chunkTag["Level"]
                    xPos = lev["xPos"].value
                    zPos = lev["zPos"].value
                    overlaps = False

                    for i in xrange(sectorStart, sectorStart + sectorCount):
                        if _freeSectors[i] is False:
                            overlaps = True
                        _freeSectors[i] = False

                    if xPos != cx or zPos != cz or overlaps:
                        lostAndFound[xPos, zPos] = data

                        if (xPos, zPos) != (cx, cz):
                            raise RegionMalformed("Chunk {found} was found in the slot reserved for {expected}".format(found=(xPos, zPos), expected=(cx, cz)))
                        else:
                            raise RegionMalformed("Chunk {found} (in slot {expected}) has overlapping sectors with another chunk!".format(found=(xPos, zPos), expected=(cx, cz)))

                except Exception, e:
                    log.info("Unexpected chunk data at sector {sector} ({exc})".format(sector=sectorStart, exc=e))
                    self.setOffset(cx, cz, 0)
                    deleted += 1

        for cPos, (format, foundData) in lostAndFound.iteritems():
            cx, cz = cPos
            if self.getOffset(cx, cz) == 0:
                log.info("Found chunk {found} and its slot is empty, recovering it".format(found=cPos))
                self.saveChunk(cx, cz, foundData[5:])
                recovered += 1

        log.info("Repair complete. Removed {0} chunks, recovered {1} chunks, net {2}".format(deleted, recovered, recovered - deleted))


    def _readChunk(self, cx, cz):
        cx &= 0x1f
        cz &= 0x1f
        offset = self.getOffset(cx, cz)
        if offset == 0:
            raise ChunkNotPresent((cx, cz))

        sectorStart = offset >> 8
        numSectors = offset & 0xff
        if numSectors == 0:
            raise ChunkNotPresent((cx, cz))

        if sectorStart + numSectors > len(self.freeSectors):
            raise ChunkNotPresent((cx, cz))

        with self.file as f:
            f.seek(sectorStart * self.SECTOR_BYTES)
            data = f.read(numSectors * self.SECTOR_BYTES)
        if len(data) < 5:
            raise RegionMalformed, "Chunk data is only %d bytes long (expected 5)" % len(data)

        # log.debug("REGION LOAD {0},{1} sector {2}".format(cx, cz, sectorStart))

        length = struct.unpack_from(">I", data)[0]
        format = struct.unpack_from("B", data, 4)[0]
        data = data[5:length + 5]
        return data, format

    def readChunk(self, cx, cz):
        data, format = self._readChunk(cx, cz)
        if format == self.VERSION_GZIP:
            return nbt.gunzip(data)
        if format == self.VERSION_DEFLATE:
            return inflate(data)

        raise IOError("Unknown compress format: {0}".format(format))

    def copyChunkFrom(self, regionFile, cx, cz):
        """
        Silently fails if regionFile does not contain the requested chunk.
        """
        try:
            data, format = regionFile._readChunk(cx, cz)
            self._saveChunk(cx, cz, data, format)
        except ChunkNotPresent:
            pass

    def saveChunk(self, cx, cz, uncompressedData):
        data = deflate(uncompressedData)
        self._saveChunk(cx, cz, data, self.VERSION_DEFLATE)

    def _saveChunk(self, cx, cz, data, format):
        cx &= 0x1f
        cz &= 0x1f
        offset = self.getOffset(cx, cz)
        sectorNumber = offset >> 8
        sectorsAllocated = offset & 0xff



        sectorsNeeded = (len(data) + self.CHUNK_HEADER_SIZE) / self.SECTOR_BYTES + 1
        if sectorsNeeded >= 256:
            return

        if sectorNumber != 0 and sectorsAllocated >= sectorsNeeded:
            log.debug("REGION SAVE {0},{1} rewriting {2}b".format(cx, cz, len(data)))
            self.writeSector(sectorNumber, data, format)
        else:
            # we need to allocate new sectors

            # mark the sectors previously used for this chunk as free
            for i in xrange(sectorNumber, sectorNumber + sectorsAllocated):
                self.freeSectors[i] = True

            runLength = 0
            runStart = 0
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
                log.debug("REGION SAVE {0},{1}, reusing {2}b".format(cx, cz, len(data)))
                sectorNumber = runStart
                self.setOffset(cx, cz, sectorNumber << 8 | sectorsNeeded)
                self.writeSector(sectorNumber, data, format)
                self.freeSectors[sectorNumber:sectorNumber + sectorsNeeded] = [False] * sectorsNeeded

            else:
                # no free space large enough found -- we need to grow the
                # file

                log.debug("REGION SAVE {0},{1}, growing by {2}b".format(cx, cz, len(data)))

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
            log.debug("REGION: Writing sector {0}".format(sectorNumber))

            f.seek(sectorNumber * self.SECTOR_BYTES)
            f.write(struct.pack(">I", len(data) + 1))  # // chunk length
            f.write(struct.pack("B", format))  # // chunk version number
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

    SECTOR_BYTES = 4096
    SECTOR_INTS = SECTOR_BYTES / 4
    CHUNK_HEADER_SIZE = 5
    VERSION_GZIP = 1
    VERSION_DEFLATE = 2

    compressMode = VERSION_DEFLATE
