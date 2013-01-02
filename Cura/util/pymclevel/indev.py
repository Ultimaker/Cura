"""
Created on Jul 22, 2011

@author: Rio

Indev levels:

TAG_Compound "MinecraftLevel"
{
   TAG_Compound "Environment"
   {
      TAG_Short "SurroundingGroundHeight"// Height of surrounding ground (in blocks)
      TAG_Byte "SurroundingGroundType"   // Block ID of surrounding ground
      TAG_Short "SurroundingWaterHeight" // Height of surrounding water (in blocks)
      TAG_Byte "SurroundingWaterType"    // Block ID of surrounding water
      TAG_Short "CloudHeight"            // Height of the cloud layer (in blocks)
      TAG_Int "CloudColor"               // Hexadecimal value for the color of the clouds
      TAG_Int "SkyColor"                 // Hexadecimal value for the color of the sky
      TAG_Int "FogColor"                 // Hexadecimal value for the color of the fog
      TAG_Byte "SkyBrightness"           // The brightness of the sky, from 0 to 100
   }

   TAG_List "Entities"
   {
      TAG_Compound
      {
         // One of these per entity on the map.
         // These can change a lot, and are undocumented.
         // Feel free to play around with them, though.
         // The most interesting one might be the one with ID "LocalPlayer", which contains the player inventory
      }
   }

   TAG_Compound "Map"
   {
      // To access a specific block from either byte array, use the following algorithm:
      // Index = x + (y * Depth + z) * Width

      TAG_Short "Width"                  // Width of the level (along X)
      TAG_Short "Height"                 // Height of the level (along Y)
      TAG_Short "Length"                 // Length of the level (along Z)
      TAG_Byte_Array "Blocks"             // An array of Length*Height*Width bytes specifying the block types
      TAG_Byte_Array "Data"              // An array of Length*Height*Width bytes with data for each blocks

      TAG_List "Spawn"                   // Default spawn position
      {
         TAG_Short x  // These values are multiplied by 32 before being saved
         TAG_Short y  // That means that the actual values are x/32.0, y/32.0, z/32.0
         TAG_Short z
      }
   }

   TAG_Compound "About"
   {
      TAG_String "Name"                  // Level name
      TAG_String "Author"                // Name of the player who made the level
      TAG_Long "CreatedOn"               // Timestamp when the level was first created
   }
}
"""

from entity import TileEntity
from level import MCLevel
from logging import getLogger
from materials import indevMaterials
from numpy import array, swapaxes
import nbt
import os

log = getLogger(__name__)

MinecraftLevel = "MinecraftLevel"

Environment = "Environment"
SurroundingGroundHeight = "SurroundingGroundHeight"
SurroundingGroundType = "SurroundingGroundType"
SurroundingWaterHeight = "SurroundingWaterHeight"
SurroundingWaterType = "SurroundingWaterType"
CloudHeight = "CloudHeight"
CloudColor = "CloudColor"
SkyColor = "SkyColor"
FogColor = "FogColor"
SkyBrightness = "SkyBrightness"

About = "About"
Name = "Name"
Author = "Author"
CreatedOn = "CreatedOn"
Spawn = "Spawn"

__all__ = ["MCIndevLevel"]

from level import EntityLevel


