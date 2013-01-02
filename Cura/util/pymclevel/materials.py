
from logging import getLogger
from numpy import zeros, rollaxis, indices
import traceback
from os.path import join
from collections import defaultdict
from pprint import pformat

import os

NOTEX = (0x90, 0xD0)

try:
	import yaml
except:
	yaml = None

log = getLogger(__file__)


class Block(object):
    """
    Value object representing an (id, data) pair.
    Provides elements of its parent material's block arrays.
    Blocks will have (name, ID, blockData, aka, color, brightness, opacity, blockTextures)
    """

    def __str__(self):
        return "<Block {name} ({id}:{data}) hasVariants:{ha}>".format(
            name=self.name, id=self.ID, data=self.blockData, ha=self.hasVariants)

    def __repr__(self):
        return str(self)

    def __cmp__(self, other):
        if not isinstance(other, Block):
            return -1
        key = lambda a: a and (a.ID, a.blockData)
        return cmp(key(self), key(other))

    hasVariants = False  # True if blockData defines additional blocktypes

    def __init__(self, materials, blockID, blockData=0):
        self.materials = materials
        self.ID = blockID
        self.blockData = blockData

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        if attr == "name":
            r = self.materials.names[self.ID]
        else:
            r = getattr(self.materials, attr)[self.ID]
        if attr in ("name", "aka", "color", "type"):
            r = r[self.blockData]
        return r


