
from src.DigitalFactoryProjectModel import DigitalFactoryProjectModel
from src.DigitalFactoryProjectResponse import DigitalFactoryProjectResponse


project_1 = DigitalFactoryProjectResponse(library_project_id = "omg",
                                              display_name = "zomg",
                                              username = "nope",
                                              organization_shared = True)

project_2 = DigitalFactoryProjectResponse(library_project_id = "omg2",
                                              display_name = "zomg2",
                                              username = "nope",
                                              organization_shared = False)


def test_setProjects():
    model = DigitalFactoryProjectModel()

    assert model.count == 0

    model.setProjects([project_1, project_2])
    assert model.count == 2

    assert model.getItem(0)["displayName"] == "zomg"
    assert model.getItem(1)["displayName"] == "zomg2"


def test_clearProjects():
    model = DigitalFactoryProjectModel()
    model.setProjects([project_1, project_2])
    model.clearProjects()
    assert model.count == 0


def test_setProjectMultipleTimes():
    model = DigitalFactoryProjectModel()
    model.setProjects([project_1, project_2])
    model.setProjects([project_2])
    assert model.count == 1
    assert model.getItem(0)["displayName"] == "zomg2"


def test_extendProjects():
    model = DigitalFactoryProjectModel()

    assert model.count == 0

    model.setProjects([project_1])
    assert model.count == 1

    model.extendProjects([project_2])
    assert model.count == 2
    assert model.getItem(0)["displayName"] == "zomg"
    assert model.getItem(1)["displayName"] == "zomg2"
