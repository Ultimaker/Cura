# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QUrl  # To test network calls.
from unittest.mock import MagicMock, patch  # To mock away dependencies.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.Toolbox import Toolbox

##  Integration test for querying which packages the user is subscribed to.
#   \param toolbox An instance of Toolbox to test with from a fixture.
def test_fetchUserSubscribedPackages(toolbox: "Toolbox"):
    # Test making a request.
    network_manager = MagicMock()
    with patch("src.Toolbox.QNetworkAccessManager", network_manager):
        toolbox._fetchUserSubscribedPackages()  # The actual call to test.

    network_manager().get.assert_called_once()  # Only make one request: To fetch the subscribed packages.
    request = network_manager().get.call_args[0][0]
    assert request.url() == QUrl(toolbox._api_url_user_packages)  # It needs to be a request to the correct URL.
    for name, value in toolbox._request_headers:  # And all of the headers.
        assert request.hasRawHeader(name)
        assert request.rawHeader(name) == value

    assert False  # DEBUG