class MCIndevLevel(EntityLevel):
    """ IMPORTANT: self.Blocks and self.Data are indexed with [x,z,y] via axis
    swapping to be consistent with infinite levels."""

    materials = indevMaterials

    def setPlayerSpawnPosition(self, pos, player=None):
        assert len(pos) == 3
        self.Spawn = array(pos)

    def playerSpawnPosition(self, player=None):
        return self.Spawn

    def setPlayerPosition(self, pos, player="Ignored"):
        self.LocalPlayer["Pos"] = nbt.TAG_List([nbt.TAG_Float(p) for p in pos])

    def getPlayerPosition(self, player="Ignored"):
        return array(map(lambda x: x.value, self.LocalPlayer["Pos"]))

    def setPlayerOrientation(self, yp, player="Ignored"):
        self.LocalPlayer["Rotation"] = nbt.TAG_List([nbt.TAG_Float(p) for p in yp])

    def getPlayerOrientation(self, player="Ignored"):
        """ returns (yaw, pitch) """
        return array(map(lambda x: x.value, self.LocalPlayer["Rotation"]))

    def setBlockDataAt(self, x, y, z, newdata):
        if x < 0 or y < 0 or z < 0:
            return 0
        if x >= self.Width or y >= self.Height or z >= self.Length:
            return 0
        self.Data[x, z, y] = (newdata & 0xf)

    def blockDataAt(self, x, y, z):
        if x < 0 or y < 0 or z < 0:
            return 0
        if x >= self.Width or y >= self.Height or z >= self.Length:
            return 0
        return self.Data[x, z, y]

    def blockLightAt(self, x, y, z):
        if x < 0 or y < 0 or z < 0:
            return 0
        if x >= self.Width or y >= self.Height or z >= self.Length:
            return 0
        return self.BlockLight[x, z, y]

    def __repr__(self):
        return u"MCIndevLevel({0}): {1}W {2}L {3}H".format(self.filename, self.Width, self.Length, self.Height)

    @classmethod
    def _isTagLevel(cls, root_tag):
        return "MinecraftLevel" == root_tag.name

    def __init__(self, root_tag=None, filename=""):
        self.Width = 0
        self.Height = 0
        self.Length = 0
        self.Blocks = array([], "uint8")
        self.Data = array([], "uint8")
        self.Spawn = (0, 0, 0)
        self.filename = filename

        if root_tag:

            self.root_tag = root_tag
            mapTag = root_tag["Map"]
            self.Width = mapTag["Width"].value
            self.Length = mapTag["Length"].value
            self.Height = mapTag["Height"].value

            mapTag["Blocks"].value.shape = (self.Height, self.Length, self.Width)

            self.Blocks = swapaxes(mapTag["Blocks"].value, 0, 2)

            mapTag["Data"].value.shape = (self.Height, self.Length, self.Width)

            self.Data = swapaxes(mapTag["Data"].value, 0, 2)

            self.BlockLight = self.Data & 0xf

            self.Data >>= 4

            self.Spawn = [mapTag[Spawn][i].value for i in range(3)]

            if "Entities" not in root_tag:
                root_tag["Entities"] = nbt.TAG_List()
            self.Entities = root_tag["Entities"]

            # xxx fixup Motion and Pos to match infdev format
            def numbersToDoubles(ent):
                for attr in "Motion", "Pos":
                    if attr in ent:
                        ent[attr] = nbt.TAG_List([nbt.TAG_Double(t.value) for t in ent[attr]])
            for ent in self.Entities:
                numbersToDoubles(ent)

            if "TileEntities" not in root_tag:
                root_tag["TileEntities"] = nbt.TAG_List()
            self.TileEntities = root_tag["TileEntities"]
            # xxx fixup TileEntities positions to match infdev format
            for te in self.TileEntities:
                pos = te["Pos"].value

                (x, y, z) = self.decodePos(pos)

                TileEntity.setpos(te, (x, y, z))


            localPlayerList = [tag for tag in root_tag["Entities"] if tag['id'].value == 'LocalPlayer']
            if len(localPlayerList) == 0:  # omen doesn't make a player entity
                playerTag = nbt.TAG_Compound()
                playerTag['id'] = nbt.TAG_String('LocalPlayer')
                playerTag['Pos'] = nbt.TAG_List([nbt.TAG_Float(0.), nbt.TAG_Float(64.), nbt.TAG_Float(0.)])
                playerTag['Rotation'] = nbt.TAG_List([nbt.TAG_Float(0.), nbt.TAG_Float(45.)])
                self.LocalPlayer = playerTag

            else:
                self.LocalPlayer = localPlayerList[0]

        else:
            log.info(u"Creating new Indev levels is not yet implemented.!")
            raise ValueError("Can't do that yet")
