'''
Created on Jul 23, 2011

@author: Rio
'''
from math import isnan

import nbt
from copy import deepcopy

__all__ = ["Entity", "TileEntity"]

class TileEntity(object):
    baseStructures = {
        "Furnace": (
            ("BurnTime", nbt.TAG_Short),
            ("CookTime", nbt.TAG_Short),
            ("Items", nbt.TAG_List),
        ),
        "Sign": (
            ("Items", nbt.TAG_List),
        ),
        "MobSpawner": (
            ("Items", nbt.TAG_List),
        ),
        "Chest": (
            ("Items", nbt.TAG_List),
        ),
        "Music": (
            ("note", nbt.TAG_Byte),
        ),
        "Trap": (
            ("Items", nbt.TAG_List),
        ),
        "RecordPlayer": (
            ("Record", nbt.TAG_Int),
        ),
        "Piston": (
            ("blockId", nbt.TAG_Int),
            ("blockData", nbt.TAG_Int),
            ("facing", nbt.TAG_Int),
            ("progress", nbt.TAG_Float),
            ("extending", nbt.TAG_Byte),
        ),
        "Cauldron": (
            ("Items", nbt.TAG_List),
            ("BrewTime", nbt.TAG_Int),
        ),
    }

    knownIDs = baseStructures.keys()
    maxItems = {
        "Furnace": 3,
        "Chest": 27,
        "Trap": 9,
        "Cauldron": 4,
    }
    slotNames = {
        "Furnace": {
            0: "Raw",
            1: "Fuel",
            2: "Product"
        },
        "Cauldron": {
            0: "Potion",
            1: "Potion",
            2: "Potion",
            3: "Reagent",
        }
    }

    @classmethod
    def Create(cls, tileEntityID, **kw):
        tileEntityTag = nbt.TAG_Compound()
        tileEntityTag["id"] = nbt.TAG_String(tileEntityID)
        base = cls.baseStructures.get(tileEntityID, None)
        if base:
            for (name, tag) in base:
                tileEntityTag[name] = tag()

        cls.setpos(tileEntityTag, (0, 0, 0))
        return tileEntityTag

    @classmethod
    def pos(cls, tag):
        return [tag[a].value for a in 'xyz']

    @classmethod
    def setpos(cls, tag, pos):
        for a, p in zip('xyz', pos):
            tag[a] = nbt.TAG_Int(p)

    @classmethod
    def copyWithOffset(cls, tileEntity, copyOffset):
        eTag = deepcopy(tileEntity)
        eTag['x'] = nbt.TAG_Int(tileEntity['x'].value + copyOffset[0])
        eTag['y'] = nbt.TAG_Int(tileEntity['y'].value + copyOffset[1])
        eTag['z'] = nbt.TAG_Int(tileEntity['z'].value + copyOffset[2])
        return eTag


class Entity(object):
    monsters = ["Creeper",
                "Skeleton",
                "Spider",
                "CaveSpider",
                "Giant",
                "Zombie",
                "Slime",
                "PigZombie",
                "Ghast",
                "Pig",
                "Sheep",
                "Cow",
                "Chicken",
                "Squid",
                "Wolf",
                "Monster",
                "Enderman",
                "Silverfish",
                "Blaze",
                "Villager",
                "LavaSlime",
                "WitherBoss",
                ]
    projectiles = ["Arrow",
                   "Snowball",
                   "Egg",
                   "Fireball",
                   "SmallFireball",
                   "ThrownEnderpearl",
                   ]

    items = ["Item",
             "XPOrb",
             "Painting",
             "EnderCrystal",
             "ItemFrame",
             "WitherSkull",
             ]
    vehicles = ["Minecart", "Boat"]
    tiles = ["PrimedTnt", "FallingSand"]

    @classmethod
    def Create(cls, entityID, **kw):
        entityTag = nbt.TAG_Compound()
        entityTag["id"] = nbt.TAG_String(entityID)
        Entity.setpos(entityTag, (0, 0, 0))
        return entityTag

    @classmethod
    def pos(cls, tag):
        if "Pos" not in tag:
            raise InvalidEntity(tag)
        values = [a.value for a in tag["Pos"]]

        if isnan(values[0]) and 'xTile' in tag :
            values[0] = tag['xTile'].value
        if isnan(values[1]) and 'yTile' in tag:
            values[1] = tag['yTile'].value
        if isnan(values[2]) and 'zTile' in tag:
            values[2] = tag['zTile'].value

        return values

    @classmethod
    def setpos(cls, tag, pos):
        tag["Pos"] = nbt.TAG_List([nbt.TAG_Double(p) for p in pos])

    @classmethod
    def copyWithOffset(cls, entity, copyOffset):
        eTag = deepcopy(entity)

        positionTags = map(lambda p, co: nbt.TAG_Double(p.value + co), eTag["Pos"], copyOffset)
        eTag["Pos"] = nbt.TAG_List(positionTags)

        if eTag["id"].value in ("Painting", "ItemFrame"):
            eTag["TileX"].value += copyOffset[0]
            eTag["TileY"].value += copyOffset[1]
            eTag["TileZ"].value += copyOffset[2]

        return eTag


class InvalidEntity(ValueError):
    pass


class InvalidTileEntity(ValueError):
    pass
