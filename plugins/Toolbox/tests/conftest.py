# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from unittest.mock import MagicMock, patch  # To mock away things outside of the plug-in.
import pytest  # To define fixtures for PyTest.

# Workaround for a race condition on certain systems where there
# is a race condition between Arcus and PyQt. Importing Arcus
# first seems to prevent Sip from going into a state where it
# tries to create PyQt objects on a non-main thread.
import Arcus #@UnusedImport
import Savitar #@UnusedImport

from src.Toolbox import Toolbox  # We define a fixture for this class.

##  Creates a Toolbox instance.
#
#   The instance is brought to the state after initialisation is completed.
#   Everything outside of the plug-in is mocked away.
@pytest.fixture
def toolbox():
    application = MagicMock()
    application_metadata = MagicMock(CuraSDKVersion = "1.2.3")
    ultimaker_cloud_authentication = MagicMock(CuraCloudAPIVersion = "1", CuraCloudAPIRoot = "**mocked_cloud_api_root**")
    with patch("cura.ApplicationMetadata", application_metadata):
        with patch("cura.UltimakerCloudAuthentication", ultimaker_cloud_authentication):
            inst = Toolbox(application)

    with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value = application)):
        with patch("PyQt5.QtNetwork.QNetworkAccessManager"):
            inst._onAppInitialized()

    return inst
