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


def test_getMaterialGroupListByGUID(application):
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
        manager = MaterialManager(mocked_registry)
    manager.initialize()

    assert manager.getMaterialGroupListByGUID("TEST!")[0].name == "test"
    assert manager.getMaterialGroupListByGUID("TEST2!")[0].name == "base_material"


def test_getRootMaterialIDforDiameter(application):
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
        manager = MaterialManager(mocked_registry)
    manager.initialize()

    assert manager.getRootMaterialIDForDiameter("base_material", "3") == "base_material"


def test_getMaterialNodeByTypeMachineHasNoMaterials(application):
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
        manager = MaterialManager(mocked_registry)
    manager.initialize()

    mocked_stack = MagicMock()
    assert manager.getMaterialNodeByType(mocked_stack, "0", "nozzle", "", "") is None


def test_getMaterialNodeByTypeMachineHasMaterialsButNoMaterialFound(application):
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
        manager = MaterialManager(mocked_registry)
    manager.initialize()

    mocked_stack = MagicMock()
    mocked_stack.definition.getMetaDataEntry = MagicMock(return_value = True)  # For the "has_materials" metadata

    assert manager.getMaterialNodeByType(mocked_stack, "0", "nozzle", "", "") is None


def test_getMaterialNodeByTypeMachineHasMaterialsAndMaterialExists(application):
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
        manager = MaterialManager(mocked_registry)
    manager.initialize()
    mocked_result = MagicMock()
    manager.getMaterialNode = MagicMock(return_value = mocked_result)
    mocked_stack = MagicMock()
    mocked_stack.definition.getMetaDataEntry = MagicMock(return_value = True)  # For the "has_materials" metadata

    assert manager.getMaterialNodeByType(mocked_stack, "0", "nozzle", "", "TEST!") is mocked_result


def test_getAllMaterialGroups(application):
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
        manager = MaterialManager(mocked_registry)
    manager.initialize()

    material_groups = manager.getAllMaterialGroups()

    assert "base_material" in material_groups
    assert "test" in material_groups
    assert material_groups["base_material"].name == "base_material"
    assert material_groups["test"].name == "test"


class TestAvailableMaterials:
    def test_happy(self, application):
        with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
            manager = MaterialManager(mocked_registry)
        manager.initialize()

        available_materials = manager.getAvailableMaterials(mocked_definition, None, None, 3)

        assert "base_material" in available_materials
        assert "test" in available_materials

    def test_wrongDiameter(self, application):
        with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
            manager = MaterialManager(mocked_registry)
        manager.initialize()

        available_materials = manager.getAvailableMaterials(mocked_definition, None, None, 200)
        assert available_materials == {} # Nothing found.

    def test_excludedMaterials(self, application):
        with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
            manager = MaterialManager(mocked_registry)
        manager.initialize()
        with patch.object(mocked_definition, "getMetaDataEntry", MagicMock(return_value = ["test"])):
            available_materials = manager.getAvailableMaterials(mocked_definition, None, None, 3)
        assert "base_material" in available_materials
        assert "test" not in available_materials


def test_getMaterialNode(application):
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
        manager = MaterialManager(mocked_registry)
    manager._updateMaps()

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