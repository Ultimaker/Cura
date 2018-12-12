#
# This file contains all constant values in Cura
#

# -------------
# Cura Versions
# -------------
DEFAULT_CURA_DISPLAY_NAME = "Ultimaker Cura"
DEFAULT_CURA_VERSION = "master"
DEFAULT_CURA_BUILD_TYPE = ""
DEFAULT_CURA_DEBUG_MODE = False
DEFAULT_CURA_SDK_VERSION = "5.0.0"

try:
    from cura.CuraVersion import CuraAppDisplayName  # type: ignore
except ImportError:
    CuraAppDisplayName = DEFAULT_CURA_DISPLAY_NAME

try:
    from cura.CuraVersion import CuraVersion  # type: ignore
except ImportError:
    CuraVersion = DEFAULT_CURA_VERSION  # [CodeStyle: Reflecting imported value]

try:
    from cura.CuraVersion import CuraBuildType  # type: ignore
except ImportError:
    CuraBuildType = DEFAULT_CURA_BUILD_TYPE

try:
    from cura.CuraVersion import CuraDebugMode  # type: ignore
except ImportError:
    CuraDebugMode = DEFAULT_CURA_DEBUG_MODE

try:
    from cura.CuraVersion import CuraSDKVersion  # type: ignore
except ImportError:
    CuraSDKVersion = DEFAULT_CURA_SDK_VERSION


# ---------
# Cloud API
# ---------
DEFAULT_CLOUD_API_ROOT = "https://api.ultimaker.com"  # type: str
DEFAULT_CLOUD_API_VERSION = "1"  # type: str

try:
    from cura.CuraVersion import CuraCloudAPIRoot  # type: ignore
except ImportError:
    CuraCloudAPIRoot = DEFAULT_CLOUD_API_ROOT

try:
    from cura.CuraVersion import CuraCloudAPIVersion  # type: ignore
except ImportError:
    CuraCloudAPIVersion = DEFAULT_CLOUD_API_VERSION
