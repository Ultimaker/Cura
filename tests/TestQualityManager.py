from unittest.mock import MagicMock

import pytest

from cura.Machines.QualityManager import QualityManager

mocked_stack = MagicMock()
mocked_extruder = MagicMock()

mocked_material = MagicMock()
mocked_material.getMetaDataEntry = MagicMock(return_value = "base_material")

mocked_extruder.material = mocked_material
mocked_stack.extruders = {"0": mocked_extruder}

@pytest.fixture()
def material_manager():
    result = MagicMock()
    result.getRootMaterialIDWithoutDiameter = MagicMock(return_value = "base_material")
    return result

@pytest.fixture()
def container_registry():
    result = MagicMock()
    mocked_metadata = [{"id": "test", "definition": "fdmprinter", "quality_type": "normal", "name": "test_name", "global_quality": True, "type": "quality"},
                       {"id": "test_material", "definition": "fdmprinter", "quality_type": "normal", "name": "test_name_material", "material": "base_material", "type": "quality"},
                       {"id": "quality_changes_id", "definition": "fdmprinter", "type": "quality_changes", "quality_type": "amazing!", "name": "herp"}]
    result.findContainersMetadata = MagicMock(return_value = mocked_metadata)
    return result


@pytest.fixture()
def quality_mocked_application(material_manager, container_registry):
    result = MagicMock()
    result.getMaterialManager = MagicMock(return_value=material_manager)
    result.getContainerRegistry = MagicMock(return_value=container_registry)
    return result


def test_getQualityGroups(quality_mocked_application):
    manager = QualityManager(quality_mocked_application)
    manager.initialize()

    assert "normal" in manager.getQualityGroups(mocked_stack)


def test_getQualityGroupsForMachineDefinition(quality_mocked_application):
    manager = QualityManager(quality_mocked_application)
    manager.initialize()

    assert "normal" in manager.getQualityGroupsForMachineDefinition(mocked_stack)


def test_getQualityChangesGroup(quality_mocked_application):
    manager = QualityManager(quality_mocked_application)
    manager.initialize()

    assert "herp" in manager.getQualityChangesGroups(mocked_stack)


def test_getDefaultQualityType(quality_mocked_application):
    manager = QualityManager(quality_mocked_application)
    manager.initialize()
    mocked_stack = MagicMock()
    mocked_stack.definition.getMetaDataEntry = MagicMock(return_value = "normal")
    assert manager.getDefaultQualityType(mocked_stack).quality_type == "normal"


    