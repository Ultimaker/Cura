# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.


##  Raised when trying to perform an operation like add on a stack that does not allow that.
class InvalidOperationError(Exception):
    pass


##  Raised when trying to replace a container with a container that does not have the expected type.
class InvalidContainerError(Exception):
    pass


##  Raised when trying to add an extruder to a Global stack that already has the maximum number of extruders.
class TooManyExtrudersError(Exception):
    pass


##  Raised when an extruder has no next stack set.
class NoGlobalStackError(Exception):
    pass
