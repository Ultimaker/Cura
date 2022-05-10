#  Copyright (c) 2021 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.

from cura.UltimakerCloud import UltimakerCloudConstants
from cura.ApplicationMetadata import CuraSDKVersion

ROOT_URL = f"{UltimakerCloudConstants.CuraCloudAPIRoot}/cura-packages/v{UltimakerCloudConstants.CuraCloudAPIVersion}"
ROOT_CURA_URL = f"{ROOT_URL}/cura/v{CuraSDKVersion}"  # Root of all Marketplace API requests.
ROOT_USER_URL = f"{ROOT_URL}/user"
PACKAGES_URL = f"{ROOT_CURA_URL}/packages"  # URL to use for requesting the list of packages.
PACKAGE_UPDATES_URL = f"{PACKAGES_URL}/package-updates"  # URL to use for requesting the list of packages that can be updated.
USER_PACKAGES_URL = f"{ROOT_USER_URL}/packages"
