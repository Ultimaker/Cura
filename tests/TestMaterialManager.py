from unittest.mock import MagicMock, patch

from cura.Machines.MaterialManager import MaterialManager


mocked_registry = MagicMock()
material_1 = {"id": "test", "GUID":"TEST!", "base_file": "base_material", "definition": "fdmmachine", "approximate_diameter": 3}
material_2 = {"id": "base_material", "GUID":"TEST2!", "base_file": "test", "definition": "fdmmachine", "approximate_diameter": 3}
mocked_registry.findContainersMetadata = MagicMock(return_value = [material_1, material_2])

def test_initialize(application):
    # Just test if the simple loading works
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
        manager = MaterialManager(mocked_registry)
    manager.initialize()
    # Double check that we actually got some material nodes
    assert manager.getMaterialGroup("base_material").name == "base_material"
    assert manager.getMaterialGroup("test").name == "test"
