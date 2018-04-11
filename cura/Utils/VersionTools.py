# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import re


# Regex for checking if a string is a semantic version number
_SEMANTIC_VERSION_REGEX = re.compile(r"^[0-9]+(.[0-9]+)+$")


# Checks if the given version string is a valid semantic version number.
def isSemanticVersion(version: str) -> bool:
    return _SEMANTIC_VERSION_REGEX.match(version) is not None


# Compares the two given semantic version strings and returns:
#   -1 if version1  < version2
#    0 if version1 == version2
#   +1 if version1  > version2
# Note that this function only works with semantic versions such as "a.b.c..."
def compareSemanticVersions(version1: str, version2: str) -> int:
    # Validate the version numbers first
    for version in (version1, version2):
        if not isSemanticVersion(version):
            raise ValueError("Invalid Package version '%s'" % version)

    # Split the version strings into lists of integers
    version1_parts = [int(p) for p in version1.split(".")]
    version2_parts = [int(p) for p in version2.split(".")]
    max_part_length = max(len(version1_parts), len(version2_parts))

    # Make sure that two versions have the same number of parts. For missing parts, just append 0s.
    for parts in (version1_parts, version2_parts):
        for _ in range(max_part_length - len(parts)):
            parts.append(0)

    # Compare the version parts and return the result
    result = 0
    for idx in range(max_part_length):
        result = version1_parts[idx] - version2_parts[idx]
        if result != 0:
            break
    return result
