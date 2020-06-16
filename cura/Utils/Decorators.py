# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import functools
import re
from typing import Callable

# An API version must be a semantic version "x.y.z" where ".z" is optional. So the valid formats are as follows:
#  - x.y.z
#  - x.y
SEMANTIC_VERSION_REGEX = re.compile(r"^[0-9]+\.[0-9]+(\.[0-9]+)?$")


def api(since_version: str) -> Callable:
    """Decorator for functions that belong to a set of APIs. For now, this should only be used for officially supported

    APIs, meaning that those APIs should be versioned and maintained.

    :param since_version: The earliest version since when this API becomes supported. This means that since this version,
        this API function is supposed to behave the same. This parameter is not used. It's just a
        documentation.
    """
    # Make sure that APi versions are semantic versions
    if not SEMANTIC_VERSION_REGEX.fullmatch(since_version):
        raise ValueError("API since_version [%s] is not a semantic version." % since_version)

    def api_decorator(function):
        @functools.wraps(function)
        def api_wrapper(*args, **kwargs):
            return function(*args, **kwargs)
        return api_wrapper
    return api_decorator
