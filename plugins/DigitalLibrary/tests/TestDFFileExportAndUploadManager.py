from unittest.mock import MagicMock, patch

import pytest
from src.DFFileExportAndUploadManager import DFFileExportAndUploadManager


@pytest.fixture
def upload_manager():
    file_handler = MagicMock(name = "file_handler")
    file_handler.getSupportedFileTypesWrite = MagicMock(return_value = [{
                    "id": "test",
                    "extension": ".3mf",
                    "description": "nope",
                    "mime_type": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml",
                    "mode": "binary",
                    "hide_in_file_dialog": True,
                }])
    node = MagicMock(name = "SceneNode")
    application = MagicMock(name = "CuraApplication")
    with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value = application)):
        return DFFileExportAndUploadManager(file_handlers = {"3mf": file_handler},
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


def test_exportJobError(upload_manager):
    mocked_application = MagicMock()
    with patch("UM.Application.Application.getInstance", MagicMock(return_value = mocked_application)):
        upload_manager._onJobExportError("file_name.3mf")

    # Ensure that message was displayed
    mocked_application.showMessageSignal.emit.assert_called_once()
