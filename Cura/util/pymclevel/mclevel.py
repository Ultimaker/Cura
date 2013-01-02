# -*- coding: utf-8 -*-
"""
MCLevel interfaces

Sample usage:

import mclevel

# Call mclevel.fromFile to identify and open any of these four file formats:
#
# Classic levels - gzipped serialized java objects.  Returns an instance of MCJavalevel
# Indev levels - gzipped NBT data in a single file.  Returns an MCIndevLevel
# Schematics - gzipped NBT data in a single file.  Returns an MCSchematic.
#   MCSchematics have the special method rotateLeft which will reorient torches, stairs, and other tiles appropriately.
# Alpha levels - world folder structure containing level.dat and chunk folders.  Single or Multiplayer.
#   Can accept a path to the world folder or a path to the level.dat.  Returns an MCInfdevOldLevel

# Load a Classic level.
level = mclevel.fromFile("server_level.dat");

# fromFile identified the file type and returned a MCJavaLevel.  MCJavaLevel doesn't actually know any java. It guessed the
# location of the Blocks array by starting at the end of the file and moving backwards until it only finds valid blocks.
# It also doesn't know the dimensions of the level.  This is why you have to tell them to MCEdit via the filename.
# This works here too:  If the file were 512 wide, 512 long, and 128 high, I'd have to name it "server_level_512_512_128.dat"
#
# This is one area for improvement.

# Classic and Indev levels have all of their blocks in one place.
blocks = level.Blocks

# Sand to glass.
blocks[blocks == level.materials.Sand.ID] = level.materials.Glass.ID

# Save the file with another name.  This only works for non-Alpha levels.
level.saveToFile("server_level_glassy.dat");

# Load an Alpha world
# Loading an Alpha world immediately scans the folder for chunk files.  This takes longer for large worlds.
ourworld = mclevel.fromFile("C:\\Minecraft\\OurWorld");

# Convenience method to load a numbered world from the saves folder.
world1 = mclevel.loadWorldNumber(1);

# Find out which chunks are present. Doing this will scan the chunk folders the
# first time it is used. If you already know where you want to be, skip to
# world1.getChunk(xPos, zPos)

chunkPositions = list(world1.allChunks)

# allChunks returns an iterator that yields a (xPos, zPos) tuple for each chunk
xPos, zPos = chunkPositions[0];

# retrieve an AnvilChunk object. this object will load and decompress
# the chunk as needed, and remember whether it needs to be saved or relighted

chunk = world1.getChunk(xPos, zPos)

### Access the data arrays of the chunk like so:
# Take note that the array is indexed x, z, y.  The last index corresponds to
# height or altitude.

blockType = chunk.Blocks[0,0,64]
chunk.Blocks[0,0,64] = 1

# Access the chunk's Entities and TileEntities as arrays of TAG_Compound as
# they appear in the save format.

# Entities usually have Pos, Health, and id
# TileEntities usually have tileX, tileY, tileZ, and id
# For more information, google "Chunk File Format"

for entity in chunk.Entities:
    if entity["id"].value == "Spider":
        entity["Health"].value = 50


# Accessing one byte at a time from the Blocks array is very slow in Python.
# To get around this, we have methods to access multiple bytes at once.
# The first technique is slicing. You can use slicing to restrict your access
# to certain depth levels, or to extract a column or a larger section from the
# array. Standard python slice notation is used.

# Set the top half of the array to 0. The : says to use the entire array along
# that dimension. The syntax []= indicates we are overwriting part of the array
chunk.Blocks[:,:,64:] = 0

# Using [] without =  creates a 'view' on part of the array.  This is not a
# copy, it is a reference to a portion of the original array.
midBlocks = chunk.Blocks[:,:,32:64]

# Here's a gotcha:  You can't just write 'midBlocks = 0' since it will replace
# the 'midBlocks' reference itself instead of accessing the array. Instead, do
# this to access and overwrite the array using []= syntax.
midBlocks[:] = 0


# The second is masking.  Using a comparison operator ( <, >, ==, etc )
# against the Blocks array will return a 'mask' that we can use to specify
# positions in the array.

# Create the mask from the result of the equality test.
fireBlocks = ( chunk.Blocks==world.materials.Fire.ID )

# Access Blocks using the mask to set elements. The syntax is the same as
# using []= with slices
chunk.Blocks[fireBlocks] = world.materials.Leaves.ID

# You can also combine mask arrays using logical operations (&, |, ^) and use
# the mask to access any other array of the same shape.
# Here we turn all trees into birch trees.

# Extract a mask from the Blocks array to find the locations of tree trunks.
# Or | it with another mask to find the locations of leaves.
# Use the combined mask to access the Data array and set those locations to birch

# Note that the Data, BlockLight, and SkyLight arrays have been
# unpacked from 4-bit arrays to numpy uint8 arrays. This makes them much easier
# to work with.

treeBlocks = ( chunk.Blocks == world.materials.Wood.ID )
treeBlocks |= ( chunk.Blocks == world.materials.Leaves.ID )
chunk.Data[treeBlocks] = 2 # birch


# The chunk doesn't know you've changed any of that data.  Call chunkChanged()
# to let it know. This will mark the chunk for lighting calculation,
# recompression, and writing to disk. It will also immediately recalculate the
# chunk's HeightMap and fill the SkyLight only with light falling straight down.
# These are relatively fast and were added here to aid MCEdit.

chunk.chunkChanged();

# To recalculate all of the dirty lights in the world, call generateLights
world.generateLights();


# Move the player and his spawn
world.setPlayerPosition( (0, 67, 0) ) # add 3 to make sure his head isn't in the ground.
world.setPlayerSpawnPosition( (0, 64, 0) )


# Save the level.dat and any chunks that have been marked for writing to disk
# This also compresses any chunks marked for recompression.
world.saveInPlace();


# Advanced use:
# The getChunkSlices method returns an iterator that returns slices of chunks within the specified range.
# the slices are returned as tuples of (chunk, slices, point)

# chunk:  The AnvilChunk object we're interested in.
# slices:  A 3-tuple of slice objects that can be used to index chunk's data arrays
# point:  A 3-tuple of floats representing the relative position of this subslice within the larger slice.
#
# Take caution:
# the point tuple is ordered (x,y,z) in accordance with the tuples used to initialize a bounding box
# however, the slices tuple is ordered (x,z,y) for easy indexing into the arrays.

# Here is an old version of MCInfdevOldLevel.fillBlocks in its entirety:

def fillBlocks(self, box, blockType, blockData = 0):
    chunkIterator = self.getChunkSlices(box)

    for (chunk, slices, point) in chunkIterator:
        chunk.Blocks[slices] = blockType
        chunk.Data[slices] = blockData
        chunk.chunkChanged();


Copyright 2010 David Rio Vierra
"""

