# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

##  Creates a new profile instance by parsing a serialised profile in version 1
#   of the file format.
#
#   \param serialised The serialised form of a profile in version 1.
#   \return A profile instance, or None if the file format is incorrect.
def importVersion1(serialised):
    return None #Not implemented yet.

##  A representation of a profile used as intermediary form for conversion from
#   one format to the other.
class Profile:
    ##  Serialises this profile as file format version 2.
    #
    #   \return A serialised form of this profile, serialised in version 2 of
    #   the file format.
    def exportVersion2():
        raise Exception("Not implemented yet.")