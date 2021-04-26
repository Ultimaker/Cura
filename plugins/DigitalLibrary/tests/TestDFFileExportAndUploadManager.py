from unittest.mock import MagicMock, patch

import pytest
from src.DFFileExportAndUploadManager import DFFileExportAndUploadManager


@pytest.fixture
def upload_manager():
    file_handler = MagicMock(name = "file_handler")
    node = MagicMock(name = "SceneNode")
    application = MagicMock(name = "CuraApplication")
    with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value=application)):
        return DFFileExportAndUploadManager(file_handlers = {"test": file_handler},
                                            nodes = [node],
                                            library_project_id = "test_library_project_id",
                                            library_project_name = "test_library_project_name",
                                            file_name = "file_name",
                                            formats = ["3mf"],
                                            on_upload_error = MagicMock(),
                                            on_upload_success = MagicMock(),
                                            on_upload_finished = MagicMock(),
                                            on_upload_progress = MagicMock())


@pytest.mark.parametrize("input,expected_result",
                        [("", ""),
                         ("invalid json! {}", ""),
                         ("{\"errors\": [{}]}", ""),
                         ("{\"errors\": [{\"title\": \"some title\"}]}", "some title")])
def test_extractErrorTitle(upload_manager, input, expected_result):
    assert upload_manager.extractErrorTitle(input) == expected_result

