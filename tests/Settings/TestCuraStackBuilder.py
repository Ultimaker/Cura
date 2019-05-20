from unittest.mock import patch, MagicMock

import pytest

from UM.Settings.InstanceContainer import InstanceContainer
from cura.Settings.CuraStackBuilder import CuraStackBuilder

@pytest.fixture
def global_variant():
    container = InstanceContainer(container_id="global_variant")
    container.setMetaDataEntry("type", "variant")

    return container

@pytest.fixture
def material_instance_container():
    container = InstanceContainer(container_id="material container")
    container.setMetaDataEntry("type", "material")

    return container

@pytest.fixture
def quality_container():
    container = InstanceContainer(container_id="quality container")
    container.setMetaDataEntry("type", "quality")

    return container


@pytest.fixture
def quality_changes_container():
    container = InstanceContainer(container_id="quality changes container")
    container.setMetaDataEntry("type", "quality_changes")

    return container


def test_createMachineWithUnknownDefinition(application, container_registry):
    application.getContainerRegistry = MagicMock(return_value=container_registry)
    with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value=application)):
        with patch("UM.ConfigurationErrorMessage.ConfigurationErrorMessage.getInstance") as mocked_config_error:
            assert CuraStackBuilder.createMachine("Whatever", "NOPE") is None
            assert mocked_config_error.addFaultyContainers.called_with("NOPE")


'''def test_createMachine(application, container_registry, definition_container, global_variant, material_instance_container, quality_container, quality_changes_container):
    variant_manager = MagicMock(name = "Variant Manager")
    global_variant_node = MagicMock( name = "global variant node")
    global_variant_node.getContainer = MagicMock(return_value = global_variant)

    variant_manager.getDefaultVariantNode = MagicMock(return_value = global_variant_node)

    application.getContainerRegistry = MagicMock(return_value=container_registry)
    application.getVariantManager = MagicMock(return_value = variant_manager)
    application.empty_material_container = material_instance_container
    application.empty_quality_container = quality_container
    application.empty_quality_changes_container = quality_changes_container

    definition_container.getMetaDataEntry = MagicMock(return_value = {}, name = "blarg")
    print("DEF CONT", definition_container)
    container_registry.addContainer(definition_container)
    with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value=application)):
        assert CuraStackBuilder.createMachine("Whatever", "Test Definition") is None'''
