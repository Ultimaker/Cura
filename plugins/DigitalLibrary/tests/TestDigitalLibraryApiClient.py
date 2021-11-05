# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from unittest.mock import MagicMock

import pytest

from cura.CuraApplication import CuraApplication
from src.DigitalFactoryApiClient import DigitalFactoryApiClient
from src.PaginationManager import PaginationManager


@pytest.fixture
def application():
    app = MagicMock(spec=CuraApplication, name = "Mocked Cura Application")
    return app


@pytest.fixture
def pagination_manager():
    manager = MagicMock(name = "Mocked Pagination Manager")
    return manager


@pytest.fixture
def api_client(application, pagination_manager):
    api_client = DigitalFactoryApiClient(application, MagicMock())
    api_client._projects_pagination_mgr = pagination_manager
    return api_client


def test_getProjectsFirstPage(api_client):
    # setup
    http_manager = MagicMock()
    api_client._http = http_manager
    pagination_manager = api_client._projects_pagination_mgr
    pagination_manager.limit = 20

    finished_callback = MagicMock()
    failed_callback = MagicMock()

    # Call
    api_client.getProjectsFirstPage(search_filter = "filter", on_finished = finished_callback, failed = failed_callback)

    # Asserts
    pagination_manager.reset.assert_called_once()  # Should be called since we asked for new set of projects
    http_manager.get.assert_called_once()
    args = http_manager.get.call_args_list[0]

    # Ensure that it's called with the right limit
    assert args[0][0] == "https://api.ultimaker.com/cura/v1/projects?limit=20&search=filter"

    # Change the limit & try again
    http_manager.get.reset_mock()
    pagination_manager.limit = 80
    api_client.getProjectsFirstPage(search_filter = "filter", on_finished = finished_callback, failed = failed_callback)
    args = http_manager.get.call_args_list[0]

    # Ensure that it's called with the right limit
    assert args[0][0] == "https://api.ultimaker.com/cura/v1/projects?limit=80&search=filter"


def test_getMoreProjects_noNewProjects(api_client):
    api_client.hasMoreProjectsToLoad = MagicMock(return_value = False)
    http_manager = MagicMock()
    api_client._http = http_manager

    finished_callback = MagicMock()
    failed_callback = MagicMock()
    api_client.getMoreProjects(finished_callback, failed_callback)

    http_manager.get.assert_not_called()


def test_getMoreProjects_hasNewProjects(api_client):
    api_client.hasMoreProjectsToLoad = MagicMock(return_value = True)
    http_manager = MagicMock()
    api_client._http = http_manager

    finished_callback = MagicMock()
    failed_callback = MagicMock()
    api_client.getMoreProjects(finished_callback, failed_callback)

    http_manager.get.assert_called_once()


def test_clear(api_client):
    api_client.clear()
    api_client._projects_pagination_mgr.reset.assert_called_once()