from indev import MCIndevLevel
from infiniteworld import MCInfdevOldLevel
from java import MCJavaLevel
from logging import getLogger
from mclevelbase import saveFileDir
import nbt
from numpy import fromstring
import os
from pocket import PocketWorld
from schematic import INVEditChest, MCSchematic, ZipSchematic
import sys
import traceback

log = getLogger(__name__)

class LoadingError(RuntimeError):
    pass


def fromFile(filename, loadInfinite=True, readonly=True):
    ''' The preferred method for loading Minecraft levels of any type.
    pass False to loadInfinite if you'd rather not load infdev levels.
    '''
    log.info(u"Identifying " + filename)

    if not filename:
        raise IOError("File not found: " + filename)
    if not os.path.exists(filename):
        raise IOError("File not found: " + filename)

    if ZipSchematic._isLevel(filename):
        log.info("Zipfile found, attempting zipped infinite level")
        lev = ZipSchematic(filename)
        log.info("Detected zipped Infdev level")
        return lev

    if PocketWorld._isLevel(filename):
        return PocketWorld(filename)

    if MCInfdevOldLevel._isLevel(filename):
        log.info(u"Detected Infdev level.dat")
        if loadInfinite:
            return MCInfdevOldLevel(filename=filename, readonly=readonly)
        else:
            raise ValueError("Asked to load {0} which is an infinite level, loadInfinite was False".format(os.path.basename(filename)))

    if os.path.isdir(filename):
        raise ValueError("Folder {0} was not identified as a Minecraft level.".format(os.path.basename(filename)))

    f = file(filename, 'rb')
    rawdata = f.read()
    f.close()
    if len(rawdata) < 4:
        raise ValueError("{0} is too small! ({1}) ".format(filename, len(rawdata)))

    data = fromstring(rawdata, dtype='uint8')
    if not data.any():
        raise ValueError("{0} contains only zeroes. This file is damaged beyond repair.")

    if MCJavaLevel._isDataLevel(data):
        log.info(u"Detected Java-style level")
        lev = MCJavaLevel(filename, data)
        lev.compressed = False
        return lev

    #ungzdata = None
    compressed = True
    unzippedData = None
    try:
        unzippedData = nbt.gunzip(rawdata)
    except Exception, e:
        log.info(u"Exception during Gzip operation, assuming {0} uncompressed: {1!r}".format(filename, e))
        if unzippedData is None:
            compressed = False
            unzippedData = rawdata

    #data =
    data = unzippedData
    if MCJavaLevel._isDataLevel(data):
        log.info(u"Detected compressed Java-style level")
        lev = MCJavaLevel(filename, data)
        lev.compressed = compressed
        return lev

    try:
        root_tag = nbt.load(buf=data)

    except Exception, e:
        log.info(u"Error during NBT load: {0!r}".format(e))
        log.info(traceback.format_exc())
        log.info(u"Fallback: Detected compressed flat block array, yzx ordered ")
        try:
            lev = MCJavaLevel(filename, data)
            lev.compressed = compressed
            return lev
        except Exception, e2:
            raise LoadingError(("Multiple errors encountered", e, e2), sys.exc_info()[2])

    else:
        if MCIndevLevel._isTagLevel(root_tag):
            log.info(u"Detected Indev .mclevel")
            return MCIndevLevel(root_tag, filename)
        if MCSchematic._isTagLevel(root_tag):
            log.info(u"Detected Schematic.")
            return MCSchematic(root_tag=root_tag, filename=filename)

        if INVEditChest._isTagLevel(root_tag):
            log.info(u"Detected INVEdit inventory file")
            return INVEditChest(root_tag=root_tag, filename=filename)

    raise IOError("Cannot detect file type.")


def loadWorld(name):
    filename = os.path.join(saveFileDir, name)
    return fromFile(filename, True)


def loadWorldNumber(i):
    #deprecated
    filename = u"{0}{1}{2}{3}{1}".format(saveFileDir, os.sep, u"World", i)
    return fromFile(filename, True)
