# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QUrl  # To test network calls.
from PyQt5.QtNetwork import QNetworkAccessManager  # To test network calls.
import pytest  # For parametrized tests.
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

##  Test for handling the response of fetching user-subscribed packages.
#   \param toolbox An instance of Toolbox to test with from a fixture.
#   \param json_data The response JSON data given from the cloud.
@pytest.mark.parametrize("json_data, message_created", [
    ("""{"data": []}""", 0),  # No packages.
    ("""{"data": [{
        "description": "This is the best package ever created in the history of packages.",
        "display_name": "My Awesome Package",
        "download_url": "https://api.ultimaker.com/cura-packages/v1/cura/v6.0.0/packages/MyAwesomePackage/download",
        "icon_url": "https://ultimaker.com/img/favicons/favicon-32x32.png",
        "md5_hash": "Mt4rGzbghPMbXKodjlgeeQ==",
        "package_id": "MyAwesomePackage",
        "package_type": "plugin",
        "package_version": "1.0.0",
        "published_date": "2016-01-01T01:01:02.000Z",
        "sdk_versions": ["1.0.0"]
    }]}""", 1),  # The example from the API documentation.
    ("""{"data": [{
        "description": "The user didn't install this package yet.",
        "display_name": "Mysterious Package",
        "download_url": "https://i.imgur.com/aXlrTUi.jpg",
        "icon_url": "https://i.redd.it/3b1trwgles031.jpg",
        "md5_hash": "W40=c4R35",
        "package_id": "MysteriousPackage",
        "package_type": "plugin",
        "package_version": "1.0.0",
        "published_date": "2019-12-18T01:01:01.000Z",
        "sdk_versions": ["7.0.0"]
    }, {
        "description": "This package is already pre-installed.",
        "display_name": "Pre-installed Package",
        "download_url": "https://i.redd.it/0xfwp5ozkp341.jpg",
        "icon_url": "https://i.redd.it/y2w0jjswr9i31.jpg",
        "md5_hash": "H45H=M45H",
        "package_id": "Package1",
        "package_type": "material",
        "package_version": "1.0.0",
        "published_date": "2019-12-18T01:01:01.000Z",
        "sdk_versions": ["7.0.0"]
    }]}""", 1),  # One of the packages is already installed and is compatible.
    ("""{"data": [{
        "description": "The user didn't install this package yet.",
        "display_name": "Mysterious Package",
        "download_url": "https://i.imgur.com/aXlrTUi.jpg",
        "icon_url": "https://i.redd.it/3b1trwgles031.jpg",
        "md5_hash": "W40=c4R35",
        "package_id": "MysteriousPackage",
        "package_type": "plugin",
        "package_version": "1.0.0",
        "published_date": "2019-12-18T01:01:01.000Z",
        "sdk_versions": ["6.0.0"]
    }, {
        "description": "This package is already pre-installed.",
        "display_name": "Pre-installed Package",
        "download_url": "https://i.redd.it/0xfwp5ozkp341.jpg",
        "icon_url": "https://i.redd.it/y2w0jjswr9i31.jpg",
        "md5_hash": "H45H=M45H",
        "package_id": "Package1",
        "package_type": "material",
        "package_version": "1.0.1",
        "published_date": "2019-12-18T01:01:01.000Z",
        "sdk_versions": ["8.0.0"]
    }]}""", 1),  # One of the packages is already installed but both are incompatible.
    ("""{"data": [{
        "description": "This package is already pre-installed.",
        "display_name": "Pre-installed Package",
        "download_url": "https://i.redd.it/0xfwp5ozkp341.jpg",
        "icon_url": "https://i.redd.it/y2w0jjswr9i31.jpg",
        "md5_hash": "H45H=M45H",
        "package_id": "Package1",
        "package_type": "material",
        "package_version": "1.0.1",
        "published_date": "2019-12-18T01:01:01.000Z",
        "sdk_versions": ["7.0.0"]
    }]}""", 0),  # All subscribed packages are installed. The user has more packages.
    ("""{"data": [{
        "description": "First pre-installed and subscribed package.",
        "display_name": "Package 1",
        "download_url": "https://i.redd.it/kkq9vgnzbxo31.jpg",
        "icon_url": "https://i.redd.it/aa6qwbbhaq331.jpg",
        "md5_hash": "MD5",
        "package_id": "Package1",
        "package_type": "plugin",
        "package_version": "0.9.9",
        "published_date": "2019-12-19T01:01:01.000Z",
        "sdk_versions": ["7.0.0"]
    }, {
        "description": "Second pre-installed and subscribed package.",
        "display_name": "Package 2",
        "download_url": "https://i.redd.it/r0t7kaz907t11.jpg",
        "icon_url": "https://i.redd.it/12arbid24yy21.jpg",
        "md5_hash", "DM5",
        "package_id": "Package2",
        "package_type": "plugin",
        "package_version": "0.9.9",
        "published_date": "2019-12-19T01:01:01.000Z",
        "sdk_versions": ["7.0.0"]
    }]}""", 0)
])
def test_fetchUserSubscribedPackagesResponse(toolbox: "Toolbox", json_data: str, message_created: int):
    toolbox._package_manager.getUserInstalledPackagesAndVersions = MagicMock(return_value = [("Package1", "1.0.0"), ("Package2", "2.3.4")])

    # Mock the response we're giving to the fetch request.
    reply = MagicMock()
    reply.operation = lambda: QNetworkAccessManager.GetOperation
    reply.url = lambda: QUrl(toolbox._api_url_user_packages)
    reply.attribute = lambda _: 200  # Always use response code 200. We don't test failed requests here.
    reply.readAll = lambda: json_data.encode("utf-8")

    # Read out the message that was created.
    mock_message = MagicMock()

    with patch("src.Toolbox.Message", mock_message):
        toolbox._onRequestFinished(reply)

    assert mock_message().call_count == message_created