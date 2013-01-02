Python library for reading Minecraft levels.

Can read Alpha levels, Indev levels, and Creative levels (with help).

Includes a command-line client (mce.py)

Requires numpy and PyYaml.

Read mclevel.py to get started.

See LICENSE.txt for licensing terms.



mce.py is a command-line editor for SMP maps. It can be used interactively from a terminal, accept editing commands on standard input, or run a single editing command from the shell.

Sample usage:

$ python mce.py

    Usage:

    Block commands:
        clone <sourcePoint> <sourceSize> <destPoint>
        fill <blockType> [ <point> <size> ]
        replace <blockType> [with] <newBlockType> [ <point> <size> ]

        export <filename> <sourcePoint> <sourceSize>
        import <filename> <destPoint>

        analyze

    Player commands:
        player [ <player> [ <point> ] ]
        spawn [ <point> ]

    Entity commands:
        removeEntities [ <EntityID> ]

    Chunk commands:
        createChunks <point> <size>
        deleteChunks <point> <size>
        prune <point> <size>
        relight [ <point> <size> ]

    World commands:
        degrief

    Editor commands:
        save
        reload
        load <filename> | <world number>
        quit

    Informational:
        blocks [ <block name> | <block ID> ]
        help [ <command> ]

    Points and sizes are space-separated triplets of numbers ordered X Y Z.
    X is position north-south, increasing southward.
    Y is position up-down, increasing upward.
    Z is position east-west, increasing westward.

    A player's name can be used as a point - it will use the
    position of the player's head. Use the keyword 'delta' after
    the name to specify a point near the player.

    Example:
       codewarrior delta 0 5 0

    This refers to a point 5 blocks above codewarrior's head.


Please enter world number or path to world folder: 4
INFO:Identifying C:\Users\Rio\AppData\Roaming\.minecraft\saves\World4\level.dat
INFO:Detected Infdev level.dat
INFO:Saved 0 chunks
INFO:Scanning for chunks...
INFO:Found 6288 chunks.
World4> fill 20 Player delta -10 0 -10 20 20 20

Filling with Glass
Filled 8000 blocks.
World4> player Player

Player Player: [87.658381289724858, 54.620000004768372, 358.64257283335115]
World4> player Player Player delta 0 25 0

Moved player Player to (87.658381289724858, 79.620000004768372, 358.642572833351
15)
World4> save

INFO:Asked to light 6 chunks
INFO:Batch 1/1
INFO:Lighting 20 chunks
INFO:Dispersing light...
INFO:BlockLight Pass 0: 20 chunks
INFO:BlockLight Pass 1: 2 chunks
INFO:BlockLight Pass 2: 0 chunks
INFO:BlockLight Pass 3: 0 chunks
INFO:BlockLight Pass 4: 0 chunks
INFO:BlockLight Pass 5: 0 chunks
INFO:BlockLight Pass 6: 0 chunks
INFO:BlockLight Pass 7: 0 chunks
INFO:BlockLight Pass 8: 0 chunks
INFO:BlockLight Pass 9: 0 chunks
INFO:BlockLight Pass 10: 0 chunks
INFO:BlockLight Pass 11: 0 chunks
INFO:BlockLight Pass 12: 0 chunks
INFO:BlockLight Pass 13: 0 chunks
INFO:SkyLight Pass 0: 20 chunks
INFO:SkyLight Pass 1: 22 chunks
INFO:SkyLight Pass 2: 17 chunks
INFO:SkyLight Pass 3: 9 chunks
INFO:SkyLight Pass 4: 7 chunks
INFO:SkyLight Pass 5: 2 chunks
INFO:SkyLight Pass 6: 0 chunks
INFO:SkyLight Pass 7: 0 chunks
INFO:SkyLight Pass 8: 0 chunks
INFO:SkyLight Pass 9: 0 chunks
INFO:SkyLight Pass 10: 0 chunks
INFO:SkyLight Pass 11: 0 chunks
INFO:SkyLight Pass 12: 0 chunks
INFO:SkyLight Pass 13: 0 chunks
INFO:Completed in 0:00:02.024000, 0:00:00.337333 per chunk
INFO:Saved 20 chunks
World4>
