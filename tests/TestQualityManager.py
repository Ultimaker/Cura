from unittest.mock import MagicMock, patch

import pytest

from cura.Machines.QualityChangesGroup import QualityChangesGroup
from cura.Machines.QualityManager import QualityManager

mocked_stack = MagicMock()
mocked_extruder = MagicMock()

mocked_material = MagicMock()
mocked_material.getMetaDataEntry = MagicMock(return_value = "base_material")

mocked_extruder.material = mocked_material
mocked_stack.extruders = {"0": mocked_extruder}

# These tests are outdated
pytestmark = pytest.mark.skip

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

    result.uniqueName = MagicMock(return_value = "uniqueName")
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


def test_getQualityChangesGroup(quality_mocked_application):
    manager = QualityManager(quality_mocked_application)
    manager.initialize()

    assert "herp" in [qcg.name for qcg in manager.getQualityChangesGroups(mocked_stack)]


@pytest.mark.skip("Doesn't work on remote")
def test_getDefaultQualityType(quality_mocked_application):
    manager = QualityManager(quality_mocked_application)
    manager.initialize()
    mocked_stack = MagicMock()
    mocked_stack.definition.getMetaDataEntry = MagicMock(return_value = "normal")
    assert manager.getDefaultQualityType(mocked_stack).quality_type == "normal"


def test_createQualityChanges(quality_mocked_application):
    manager = QualityManager(quality_mocked_application)
    mocked_quality_changes = MagicMock()
    manager._createQualityChanges = MagicMock(return_value = mocked_quality_changes)
    manager.initialize()
    container_manager = MagicMock()

    manager._container_registry.addContainer = MagicMock()  # Side effect we want to check.
    with patch("cura.Settings.ContainerManager.ContainerManager.getInstance", container_manager):
        manager.createQualityChanges("derp")
        assert manager._container_registry.addContainer.called_once_with(mocked_quality_changes)


def test_renameQualityChangesGroup(quality_mocked_application):
    manager = QualityManager(quality_mocked_application)
    manager.initialize()

    mocked_container = MagicMock()

    quality_changes_group = QualityChangesGroup("zomg", "beep")
    quality_changes_group.getAllNodes = MagicMock(return_value = [mocked_container])

    # We need to check for "uniqueName" instead of "NEWRANDOMNAMEYAY" because the mocked registry always returns
    # "uniqueName" when attempting to generate an unique name.
    assert manager.renameQualityChangesGroup(quality_changes_group, "NEWRANDOMNAMEYAY") == "uniqueName"
    assert mocked_container.setName.called_once_with("uniqueName")


def test_duplicateQualityChangesQualityOnly(quality_mocked_application):
    manager = QualityManager(quality_mocked_application)
    manager.initialize()
    mocked_quality = MagicMock()
    quality_group = MagicMock()
    quality_group.getAllNodes = MagicMock(return_value = mocked_quality)
    mocked_quality_changes = MagicMock()

    # Isolate what we want to test (in this case, we're not interested if createQualityChanges does it's job!)
    manager._createQualityChanges = MagicMock(return_value = mocked_quality_changes)
    manager._container_registry.addContainer = MagicMock()  # Side effect we want to check.

    manager.duplicateQualityChanges("zomg", {"quality_group": quality_group, "quality_changes_group": None})
    assert manager._container_registry.addContainer.called_once_with(mocked_quality_changes)


def test_duplicateQualityChanges(quality_mocked_application):
    manager = QualityManager(quality_mocked_application)
    manager.initialize()
    mocked_quality = MagicMock()
    quality_group = MagicMock()
    quality_group.getAllNodes = MagicMock(return_value = mocked_quality)
    quality_changes_group = MagicMock()
    mocked_quality_changes = MagicMock()
    quality_changes_group.getAllNodes = MagicMock(return_value=[mocked_quality_changes])
    mocked_quality_changes.duplicate = MagicMock(return_value = mocked_quality_changes)

    manager._container_registry.addContainer = MagicMock()  # Side effect we want to check.

    manager.duplicateQualityChanges("zomg", {"quality_group": quality_group, "quality_changes_group": quality_changes_group})
    assert manager._container_registry.addContainer.called_once_with(mocked_quality_changes)