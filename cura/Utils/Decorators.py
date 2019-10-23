# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import functools


##  Decorator for functions that belong to a set of APIs. For now, this should only be used for officially supported
#   APIs, meaning that those APIs should be versioned and maintained.
#
#   \param since The earliest version since when this API becomes supported. This means that since this version, this
#                API function is supposed to behave the same. This parameter is not used. It's just a documentation.
#
def api(since = "Unknown"):
    def api_decorator(function):
        @functools.wraps(function)
        def api_wrapper(*args, **kwargs):
            return function(*args, **kwargs)
        return api_wrapper
    return api_decorator
