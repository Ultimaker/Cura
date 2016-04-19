# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

##  Creates a new machine instance instance by parsing a serialised machine
#   instance in version 1 of the file format.
#
#   \param serialised The serialised form of a machine instance in version 1.
#   \return A machine instance instance, or None if the file format is
#   incorrect.
def importVersion1(serialised):
    return None #Not implemented yet.

##  A representation of a machine instance used as intermediary form for
#   conversion from one format to the other.
class MachineInstance:
    ##  Serialises this machine instance as file format version 2.
    #
    #   \return A serialised form of this machine instance, serialised in
    #   version 2 of the file format.
    def exportVersion2():
        raise Exception("Not implemented yet.")