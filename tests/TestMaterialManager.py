from unittest.mock import MagicMock, patch

from cura.Machines.MaterialManager import MaterialManager


mocked_registry = MagicMock()
material_1 = {"id": "test", "GUID":"TEST!", "base_file": "base_material", "definition": "fdmmachine", "approximate_diameter": 3, "brand": "generic"}
material_2 = {"id": "base_material", "GUID": "TEST2!", "base_file": "test", "definition": "fdmmachine", "approximate_diameter": 3}
mocked_registry.findContainersMetadata = MagicMock(return_value = [material_1, material_2])


mocked_definition = MagicMock()
mocked_definition.getId = MagicMock(return_value = "fdmmachine")
mocked_definition.getMetaDataEntry = MagicMock(return_value = [])


def test_initialize(application):
    # Just test if the simple loading works
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
        manager = MaterialManager(mocked_registry)
    manager.initialize()
    # Double check that we actually got some material nodes
    assert manager.getMaterialGroup("base_material").name == "base_material"
    assert manager.getMaterialGroup("test").name == "test"


def test_getAvailableMaterials(application):
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
        manager = MaterialManager(mocked_registry)
    manager.initialize()

    available_materials = manager.getAvailableMaterials(mocked_definition, None, None, 3)

    assert "base_material" in available_materials
    assert "test" in available_materials


def test_getMaterialNode(application):
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
        manager = MaterialManager(mocked_registry)
    manager.initialize()

    assert manager.getMaterialNode("fdmmachine", None, None, 3, "base_material").getMetaDataEntry("id") == "test"


def test_getAvailableMaterialsForMachineExtruder(application):
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
        manager = MaterialManager(mocked_registry)
    manager.initialize()

    mocked_machine = MagicMock()
    mocked_machine.getBuildplateName = MagicMock(return_value = "build_plate")
    mocked_machine.definition = mocked_definition
    mocked_extruder_stack = MagicMock()
    mocked_extruder_stack.variant.getId = MagicMock(return_value = "test")
    mocked_extruder_stack.getApproximateMaterialDiameter = MagicMock(return_value = 2.85)

    available_materials = manager.getAvailableMaterialsForMachineExtruder(mocked_machine, mocked_extruder_stack)
    assert "base_material" in available_materials
    assert "test" in available_materials


class TestFavorites:
    def test_addFavorite(self, application):
        with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
            manager = MaterialManager(mocked_registry)
            manager.materialsUpdated = MagicMock()
            manager.addFavorite("blarg")
            assert manager.getFavorites() == {"blarg"}

            application.getPreferences().setValue.assert_called_once_with("cura/favorite_materials", "blarg")
            manager.materialsUpdated.emit.assert_called_once_with()

    def test_removeNotExistingFavorite(self, application):
        with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
            manager = MaterialManager(mocked_registry)
            manager.materialsUpdated = MagicMock()
            manager.removeFavorite("blarg")
            manager.materialsUpdated.emit.assert_not_called()

    def test_removeExistingFavorite(self, application):
        with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
            manager = MaterialManager(mocked_registry)
            manager.materialsUpdated = MagicMock()
            manager.addFavorite("blarg")

            manager.removeFavorite("blarg")
            assert manager.materialsUpdated.emit.call_count == 2
            application.getPreferences().setValue.assert_called_with("cura/favorite_materials", "")
            assert manager.getFavorites() == set()