#            self.SurroundingGroundHeight = root_tag[Environment][SurroundingGroundHeight].value
#            self.SurroundingGroundType = root_tag[Environment][SurroundingGroundType].value
#            self.SurroundingWaterHeight = root_tag[Environment][SurroundingGroundHeight].value
#            self.SurroundingWaterType = root_tag[Environment][SurroundingWaterType].value
#            self.CloudHeight = root_tag[Environment][CloudHeight].value
#            self.CloudColor = root_tag[Environment][CloudColor].value
#            self.SkyColor = root_tag[Environment][SkyColor].value
#            self.FogColor = root_tag[Environment][FogColor].value
#            self.SkyBrightness = root_tag[Environment][SkyBrightness].value
#            self.TimeOfDay = root_tag[Environment]["TimeOfDay"].value
#
#
#            self.Name = self.root_tag[About][Name].value
#            self.Author = self.root_tag[About][Author].value
#            self.CreatedOn = self.root_tag[About][CreatedOn].value

    def rotateLeft(self):
        MCLevel.rotateLeft(self)

        self.Data = swapaxes(self.Data, 1, 0)[:, ::-1, :]  # x=y; y=-x

        torchRotation = array([0, 4, 3, 1, 2, 5,
                               6, 7,

                               8, 9, 10, 11, 12, 13, 14, 15])

        torchIndexes = (self.Blocks == self.materials.Torch.ID)
        log.info(u"Rotating torches: {0}".format(len(torchIndexes.nonzero()[0])))
        self.Data[torchIndexes] = torchRotation[self.Data[torchIndexes]]

    def decodePos(self, v):
        b = 10
        m = (1 << b) - 1
        return v & m, (v >> b) & m, (v >> (2 * b))

    def encodePos(self, x, y, z):
        b = 10
        return x + (y << b) + (z << (2 * b))

    def saveToFile(self, filename=None):
        if filename is None:
            filename = self.filename
        if filename is None:
            log.warn(u"Attempted to save an unnamed file in place")
            return  # you fool!

        self.Data <<= 4
        self.Data |= (self.BlockLight & 0xf)

        self.Blocks = swapaxes(self.Blocks, 0, 2)
        self.Data = swapaxes(self.Data, 0, 2)

        mapTag = nbt.TAG_Compound()
        mapTag["Width"] = nbt.TAG_Short(self.Width)
        mapTag["Height"] = nbt.TAG_Short(self.Height)
        mapTag["Length"] = nbt.TAG_Short(self.Length)
        mapTag["Blocks"] = nbt.TAG_Byte_Array(self.Blocks)
        mapTag["Data"] = nbt.TAG_Byte_Array(self.Data)

        self.Blocks = swapaxes(self.Blocks, 0, 2)
        self.Data = swapaxes(self.Data, 0, 2)

        mapTag[Spawn] = nbt.TAG_List([nbt.TAG_Short(i) for i in self.Spawn])

        self.root_tag["Map"] = mapTag

        self.Entities.append(self.LocalPlayer)
        # fix up Entities imported from Alpha worlds
        def numbersToFloats(ent):
            for attr in "Motion", "Pos":
                if attr in ent:
                    ent[attr] = nbt.TAG_List([nbt.TAG_Double(t.value) for t in ent[attr]])
        for ent in self.Entities:
            numbersToFloats(ent)

        # fix up TileEntities imported from Alpha worlds.
        for ent in self.TileEntities:
            if "Pos" not in ent and all(c in ent for c in 'xyz'):
                ent["Pos"] = nbt.TAG_Int(self.encodePos(ent['x'].value, ent['y'].value, ent['z'].value))
        # output_file = gzip.open(self.filename, "wb", compresslevel=1)
        try:
            os.rename(filename, filename + ".old")
        except Exception:
            pass

        try:
            self.root_tag.save(filename)
        except:
            os.rename(filename + ".old", filename)

        try:
            os.remove(filename + ".old")
        except Exception:
            pass

        self.Entities.remove(self.LocalPlayer)

        self.BlockLight = self.Data & 0xf

        self.Data >>= 4
