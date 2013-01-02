from datetime import datetime
import logging
log = logging.getLogger(__name__)

import numpy
from box import BoundingBox, Vector
from mclevelbase import exhaust
import materials
from entity import Entity, TileEntity


def convertBlocks(destLevel, sourceLevel, blocks, blockData):
    return materials.convertBlocks(destLevel.materials, sourceLevel.materials, blocks, blockData)

def sourceMaskFunc(blocksToCopy):
    if blocksToCopy is not None:
        typemask = numpy.zeros(256, dtype='bool')
        typemask[blocksToCopy] = 1

        def maskedSourceMask(sourceBlocks):
            return typemask[sourceBlocks]

        return maskedSourceMask

    def unmaskedSourceMask(_sourceBlocks):
        return slice(None, None)

    return unmaskedSourceMask


def adjustCopyParameters(destLevel, sourceLevel, sourceBox, destinationPoint):
    # if the destination box is outside the level, it and the source corners are moved inward to fit.
    (dx, dy, dz) = map(int, destinationPoint)

    log.debug(u"Asked to copy {} blocks \n\tfrom {} in {}\n\tto {} in {}" .format(
              sourceBox.volume, sourceBox, sourceLevel, destinationPoint, destLevel))
    if destLevel.Width == 0:
        return sourceBox, destinationPoint

    destBox = BoundingBox(destinationPoint, sourceBox.size)
    actualDestBox = destBox.intersect(destLevel.bounds)

    actualSourceBox = BoundingBox(sourceBox.origin + actualDestBox.origin - destBox.origin, destBox.size)
    actualDestPoint = actualDestBox.origin

    return actualSourceBox, actualDestPoint



def copyBlocksFromIter(destLevel, sourceLevel, sourceBox, destinationPoint, blocksToCopy=None, entities=True, create=False):
    """ copy blocks between two infinite levels by looping through the
    destination's chunks. make a sub-box of the source level for each chunk
    and copy block and entities in the sub box to the dest chunk."""

    (lx, ly, lz) = sourceBox.size

    sourceBox, destinationPoint = adjustCopyParameters(destLevel, sourceLevel, sourceBox, destinationPoint)
    # needs work xxx
    log.info(u"Copying {0} blocks from {1} to {2}" .format(ly * lz * lx, sourceBox, destinationPoint))
    startTime = datetime.now()

    destBox = BoundingBox(destinationPoint, sourceBox.size)
    chunkCount = destBox.chunkCount
    i = 0
    e = 0
    t = 0

    sourceMask = sourceMaskFunc(blocksToCopy)

    copyOffset = [d - s for s, d in zip(sourceBox.origin, destinationPoint)]

    # Visit each chunk in the destination area.
    #   Get the region of the source area corresponding to that chunk
    #   Visit each chunk of the region of the source area
    #     Get the slices of the destination chunk
    #     Get the slices of the source chunk
    #     Copy blocks and data

    for destCpos in destBox.chunkPositions:
        cx, cz = destCpos

        destChunkBox = BoundingBox((cx << 4, 0, cz << 4), (16, destLevel.Height, 16)).intersect(destBox)
        destChunkBoxInSourceLevel = BoundingBox([d - o for o, d in zip(copyOffset, destChunkBox.origin)], destChunkBox.size)

        if not destLevel.containsChunk(*destCpos):
            if create and any(sourceLevel.containsChunk(*c) for c in destChunkBoxInSourceLevel.chunkPositions):
                # Only create chunks in the destination level if the source level has chunks covering them.
                destLevel.createChunk(*destCpos)
            else:
                continue

        destChunk = destLevel.getChunk(*destCpos)


        i += 1
        yield (i, chunkCount)
        if i % 100 == 0:
            log.info("Chunk {0}...".format(i))

        for srcCpos in destChunkBoxInSourceLevel.chunkPositions:
            if not sourceLevel.containsChunk(*srcCpos):
                continue

            sourceChunk = sourceLevel.getChunk(*srcCpos)

            sourceChunkBox, sourceSlices = sourceChunk.getChunkSlicesForBox(destChunkBoxInSourceLevel)
            sourceChunkBoxInDestLevel = BoundingBox([d + o for o, d in zip(copyOffset, sourceChunkBox.origin)], sourceChunkBox.size)

            _, destSlices = destChunk.getChunkSlicesForBox(sourceChunkBoxInDestLevel)

            sourceBlocks = sourceChunk.Blocks[sourceSlices]
            sourceData = sourceChunk.Data[sourceSlices]

            mask = sourceMask(sourceBlocks)
            convertedSourceBlocks, convertedSourceData = convertBlocks(destLevel, sourceLevel, sourceBlocks, sourceData)

            destChunk.Blocks[destSlices][mask] = convertedSourceBlocks[mask]
            if convertedSourceData is not None:
                destChunk.Data[destSlices][mask] = convertedSourceData[mask]

            if entities:
                ents = sourceChunk.getEntitiesInBox(destChunkBoxInSourceLevel)
                e += len(ents)
                for entityTag in ents:
                    eTag = Entity.copyWithOffset(entityTag, copyOffset)
                    destLevel.addEntity(eTag)

            tileEntities = sourceChunk.getTileEntitiesInBox(destChunkBoxInSourceLevel)
            t += len(tileEntities)
            for tileEntityTag in tileEntities:
                eTag = TileEntity.copyWithOffset(tileEntityTag, copyOffset)
                destLevel.addTileEntity(eTag)

        destChunk.chunkChanged()

    log.info("Duration: {0}".format(datetime.now() - startTime))
    log.info("Copied {0} entities and {1} tile entities".format(e, t))

def copyBlocksFrom(destLevel, sourceLevel, sourceBox, destinationPoint, blocksToCopy=None, entities=True, create=False):
    return exhaust(copyBlocksFromIter(destLevel, sourceLevel, sourceBox, destinationPoint, blocksToCopy, entities, create))