class MCMaterials(object):
    defaultColor = (0xc9, 0x77, 0xf0, 0xff)
    defaultBrightness = 0
    defaultOpacity = 15
    defaultTexture = NOTEX
    defaultTex = [t // 16 for t in defaultTexture]

    def __init__(self, defaultName="Unused Block"):
        object.__init__(self)
        self.yamlDatas = []

        self.defaultName = defaultName

        self.blockTextures = zeros((256, 16, 6, 2), dtype='uint8')
        self.blockTextures[:] = self.defaultTexture
        self.names = [[defaultName] * 16 for i in range(256)]
        self.aka = [[""] * 16 for i in range(256)]

        self.type = [["NORMAL"] * 16] * 256
        self.blocksByType = defaultdict(list)
        self.allBlocks = []
        self.blocksByID = {}

        self.lightEmission = zeros(256, dtype='uint8')
        self.lightEmission[:] = self.defaultBrightness
        self.lightAbsorption = zeros(256, dtype='uint8')
        self.lightAbsorption[:] = self.defaultOpacity
        self.flatColors = zeros((256, 16, 4), dtype='uint8')
        self.flatColors[:] = self.defaultColor

        self.idStr = {}

        self.color = self.flatColors
        self.brightness = self.lightEmission
        self.opacity = self.lightAbsorption

        self.Air = self.addBlock(0,
            name="Air",
            texture=(0x80, 0xB0),
            opacity=0,
        )

    def __repr__(self):
        return "<MCMaterials ({0})>".format(self.name)

    @property
    def AllStairs(self):
        return [b for b in self.allBlocks if b.name.endswith("Stairs")]

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __len__(self):
        return len(self.allBlocks)

    def __iter__(self):
        return iter(self.allBlocks)

    def __getitem__(self, key):
        """ Let's be magic. If we get a string, return the first block whose
            name matches exactly. If we get a (id, data) pair or an id, return
            that block. for example:

                level.materials[0]  # returns Air
                level.materials["Air"]  # also returns Air
                level.materials["Powered Rail"]  # returns Powered Rail
                level.materials["Lapis Lazuli Block"]  # in Classic

           """
        if isinstance(key, basestring):
            for b in self.allBlocks:
                if b.name == key:
                    return b
            raise KeyError("No blocks named: " + key)
        if isinstance(key, (tuple, list)):
            id, blockData = key
            return self.blockWithID(id, blockData)
        return self.blockWithID(key)

    def blocksMatching(self, name):
        name = name.lower()
        return [v for v in self.allBlocks if name in v.name.lower() or name in v.aka.lower()]

    def blockWithID(self, id, data=0):
        if (id, data) in self.blocksByID:
            return self.blocksByID[id, data]
        else:
            bl = Block(self, id, blockData=data)
            bl.hasVariants = True
            return bl

    def addYamlBlocksFromFile(self, filename):
        if yaml is None:
            return

        try:
            import pkg_resources

            f = pkg_resources.resource_stream(__name__, filename)
        except (ImportError, IOError):
            root = os.environ.get("PYMCLEVEL_YAML_ROOT", "pymclevel")  # fall back to cwd as last resort
            path = join(root, filename)

            log.exception("Failed to read %s using pkg_resources. Trying %s instead." % (filename, path))

            f = file(path)
        try:
            log.info(u"Loading block info from %s", f)
            blockyaml = yaml.load(f)
            self.addYamlBlocks(blockyaml)

        except Exception, e:
            log.warn(u"Exception while loading block info from %s: %s", f, e)
            traceback.print_exc()

    def addYamlBlocks(self, blockyaml):
        self.yamlDatas.append(blockyaml)
        for block in blockyaml['blocks']:
            try:
                self.addYamlBlock(block)
            except Exception, e:
                log.warn(u"Exception while parsing block: %s", e)
                traceback.print_exc()
                log.warn(u"Block definition: \n%s", pformat(block))

    def addYamlBlock(self, kw):
        blockID = kw['id']

        # xxx unused_yaml_properties variable unused; needed for
        #     documentation purpose of some sort?  -zothar
        #unused_yaml_properties = \
        #['explored',
        # # 'id',
        # # 'idStr',
        # # 'mapcolor',
        # # 'name',
        # # 'tex',
        # ### 'tex_data',
        # # 'tex_direction',
        # ### 'tex_direction_data',
        # 'tex_extra',
        # # 'type'
        # ]

        for val, data in kw.get('data', {0: {}}).items():
            datakw = dict(kw)
            datakw.update(data)
            idStr = datakw.get('idStr', "")
            tex = [t * 16 for t in datakw.get('tex', self.defaultTex)]
            texture = [tex] * 6
            texDirs = {
                "FORWARD": 5,
                "BACKWARD": 4,
                "LEFT": 1,
                "RIGHT": 0,
                "TOP": 2,
                "BOTTOM": 3,
            }
            for dirname, dirtex in datakw.get('tex_direction', {}).items():
                if dirname == "SIDES":
                    for dirname in ("LEFT", "RIGHT"):
                        texture[texDirs[dirname]] = [t * 16 for t in dirtex]
                if dirname in texDirs:
                    texture[texDirs[dirname]] = [t * 16 for t in dirtex]
            datakw['texture'] = texture
            # print datakw
            block = self.addBlock(blockID, val, **datakw)
            block.yaml = datakw
            if idStr not in self.idStr:
                self.idStr[idStr] = block

        tex_direction_data = kw.get('tex_direction_data')
        if tex_direction_data:
            texture = datakw['texture']
            # X+0, X-1, Y+, Y-, Z+b, Z-f
            texDirMap = {
                "NORTH": 0,
                "EAST": 1,
                "SOUTH": 2,
                "WEST": 3,
            }

            def rot90cw():
                rot = (5, 0, 2, 3, 4, 1)
                texture[:] = [texture[r] for r in rot]

            for data, dir in tex_direction_data.items():
                for _i in range(texDirMap.get(dir, 0)):
                    rot90cw()
                self.blockTextures[blockID][data] = texture

    def addBlock(self, blockID, blockData=0, **kw):
        name = kw.pop('name', self.names[blockID][blockData])

        self.lightEmission[blockID] = kw.pop('brightness', self.defaultBrightness)
        self.lightAbsorption[blockID] = kw.pop('opacity', self.defaultOpacity)
        self.aka[blockID][blockData] = kw.pop('aka', "")
        type = kw.pop('type', 'NORMAL')

        color = kw.pop('mapcolor', self.flatColors[blockID, blockData])
        self.flatColors[blockID, (blockData or slice(None))] = (tuple(color) + (255,))[:4]

        texture = kw.pop('texture', None)

        if texture:
            self.blockTextures[blockID, (blockData or slice(None))] = texture

        if blockData is 0:
            self.names[blockID] = [name] * 16
            self.type[blockID] = [type] * 16
        else:
            self.names[blockID][blockData] = name
            self.type[blockID][blockData] = type

        block = Block(self, blockID, blockData)

        self.allBlocks.append(block)
        self.blocksByType[type].append(block)

        if (blockID, 0) in self.blocksByID:
            self.blocksByID[blockID, 0].hasVariants = True
            block.hasVariants = True

        self.blocksByID[blockID, blockData] = block

        return block

alphaMaterials = MCMaterials(defaultName="Future Block!")
alphaMaterials.name = "Alpha"
alphaMaterials.addYamlBlocksFromFile("minecraft.yaml")

# --- Special treatment for some blocks ---

HugeMushroomTypes = {
   "Northwest": 1,
   "North": 2,
   "Northeast": 3,
   "East": 6,
   "Southeast": 9,
   "South": 8,
   "Southwest": 7,
   "West": 4,
   "Stem": 10,
   "Top": 5,
}
from faces import FaceXDecreasing, FaceXIncreasing, FaceYIncreasing, FaceZDecreasing, FaceZIncreasing

Red = (0xD0, 0x70)
Brown = (0xE0, 0x70)
Pore = (0xE0, 0x80)
Stem = (0xD0, 0x80)


def defineShroomFaces(Shroom, id, name):
    for way, data in sorted(HugeMushroomTypes.items(), key=lambda a: a[1]):
        loway = way.lower()
        if way is "Stem":
            tex = [Stem, Stem, Pore, Pore, Stem, Stem]
        elif way is "Pore":
            tex = Pore
        else:
            tex = [Pore] * 6
            tex[FaceYIncreasing] = Shroom
            if "north" in loway:
                tex[FaceZDecreasing] = Shroom
            if "south" in loway:
                tex[FaceZIncreasing] = Shroom
            if "west" in loway:
                tex[FaceXDecreasing] = Shroom
            if "east" in loway:
                tex[FaceXIncreasing] = Shroom

        alphaMaterials.addBlock(id, blockData=data,
            name="Huge " + name + " Mushroom (" + way + ")",
            texture=tex,
            )

defineShroomFaces(Brown, 99, "Brown")
defineShroomFaces(Red, 100, "Red")

classicMaterials = MCMaterials(defaultName="Not present in Classic")
classicMaterials.name = "Classic"
classicMaterials.addYamlBlocksFromFile("classic.yaml")

indevMaterials = MCMaterials(defaultName="Not present in Indev")
indevMaterials.name = "Indev"
indevMaterials.addYamlBlocksFromFile("indev.yaml")

pocketMaterials = MCMaterials()
pocketMaterials.name = "Pocket"
pocketMaterials.addYamlBlocksFromFile("pocket.yaml")

# --- Static block defs ---

alphaMaterials.Stone = alphaMaterials[1, 0]
alphaMaterials.Grass = alphaMaterials[2, 0]
alphaMaterials.Dirt = alphaMaterials[3, 0]
alphaMaterials.Cobblestone = alphaMaterials[4, 0]
alphaMaterials.WoodPlanks = alphaMaterials[5, 0]
alphaMaterials.Sapling = alphaMaterials[6, 0]
alphaMaterials.SpruceSapling = alphaMaterials[6, 1]
alphaMaterials.BirchSapling = alphaMaterials[6, 2]
alphaMaterials.Bedrock = alphaMaterials[7, 0]
alphaMaterials.WaterActive = alphaMaterials[8, 0]
alphaMaterials.Water = alphaMaterials[9, 0]
alphaMaterials.LavaActive = alphaMaterials[10, 0]
alphaMaterials.Lava = alphaMaterials[11, 0]
alphaMaterials.Sand = alphaMaterials[12, 0]
alphaMaterials.Gravel = alphaMaterials[13, 0]
alphaMaterials.GoldOre = alphaMaterials[14, 0]
alphaMaterials.IronOre = alphaMaterials[15, 0]
alphaMaterials.CoalOre = alphaMaterials[16, 0]
alphaMaterials.Wood = alphaMaterials[17, 0]
alphaMaterials.Ironwood = alphaMaterials[17, 1]
alphaMaterials.BirchWood = alphaMaterials[17, 2]
alphaMaterials.Leaves = alphaMaterials[18, 0]
alphaMaterials.PineLeaves = alphaMaterials[18, 1]
alphaMaterials.BirchLeaves = alphaMaterials[18, 2]
alphaMaterials.JungleLeaves = alphaMaterials[18, 3]
alphaMaterials.LeavesPermanent = alphaMaterials[18, 4]
alphaMaterials.PineLeavesPermanent = alphaMaterials[18, 5]
alphaMaterials.BirchLeavesPermanent = alphaMaterials[18, 6]
alphaMaterials.JungleLeavesPermanent = alphaMaterials[18, 7]
alphaMaterials.LeavesDecaying = alphaMaterials[18, 8]
alphaMaterials.PineLeavesDecaying = alphaMaterials[18, 9]
alphaMaterials.BirchLeavesDecaying = alphaMaterials[18, 10]
alphaMaterials.JungleLeavesDecaying = alphaMaterials[18, 11]
alphaMaterials.Sponge = alphaMaterials[19, 0]
alphaMaterials.Glass = alphaMaterials[20, 0]

alphaMaterials.LapisLazuliOre = alphaMaterials[21, 0]
alphaMaterials.LapisLazuliBlock = alphaMaterials[22, 0]
alphaMaterials.Dispenser = alphaMaterials[23, 0]
alphaMaterials.Sandstone = alphaMaterials[24, 0]
alphaMaterials.NoteBlock = alphaMaterials[25, 0]
alphaMaterials.Bed = alphaMaterials[26, 0]
alphaMaterials.PoweredRail = alphaMaterials[27, 0]
alphaMaterials.DetectorRail = alphaMaterials[28, 0]
alphaMaterials.StickyPiston = alphaMaterials[29, 0]
alphaMaterials.Web = alphaMaterials[30, 0]
alphaMaterials.UnusedShrub = alphaMaterials[31, 0]
alphaMaterials.TallGrass = alphaMaterials[31, 1]
alphaMaterials.Shrub = alphaMaterials[31, 2]
alphaMaterials.DesertShrub2 = alphaMaterials[32, 0]
alphaMaterials.Piston = alphaMaterials[33, 0]
alphaMaterials.PistonHead = alphaMaterials[34, 0]
alphaMaterials.WhiteWool = alphaMaterials[35, 0]
alphaMaterials.OrangeWool = alphaMaterials[35, 1]
alphaMaterials.MagentaWool = alphaMaterials[35, 2]
alphaMaterials.LightBlueWool = alphaMaterials[35, 3]
alphaMaterials.YellowWool = alphaMaterials[35, 4]
alphaMaterials.LightGreenWool = alphaMaterials[35, 5]
alphaMaterials.PinkWool = alphaMaterials[35, 6]
alphaMaterials.GrayWool = alphaMaterials[35, 7]
alphaMaterials.LightGrayWool = alphaMaterials[35, 8]
alphaMaterials.CyanWool = alphaMaterials[35, 9]
alphaMaterials.PurpleWool = alphaMaterials[35, 10]
alphaMaterials.BlueWool = alphaMaterials[35, 11]
alphaMaterials.BrownWool = alphaMaterials[35, 12]
alphaMaterials.DarkGreenWool = alphaMaterials[35, 13]
alphaMaterials.RedWool = alphaMaterials[35, 14]
alphaMaterials.BlackWool = alphaMaterials[35, 15]

alphaMaterials.Flower = alphaMaterials[37, 0]
alphaMaterials.Rose = alphaMaterials[38, 0]
alphaMaterials.BrownMushroom = alphaMaterials[39, 0]
alphaMaterials.RedMushroom = alphaMaterials[40, 0]
alphaMaterials.BlockofGold = alphaMaterials[41, 0]
alphaMaterials.BlockofIron = alphaMaterials[42, 0]
alphaMaterials.DoubleStoneSlab = alphaMaterials[43, 0]
alphaMaterials.DoubleSandstoneSlab = alphaMaterials[43, 1]
alphaMaterials.DoubleWoodenSlab = alphaMaterials[43, 2]
alphaMaterials.DoubleCobblestoneSlab = alphaMaterials[43, 3]
alphaMaterials.DoubleBrickSlab = alphaMaterials[43, 4]
alphaMaterials.DoubleStoneBrickSlab = alphaMaterials[43, 5]
alphaMaterials.StoneSlab = alphaMaterials[44, 0]
alphaMaterials.SandstoneSlab = alphaMaterials[44, 1]
alphaMaterials.WoodenSlab = alphaMaterials[44, 2]
alphaMaterials.CobblestoneSlab = alphaMaterials[44, 3]
alphaMaterials.BrickSlab = alphaMaterials[44, 4]
alphaMaterials.StoneBrickSlab = alphaMaterials[44, 5]
alphaMaterials.Brick = alphaMaterials[45, 0]
alphaMaterials.TNT = alphaMaterials[46, 0]
alphaMaterials.Bookshelf = alphaMaterials[47, 0]
alphaMaterials.MossStone = alphaMaterials[48, 0]
alphaMaterials.Obsidian = alphaMaterials[49, 0]

alphaMaterials.Torch = alphaMaterials[50, 0]
alphaMaterials.Fire = alphaMaterials[51, 0]
alphaMaterials.MonsterSpawner = alphaMaterials[52, 0]
alphaMaterials.WoodenStairs = alphaMaterials[53, 0]
alphaMaterials.Chest = alphaMaterials[54, 0]
alphaMaterials.RedstoneWire = alphaMaterials[55, 0]
alphaMaterials.DiamondOre = alphaMaterials[56, 0]
alphaMaterials.BlockofDiamond = alphaMaterials[57, 0]
alphaMaterials.CraftingTable = alphaMaterials[58, 0]
alphaMaterials.Crops = alphaMaterials[59, 0]
alphaMaterials.Farmland = alphaMaterials[60, 0]
alphaMaterials.Furnace = alphaMaterials[61, 0]
alphaMaterials.LitFurnace = alphaMaterials[62, 0]
alphaMaterials.Sign = alphaMaterials[63, 0]
alphaMaterials.WoodenDoor = alphaMaterials[64, 0]
alphaMaterials.Ladder = alphaMaterials[65, 0]
alphaMaterials.Rail = alphaMaterials[66, 0]
alphaMaterials.StoneStairs = alphaMaterials[67, 0]
alphaMaterials.WallSign = alphaMaterials[68, 0]
alphaMaterials.Lever = alphaMaterials[69, 0]
alphaMaterials.StoneFloorPlate = alphaMaterials[70, 0]
alphaMaterials.IronDoor = alphaMaterials[71, 0]
alphaMaterials.WoodFloorPlate = alphaMaterials[72, 0]
alphaMaterials.RedstoneOre = alphaMaterials[73, 0]
alphaMaterials.RedstoneOreGlowing = alphaMaterials[74, 0]
alphaMaterials.RedstoneTorchOff = alphaMaterials[75, 0]
alphaMaterials.RedstoneTorchOn = alphaMaterials[76, 0]
alphaMaterials.Button = alphaMaterials[77, 0]
alphaMaterials.SnowLayer = alphaMaterials[78, 0]
alphaMaterials.Ice = alphaMaterials[79, 0]
alphaMaterials.Snow = alphaMaterials[80, 0]

alphaMaterials.Cactus = alphaMaterials[81, 0]
alphaMaterials.Clay = alphaMaterials[82, 0]
alphaMaterials.SugarCane = alphaMaterials[83, 0]
alphaMaterials.Jukebox = alphaMaterials[84, 0]
alphaMaterials.Fence = alphaMaterials[85, 0]
alphaMaterials.Pumpkin = alphaMaterials[86, 0]
alphaMaterials.Netherrack = alphaMaterials[87, 0]
alphaMaterials.SoulSand = alphaMaterials[88, 0]
alphaMaterials.Glowstone = alphaMaterials[89, 0]
alphaMaterials.NetherPortal = alphaMaterials[90, 0]
alphaMaterials.JackOLantern = alphaMaterials[91, 0]
alphaMaterials.Cake = alphaMaterials[92, 0]
alphaMaterials.RedstoneRepeaterOff = alphaMaterials[93, 0]
alphaMaterials.RedstoneRepeaterOn = alphaMaterials[94, 0]
alphaMaterials.AprilFoolsChest = alphaMaterials[95, 0]
alphaMaterials.Trapdoor = alphaMaterials[96, 0]

alphaMaterials.HiddenSilverfishStone = alphaMaterials[97, 0]
alphaMaterials.HiddenSilverfishCobblestone = alphaMaterials[97, 1]
alphaMaterials.HiddenSilverfishStoneBrick = alphaMaterials[97, 2]
alphaMaterials.StoneBricks = alphaMaterials[98, 0]
alphaMaterials.MossyStoneBricks = alphaMaterials[98, 1]
alphaMaterials.CrackedStoneBricks = alphaMaterials[98, 2]
alphaMaterials.HugeBrownMushroom = alphaMaterials[99, 0]
alphaMaterials.HugeRedMushroom = alphaMaterials[100, 0]
alphaMaterials.IronBars = alphaMaterials[101, 0]
alphaMaterials.GlassPane = alphaMaterials[102, 0]
alphaMaterials.Watermelon = alphaMaterials[103, 0]
alphaMaterials.PumpkinStem = alphaMaterials[104, 0]
alphaMaterials.MelonStem = alphaMaterials[105, 0]
alphaMaterials.Vines = alphaMaterials[106, 0]
alphaMaterials.FenceGate = alphaMaterials[107, 0]
alphaMaterials.BrickStairs = alphaMaterials[108, 0]
alphaMaterials.StoneBrickStairs = alphaMaterials[109, 0]
alphaMaterials.Mycelium = alphaMaterials[110, 0]
alphaMaterials.Lilypad = alphaMaterials[111, 0]
alphaMaterials.NetherBrick = alphaMaterials[112, 0]
alphaMaterials.NetherBrickFence = alphaMaterials[113, 0]
alphaMaterials.NetherBrickStairs = alphaMaterials[114, 0]
alphaMaterials.NetherWart = alphaMaterials[115, 0]

# --- Classic static block defs ---
classicMaterials.Stone = classicMaterials[1]
classicMaterials.Grass = classicMaterials[2]
classicMaterials.Dirt = classicMaterials[3]
classicMaterials.Cobblestone = classicMaterials[4]
classicMaterials.WoodPlanks = classicMaterials[5]
classicMaterials.Sapling = classicMaterials[6]
classicMaterials.Bedrock = classicMaterials[7]
classicMaterials.WaterActive = classicMaterials[8]
classicMaterials.Water = classicMaterials[9]
classicMaterials.LavaActive = classicMaterials[10]
classicMaterials.Lava = classicMaterials[11]
classicMaterials.Sand = classicMaterials[12]
classicMaterials.Gravel = classicMaterials[13]
classicMaterials.GoldOre = classicMaterials[14]
classicMaterials.IronOre = classicMaterials[15]
classicMaterials.CoalOre = classicMaterials[16]
classicMaterials.Wood = classicMaterials[17]
classicMaterials.Leaves = classicMaterials[18]
classicMaterials.Sponge = classicMaterials[19]
classicMaterials.Glass = classicMaterials[20]

classicMaterials.RedWool = classicMaterials[21]
classicMaterials.OrangeWool = classicMaterials[22]
classicMaterials.YellowWool = classicMaterials[23]
classicMaterials.LimeWool = classicMaterials[24]
classicMaterials.GreenWool = classicMaterials[25]
classicMaterials.AquaWool = classicMaterials[26]
classicMaterials.CyanWool = classicMaterials[27]
classicMaterials.BlueWool = classicMaterials[28]
classicMaterials.PurpleWool = classicMaterials[29]
classicMaterials.IndigoWool = classicMaterials[30]
classicMaterials.VioletWool = classicMaterials[31]
classicMaterials.MagentaWool = classicMaterials[32]
classicMaterials.PinkWool = classicMaterials[33]
classicMaterials.BlackWool = classicMaterials[34]
classicMaterials.GrayWool = classicMaterials[35]
classicMaterials.WhiteWool = classicMaterials[36]

classicMaterials.Flower = classicMaterials[37]
classicMaterials.Rose = classicMaterials[38]
classicMaterials.BrownMushroom = classicMaterials[39]
classicMaterials.RedMushroom = classicMaterials[40]
classicMaterials.BlockofGold = classicMaterials[41]
classicMaterials.BlockofIron = classicMaterials[42]
classicMaterials.DoubleStoneSlab = classicMaterials[43]
classicMaterials.StoneSlab = classicMaterials[44]
classicMaterials.Brick = classicMaterials[45]
classicMaterials.TNT = classicMaterials[46]
classicMaterials.Bookshelf = classicMaterials[47]
classicMaterials.MossStone = classicMaterials[48]
classicMaterials.Obsidian = classicMaterials[49]

# --- Indev static block defs ---
indevMaterials.Stone = indevMaterials[1]
indevMaterials.Grass = indevMaterials[2]
indevMaterials.Dirt = indevMaterials[3]
indevMaterials.Cobblestone = indevMaterials[4]
indevMaterials.WoodPlanks = indevMaterials[5]
indevMaterials.Sapling = indevMaterials[6]
indevMaterials.Bedrock = indevMaterials[7]
indevMaterials.WaterActive = indevMaterials[8]
indevMaterials.Water = indevMaterials[9]
indevMaterials.LavaActive = indevMaterials[10]
indevMaterials.Lava = indevMaterials[11]
indevMaterials.Sand = indevMaterials[12]
indevMaterials.Gravel = indevMaterials[13]
indevMaterials.GoldOre = indevMaterials[14]
indevMaterials.IronOre = indevMaterials[15]
indevMaterials.CoalOre = indevMaterials[16]
indevMaterials.Wood = indevMaterials[17]
indevMaterials.Leaves = indevMaterials[18]
indevMaterials.Sponge = indevMaterials[19]
indevMaterials.Glass = indevMaterials[20]

indevMaterials.RedWool = indevMaterials[21]
indevMaterials.OrangeWool = indevMaterials[22]
indevMaterials.YellowWool = indevMaterials[23]
indevMaterials.LimeWool = indevMaterials[24]
indevMaterials.GreenWool = indevMaterials[25]
indevMaterials.AquaWool = indevMaterials[26]
indevMaterials.CyanWool = indevMaterials[27]
indevMaterials.BlueWool = indevMaterials[28]
indevMaterials.PurpleWool = indevMaterials[29]
indevMaterials.IndigoWool = indevMaterials[30]
indevMaterials.VioletWool = indevMaterials[31]
indevMaterials.MagentaWool = indevMaterials[32]
indevMaterials.PinkWool = indevMaterials[33]
indevMaterials.BlackWool = indevMaterials[34]
indevMaterials.GrayWool = indevMaterials[35]
indevMaterials.WhiteWool = indevMaterials[36]

indevMaterials.Flower = indevMaterials[37]
indevMaterials.Rose = indevMaterials[38]
indevMaterials.BrownMushroom = indevMaterials[39]
indevMaterials.RedMushroom = indevMaterials[40]
indevMaterials.BlockofGold = indevMaterials[41]
indevMaterials.BlockofIron = indevMaterials[42]
indevMaterials.DoubleStoneSlab = indevMaterials[43]
indevMaterials.StoneSlab = indevMaterials[44]
indevMaterials.Brick = indevMaterials[45]
indevMaterials.TNT = indevMaterials[46]
indevMaterials.Bookshelf = indevMaterials[47]
indevMaterials.MossStone = indevMaterials[48]
indevMaterials.Obsidian = indevMaterials[49]

indevMaterials.Torch = indevMaterials[50, 0]
indevMaterials.Fire = indevMaterials[51, 0]
indevMaterials.InfiniteWater = indevMaterials[52, 0]
indevMaterials.InfiniteLava = indevMaterials[53, 0]
indevMaterials.Chest = indevMaterials[54, 0]
indevMaterials.Cog = indevMaterials[55, 0]
indevMaterials.DiamondOre = indevMaterials[56, 0]
indevMaterials.BlockofDiamond = indevMaterials[57, 0]
indevMaterials.CraftingTable = indevMaterials[58, 0]
indevMaterials.Crops = indevMaterials[59, 0]
indevMaterials.Farmland = indevMaterials[60, 0]
indevMaterials.Furnace = indevMaterials[61, 0]
indevMaterials.LitFurnace = indevMaterials[62, 0]

# --- Pocket static block defs ---

pocketMaterials.Air = pocketMaterials[0, 0]
pocketMaterials.Stone = pocketMaterials[1, 0]
pocketMaterials.Grass = pocketMaterials[2, 0]
pocketMaterials.Dirt = pocketMaterials[3, 0]
pocketMaterials.Cobblestone = pocketMaterials[4, 0]
pocketMaterials.WoodPlanks = pocketMaterials[5, 0]
pocketMaterials.Sapling = pocketMaterials[6, 0]
pocketMaterials.SpruceSapling = pocketMaterials[6, 1]
pocketMaterials.BirchSapling = pocketMaterials[6, 2]
pocketMaterials.Bedrock = pocketMaterials[7, 0]
pocketMaterials.Wateractive = pocketMaterials[8, 0]
pocketMaterials.Water = pocketMaterials[9, 0]
pocketMaterials.Lavaactive = pocketMaterials[10, 0]
pocketMaterials.Lava = pocketMaterials[11, 0]
pocketMaterials.Sand = pocketMaterials[12, 0]
pocketMaterials.Gravel = pocketMaterials[13, 0]
pocketMaterials.GoldOre = pocketMaterials[14, 0]
pocketMaterials.IronOre = pocketMaterials[15, 0]
pocketMaterials.CoalOre = pocketMaterials[16, 0]
pocketMaterials.Wood = pocketMaterials[17, 0]
pocketMaterials.PineWood = pocketMaterials[17, 1]
pocketMaterials.BirchWood = pocketMaterials[17, 2]
pocketMaterials.Leaves = pocketMaterials[18, 0]
pocketMaterials.Glass = pocketMaterials[20, 0]

pocketMaterials.LapisLazuliOre = pocketMaterials[21, 0]
pocketMaterials.LapisLazuliBlock = pocketMaterials[22, 0]
pocketMaterials.Sandstone = pocketMaterials[24, 0]
pocketMaterials.Bed = pocketMaterials[26, 0]
pocketMaterials.Web = pocketMaterials[30, 0]
pocketMaterials.UnusedShrub = pocketMaterials[31, 0]
pocketMaterials.TallGrass = pocketMaterials[31, 1]
pocketMaterials.Shrub = pocketMaterials[31, 2]
pocketMaterials.WhiteWool = pocketMaterials[35, 0]
pocketMaterials.OrangeWool = pocketMaterials[35, 1]
pocketMaterials.MagentaWool = pocketMaterials[35, 2]
pocketMaterials.LightBlueWool = pocketMaterials[35, 3]
pocketMaterials.YellowWool = pocketMaterials[35, 4]
pocketMaterials.LightGreenWool = pocketMaterials[35, 5]
pocketMaterials.PinkWool = pocketMaterials[35, 6]
pocketMaterials.GrayWool = pocketMaterials[35, 7]
pocketMaterials.LightGrayWool = pocketMaterials[35, 8]
pocketMaterials.CyanWool = pocketMaterials[35, 9]
pocketMaterials.PurpleWool = pocketMaterials[35, 10]
pocketMaterials.BlueWool = pocketMaterials[35, 11]
pocketMaterials.BrownWool = pocketMaterials[35, 12]
pocketMaterials.DarkGreenWool = pocketMaterials[35, 13]
pocketMaterials.RedWool = pocketMaterials[35, 14]
pocketMaterials.BlackWool = pocketMaterials[35, 15]
pocketMaterials.Flower = pocketMaterials[37, 0]
pocketMaterials.Rose = pocketMaterials[38, 0]
pocketMaterials.BrownMushroom = pocketMaterials[39, 0]
pocketMaterials.RedMushroom = pocketMaterials[40, 0]
pocketMaterials.BlockofGold = pocketMaterials[41, 0]
pocketMaterials.BlockofIron = pocketMaterials[42, 0]
pocketMaterials.DoubleStoneSlab = pocketMaterials[43, 0]
pocketMaterials.DoubleSandstoneSlab = pocketMaterials[43, 1]
pocketMaterials.DoubleWoodenSlab = pocketMaterials[43, 2]
pocketMaterials.DoubleCobblestoneSlab = pocketMaterials[43, 3]
pocketMaterials.DoubleBrickSlab = pocketMaterials[43, 4]
pocketMaterials.StoneSlab = pocketMaterials[44, 0]
pocketMaterials.SandstoneSlab = pocketMaterials[44, 1]
pocketMaterials.WoodenSlab = pocketMaterials[44, 2]
pocketMaterials.CobblestoneSlab = pocketMaterials[44, 3]
pocketMaterials.BrickSlab = pocketMaterials[44, 4]
pocketMaterials.Brick = pocketMaterials[45, 0]
pocketMaterials.TNT = pocketMaterials[46, 0]
pocketMaterials.Bookshelf = pocketMaterials[47, 0]
pocketMaterials.MossStone = pocketMaterials[48, 0]
pocketMaterials.Obsidian = pocketMaterials[49, 0]

pocketMaterials.Torch = pocketMaterials[50, 0]
pocketMaterials.Fire = pocketMaterials[51, 0]
pocketMaterials.WoodenStairs = pocketMaterials[53, 0]
pocketMaterials.Chest = pocketMaterials[54, 0]
pocketMaterials.DiamondOre = pocketMaterials[56, 0]
pocketMaterials.BlockofDiamond = pocketMaterials[57, 0]
pocketMaterials.CraftingTable = pocketMaterials[58, 0]
pocketMaterials.Crops = pocketMaterials[59, 0]
pocketMaterials.Farmland = pocketMaterials[60, 0]
pocketMaterials.Furnace = pocketMaterials[61, 0]
pocketMaterials.LitFurnace = pocketMaterials[62, 0]
pocketMaterials.WoodenDoor = pocketMaterials[64, 0]
pocketMaterials.Ladder = pocketMaterials[65, 0]
pocketMaterials.StoneStairs = pocketMaterials[67, 0]
pocketMaterials.IronDoor = pocketMaterials[71, 0]
pocketMaterials.RedstoneOre = pocketMaterials[73, 0]
pocketMaterials.RedstoneOreGlowing = pocketMaterials[74, 0]
pocketMaterials.SnowLayer = pocketMaterials[78, 0]
pocketMaterials.Ice = pocketMaterials[79, 0]

pocketMaterials.Snow = pocketMaterials[80, 0]
pocketMaterials.Cactus = pocketMaterials[81, 0]
pocketMaterials.Clay = pocketMaterials[82, 0]
pocketMaterials.SugarCane = pocketMaterials[83, 0]
pocketMaterials.Fence = pocketMaterials[85, 0]
pocketMaterials.Glowstone = pocketMaterials[89, 0]
pocketMaterials.InvisibleBedrock = pocketMaterials[95, 0]
pocketMaterials.Trapdoor = pocketMaterials[96, 0]

pocketMaterials.StoneBricks = pocketMaterials[98, 0]
pocketMaterials.GlassPane = pocketMaterials[102, 0]
pocketMaterials.Watermelon = pocketMaterials[103, 0]
pocketMaterials.MelonStem = pocketMaterials[105, 0]
pocketMaterials.FenceGate = pocketMaterials[107, 0]
pocketMaterials.BrickStairs = pocketMaterials[108, 0]

pocketMaterials.GlowingObsidian = pocketMaterials[246, 0]
pocketMaterials.NetherReactor = pocketMaterials[247, 0]
pocketMaterials.NetherReactorUsed = pocketMaterials[247, 1]

# print "\n".join(["pocketMaterials.{0} = pocketMaterials[{1},{2}]".format(
#                      b.name.replace(" ", "").replace("(","").replace(")",""),
#                      b.ID, b.blockData)
#                  for b in sorted(mats.pocketMaterials.allBlocks)])

_indices = rollaxis(indices((256, 16)), 0, 3)


def _filterTable(filters, unavailable, default=(0, 0)):
    # a filter table is a 256x16 table of (ID, data) pairs.
    table = zeros((256, 16, 2), dtype='uint8')
    table[:] = _indices
    for u in unavailable:
        try:
            if u[1] == 0:
                u = u[0]
        except TypeError:
            pass
        table[u] = default
    for f, t in filters:
        try:
            if f[1] == 0:
                f = f[0]
        except TypeError:
            pass
        table[f] = t
    return table

nullConversion = lambda b, d: (b, d)


def filterConversion(table):
    def convert(blocks, data):
        if data is None:
            data = 0
        t = table[blocks, data]
        return t[..., 0], t[..., 1]

    return convert


def guessFilterTable(matsFrom, matsTo):
    """ Returns a pair (filters, unavailable)
    filters is a list of (from, to) pairs;  from and to are (ID, data) pairs
    unavailable is a list of (ID, data) pairs in matsFrom not found in matsTo.

    Searches the 'name' and 'aka' fields to find matches.
    """
    filters = []
    unavailable = []
    toByName = dict(((b.name, b) for b in sorted(matsTo.allBlocks, reverse=True)))
    for fromBlock in matsFrom.allBlocks:
        block = toByName.get(fromBlock.name)
        if block is None:
            for b in matsTo.allBlocks:
                if b.name.startswith(fromBlock.name):
                    block = b
                    break
        if block is None:
            for b in matsTo.allBlocks:
                if fromBlock.name in b.name:
                    block = b
                    break
        if block is None:
            for b in matsTo.allBlocks:
                if fromBlock.name in b.aka:
                    block = b
                    break
        if block is None:
            if "Indigo Wool" == fromBlock.name:
                block = toByName.get("Purple Wool")
            elif "Violet Wool" == fromBlock.name:
                block = toByName.get("Purple Wool")

        if block:
            if block != fromBlock:
                filters.append(((fromBlock.ID, fromBlock.blockData), (block.ID, block.blockData)))
        else:
            unavailable.append((fromBlock.ID, fromBlock.blockData))

    return filters, unavailable

allMaterials = (alphaMaterials, classicMaterials, pocketMaterials, indevMaterials)

_conversionFuncs = {}


def conversionFunc(destMats, sourceMats):
    if destMats is sourceMats:
        return nullConversion
    func = _conversionFuncs.get((destMats, sourceMats))
    if func:
        return func

    filters, unavailable = guessFilterTable(sourceMats, destMats)
    log.debug("")
    log.debug("%s %s %s", sourceMats.name, "=>", destMats.name)
    for a, b in [(sourceMats.blockWithID(*a), destMats.blockWithID(*b)) for a, b in filters]:
        log.debug("{0:20}: \"{1}\"".format('"' + a.name + '"', b.name))

    log.debug("")
    log.debug("Missing blocks: %s", [sourceMats.blockWithID(*a).name for a in unavailable])

    table = _filterTable(filters, unavailable, (35, 0))
    func = filterConversion(table)
    _conversionFuncs[(destMats, sourceMats)] = func
    return func


def convertBlocks(destMats, sourceMats, blocks, blockData):
    if sourceMats == destMats:
        return blocks, blockData

    return conversionFunc(destMats, sourceMats)(blocks, blockData)

namedMaterials = dict((i.name, i) for i in allMaterials)

__all__ = "indevMaterials, pocketMaterials, alphaMaterials, classicMaterials, namedMaterials, MCMaterials".split(", ")
