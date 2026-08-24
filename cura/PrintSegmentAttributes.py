# Copyright (c) 2026 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from enum import IntFlag


class PrintSegmentAttributes(IntFlag):
    '''
    Print attributes are flags that can be added to some print segments to indicate that they have been processed
    a specific way, e.g. by using overhanging or bridging settings
    This enumeration has an equivalent in CuraEngine/include/PrintSegmentAttributes.h
    '''
    NoAttribute = 0
    Overhanging = 0x1
    Bridging = 0x2
