# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

# ---------
# Constants used for the Cloud API
# ---------
DEFAULT_CLOUD_API_ROOT = "https://api.ultimaker.com"  # type: str
DEFAULT_CLOUD_API_VERSION = "1"  # type: str
DEFAULT_CLOUD_ACCOUNT_API_ROOT = "https://account.ultimaker.com"  # type: str

try:
    from cura.CuraVersion import CuraCloudAPIRoot  # type: ignore
    if CuraCloudAPIRoot == "":
        CuraCloudAPIRoot = DEFAULT_CLOUD_API_ROOT
except ImportError:
    CuraCloudAPIRoot = DEFAULT_CLOUD_API_ROOT

try:
    from cura.CuraVersion import CuraCloudAPIVersion  # type: ignore
    if CuraCloudAPIVersion == "":
        CuraCloudAPIVersion = DEFAULT_CLOUD_API_VERSION
except ImportError:
    CuraCloudAPIVersion = DEFAULT_CLOUD_API_VERSION

try:
    from cura.CuraVersion import CuraCloudAccountAPIRoot  # type: ignore
    if CuraCloudAccountAPIRoot == "":
        CuraCloudAccountAPIRoot = DEFAULT_CLOUD_ACCOUNT_API_ROOT
except ImportError:
    CuraCloudAccountAPIRoot = DEFAULT_CLOUD_ACCOUNT_API_ROOT
