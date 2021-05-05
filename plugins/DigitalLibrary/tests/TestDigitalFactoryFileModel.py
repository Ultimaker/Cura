from pathlib import Path

from src.DigitalFactoryFileModel import DigitalFactoryFileModel
from src.DigitalFactoryFileResponse import DigitalFactoryFileResponse


file_1 = DigitalFactoryFileResponse(client_id = "client_id_1",
                                    content_type = "zomg",
                                    file_name = "file_1.3mf",
                                    file_id = "file_id_1",
                                    library_project_id = "project_id_1",
                                    status = "test",
                                    user_id = "user_id_1",
                                    username = "username_1",
                                    uploaded_at = "2021-04-07T10:33:25.000Z")

file_2 = DigitalFactoryFileResponse(client_id ="client_id_2",
                                    content_type = "zomg",
                                    file_name = "file_2.3mf",
                                    file_id = "file_id_2",
                                    library_project_id = "project_id_2",
                                    status = "test",
                                    user_id = "user_id_2",
                                    username = "username_2",
                                    uploaded_at = "2021-02-06T09:33:22.000Z")

file_wtf = DigitalFactoryFileResponse(client_id ="client_id_1",
                                      content_type = "zomg",
                                      file_name = "file_3.wtf",
                                      file_id = "file_id_3",
                                      library_project_id = "project_id_1",
                                      status = "test",
                                      user_id = "user_id_1",
                                      username = "username_1",
                                      uploaded_at = "2021-04-06T12:33:25.000Z")


def test_setFiles():
    model = DigitalFactoryFileModel()

    assert model.count == 0

    model.setFiles([file_1, file_2])
    assert model.count == 2

    assert model.getItem(0)["fileName"] == "file_1.3mf"
    assert model.getItem(1)["fileName"] == "file_2.3mf"


def test_clearProjects():
    model = DigitalFactoryFileModel()
    model.setFiles([file_1, file_2])
    model.clearFiles()
    assert model.count == 0


def test_setProjectMultipleTimes():
    model = DigitalFactoryFileModel()
    model.setFiles([file_1, file_2])
    model.setFiles([file_2])
    assert model.count == 1
    assert model.getItem(0)["fileName"] == "file_2.3mf"


def test_setFilter():
    model = DigitalFactoryFileModel()

    model.setFiles([file_1, file_2, file_wtf])
    model.setFilters({"file_name": lambda x: Path(x).suffix[1:].lower() in ["3mf"]})
    assert model.count == 2

    model.clearFilters()
    assert model.count == 3
