# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

##  Creates a new preferences instance by parsing a serialised preferences file
#   in version 2 of the file format.
#
#   \param serialised The serialised form of a preferences file in version 2.
#   \return A preferences instance, or None if the file format is incorrect.
def importVersion2(serialised):
    return None #Not implemented yet.

##  A representation of a preferences file used as intermediary form for
#   conversion from one format to the other.
class Preferences:
    ##  Serialises this preferences file as file format version 3.
    #
    #   \return A serialised form of this preferences file, serialised in
    #   version 3 of the file format.
    def exportVersion3():
        raise Exception("Not implemented yet.")