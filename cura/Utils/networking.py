# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import socket


# Checks if the given string is a valid IPv4 address.
def isIPv4(address: str) -> bool:
    try:
        socket.inet_pton(socket.AF_INET, address)
        result = True
    except:
        result = False
    return result


# Checks if the given string is a valid IPv6 address.
def isIPv6(address: str) -> bool:
    try:
        socket.inet_pton(socket.AF_INET6, address)
        result = True
    except:
        result = False
    return result


# Checks if the given string is a valid IPv4 or IPv6 address.
def isValidIP(address: str) -> bool:
    return isIPv4(address) or isIPv6(address)


__all__ = ["isIPv4", "isIPv6", "isValidIP"]
