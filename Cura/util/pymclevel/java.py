'''
Created on Jul 22, 2011

@author: Rio
'''

__all__ = ["MCJavaLevel"]

from cStringIO import StringIO
import gzip
from level import MCLevel
from logging import getLogger
from numpy import fromstring
import os
import re

log = getLogger(__name__)

class MCJavaLevel(MCLevel):
    def setBlockDataAt(self, *args):
        pass

    def blockDataAt(self, *args):
        return 0

    @property
    def Height(self):
        return self.Blocks.shape[2]

    @property
    def Length(self):
        return self.Blocks.shape[1]

    @property
    def Width(self):
        return self.Blocks.shape[0]

    def guessSize(self, data):
        Width = 64
        Length = 64
        Height = 64
        if data.shape[0] <= (32 * 32 * 64) * 2:
            log.warn(u"Can't guess the size of a {0} byte level".format(data.shape[0]))
            raise IOError("MCJavaLevel attempted for smaller than 64 blocks cubed")
        if data.shape[0] > (64 * 64 * 64) * 2:
            Width = 128
            Length = 128
            Height = 64
        if data.shape[0] > (128 * 128 * 64) * 2:
            Width = 256
            Length = 256
            Height = 64
        if data.shape[0] > (256 * 256 * 64) * 2:  # could also be 256*256*256
            Width = 512
            Length = 512
            Height = 64
        if data.shape[0] > 512 * 512 * 64 * 2:  # just to load shadowmarch castle
            Width = 512
            Length = 512
            Height = 256
        return Width, Length, Height

    @classmethod
    def _isDataLevel(cls, data):
        return (data[0] == 0x27 and
                data[1] == 0x1B and
                data[2] == 0xb7 and
                data[3] == 0x88)

    def __init__(self, filename, data):
        self.filename = filename
        if isinstance(data, basestring):
            data = fromstring(data, dtype='uint8')
        self.filedata = data

        # try to take x,z,y from the filename
        r = re.findall("\d+", os.path.basename(filename))
        if r and len(r) >= 3:
            (w, l, h) = map(int, r[-3:])
            if w * l * h > data.shape[0]:
                log.info("Not enough blocks for size " + str((w, l, h)))
                w, l, h = self.guessSize(data)
        else:
            w, l, h = self.guessSize(data)

        log.info(u"MCJavaLevel created for potential level of size " + str((w, l, h)))

        blockCount = h * l * w
        if blockCount > data.shape[0]:
            raise ValueError("Level file does not contain enough blocks! (size {s}) Try putting the size into the filename, e.g. server_level_{w}_{l}_{h}.dat".format(w=w, l=l, h=h, s=data.shape))

        blockOffset = data.shape[0] - blockCount
        blocks = data[blockOffset:blockOffset + blockCount]

        maxBlockType = 64  # maximum allowed in classic
        while max(blocks[-4096:]) > maxBlockType:
            # guess the block array by starting at the end of the file
            # and sliding the blockCount-sized window back until it
            # looks like every block has a valid blockNumber
            blockOffset -= 1
            blocks = data[blockOffset:blockOffset + blockCount]

            if blockOffset <= -data.shape[0]:
                raise IOError("Can't find a valid array of blocks <= #%d" % maxBlockType)

        self.Blocks = blocks
        self.blockOffset = blockOffset
        blocks.shape = (w, l, h)
        blocks.strides = (1, w, w * l)

    def saveInPlace(self):

        s = StringIO()
        g = gzip.GzipFile(fileobj=s, mode='wb')


        g.write(self.filedata.tostring())
        g.flush()
        g.close()

        try:
            os.rename(self.filename, self.filename + ".old")
        except Exception, e:
            pass

        try:
            with open(self.filename, 'wb') as f:
                f.write(s.getvalue())
        except Exception, e:
            log.info(u"Error while saving java level in place: {0}".format(e))
            try:
                os.remove(self.filename)
            except:
                pass
            os.rename(self.filename + ".old", self.filename)

        try:
            os.remove(self.filename + ".old")
        except Exception, e:
            pass


class MCSharpLevel(MCLevel):
    """ int magic = convert(data.readShort())
        logger.trace("Magic number: {}", magic)
        if (magic != 1874)
            throw new IOException("Only version 1 MCSharp levels supported (magic number was "+magic+")")

        int width = convert(data.readShort())
        int height = convert(data.readShort())
        int depth = convert(data.readShort())
        logger.trace("Width: {}", width)
        logger.trace("Depth: {}", depth)
        logger.trace("Height: {}", height)

        int spawnX = convert(data.readShort())
        int spawnY = convert(data.readShort())
        int spawnZ = convert(data.readShort())

        int spawnRotation = data.readUnsignedByte()
        int spawnPitch = data.readUnsignedByte()

        int visitRanks = data.readUnsignedByte()
        int buildRanks = data.readUnsignedByte()

        byte[][][] blocks = new byte[width][height][depth]
        int i = 0
        BlockManager manager = BlockManager.getBlockManager()
        for(int z = 0;z<depth;z++) {
            for(int y = 0;y<height;y++) {
                byte[] row = new byte[height]
                data.readFully(row)
                for(int x = 0;x<width;x++) {
                    blocks[x][y][z] = translateBlock(row[x])
                }
            }
        }

        lvl.setBlocks(blocks, new byte[width][height][depth], width, height, depth)
        lvl.setSpawnPosition(new Position(spawnX, spawnY, spawnZ))
        lvl.setSpawnRotation(new Rotation(spawnRotation, spawnPitch))
        lvl.setEnvironment(new Environment())

        return lvl
    }"""
