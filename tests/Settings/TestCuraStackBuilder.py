from unittest.mock import patch, MagicMock

import pytest

from UM.Settings.InstanceContainer import InstanceContainer
from cura.Machines.QualityGroup import QualityGroup
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
def intent_container():
    container = InstanceContainer(container_id="intent container")
    container.setMetaDataEntry("type", "intent")

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


def test_createMachine(application, container_registry, definition_container, global_variant, material_instance_container,
                       quality_container, intent_container, quality_changes_container):
    variant_manager = MagicMock(name = "Variant Manager")
    quality_manager = MagicMock(name = "Quality Manager")
    global_variant_node = MagicMock(name = "global variant node")
    global_variant_node.container = global_variant

    variant_manager.getDefaultVariantNode = MagicMock(return_value = global_variant_node)
    quality_group = QualityGroup(name = "zomg", quality_type = "normal")
    quality_group.node_for_global = MagicMock(name = "Node for global")
    quality_group.node_for_global.container = quality_container
    quality_manager.getQualityGroups = MagicMock(return_value = {"normal": quality_group})

    application.getContainerRegistry = MagicMock(return_value=container_registry)
    application.empty_material_container = material_instance_container
    application.empty_quality_container = quality_container
    application.empty_intent_container = intent_container
    application.empty_quality_changes_container = quality_changes_container
    application.empty_variant_container = global_variant

    metadata = definition_container.getMetaData()
    metadata["machine_extruder_trains"] = {}
    metadata["preferred_quality_type"] = "normal"

    container_registry.addContainer(definition_container)
    quality_node = MagicMock()
    machine_node = MagicMock()
    machine_node.preferredGlobalQuality = MagicMock(return_value = quality_node)
    quality_node.container = quality_container

    # Patch out the creation of MachineNodes since that isn't under test (and would require quite a bit of extra setup)
    with patch("cura.Machines.ContainerTree.MachineNode", MagicMock(return_value = machine_node)):
        with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value=application)):
            machine = CuraStackBuilder.createMachine("Whatever", "Test Definition")

            assert machine.quality == quality_container
            assert machine.definition == definition_container
            assert machine.variant == global_variant


def test_createExtruderStack(application, definition_container, global_variant, material_instance_container,
                             quality_container, intent_container, quality_changes_container):
    application.empty_material_container = material_instance_container
    application.empty_quality_container = quality_container
    application.empty_intent_container = intent_container
    application.empty_quality_changes_container = quality_changes_container
    with patch("cura.CuraApplication.CuraApplication.getInstance", MagicMock(return_value = application)):
        extruder_stack = CuraStackBuilder.createExtruderStack("Whatever", definition_container, "meh", 0,  global_variant, material_instance_container, quality_container)
        assert extruder_stack.variant == global_variant
        assert extruder_stack.material == material_instance_container
        assert extruder_stack.quality == quality_container