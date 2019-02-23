# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os #To find the directory with test files and find the test files.
import unittest.mock #To mock and monkeypatch stuff.

from UM.Settings.DefinitionContainer import DefinitionContainer
from cura.Settings.ExtruderStack import ExtruderStack #Testing for returning the correct types of stacks.
from cura.Settings.GlobalStack import GlobalStack #Testing for returning the correct types of stacks.
import UM.Settings.InstanceContainer #Creating instance containers to register.
import UM.Settings.ContainerRegistry #Making empty container stacks.
import UM.Settings.ContainerStack #Setting the container registry here properly.


def teardown():
    #If the temporary file for the legacy file rename test still exists, remove it.
    temporary_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stacks", "temporary.stack.cfg")
    if os.path.isfile(temporary_file):
        os.remove(temporary_file)


def test_createUniqueName(container_registry):
    from cura.CuraApplication import CuraApplication


    assert container_registry.createUniqueName("user", "test", "test2", "nope") == "test2"

    # Make a conflict (so that "test2" will no longer be an unique name)
    instance = UM.Settings.InstanceContainer.InstanceContainer(container_id="test2")
    instance.setMetaDataEntry("type", "user")
    instance.setMetaDataEntry("setting_version", CuraApplication.SettingVersion)
    container_registry.addContainer(instance)

    # It should add a #2 to test2
    assert container_registry.createUniqueName("user", "test", "test2", "nope") == "test2 #2"


##  Tests whether addContainer properly converts to ExtruderStack.
def test_addContainerExtruderStack(container_registry, definition_container, definition_changes_container):
    container_registry.addContainer(definition_container)
    container_registry.addContainer(definition_changes_container)

    container_stack = UM.Settings.ContainerStack.ContainerStack(stack_id = "Test Extruder Stack") #A container we're going to convert.
    container_stack.setMetaDataEntry("type", "extruder_train") #This is now an extruder train.
    container_stack.insertContainer(0, definition_container) #Add a definition to it so it doesn't complain.
    container_stack.insertContainer(1, definition_changes_container)

    mock_super_add_container = unittest.mock.MagicMock() #Takes the role of the Uranium-ContainerRegistry where the resulting containers get registered.
    with unittest.mock.patch("UM.Settings.ContainerRegistry.ContainerRegistry.addContainer", mock_super_add_container):
        container_registry.addContainer(container_stack)

    assert len(mock_super_add_container.call_args_list) == 1 #Called only once.
    assert len(mock_super_add_container.call_args_list[0][0]) == 1 #Called with one parameter.
    assert type(mock_super_add_container.call_args_list[0][0][0]) == ExtruderStack


##  Tests whether addContainer properly converts to GlobalStack.
def test_addContainerGlobalStack(container_registry, definition_container, definition_changes_container):
    container_registry.addContainer(definition_container)
    container_registry.addContainer(definition_changes_container)

    container_stack = UM.Settings.ContainerStack.ContainerStack(stack_id = "Test Global Stack") #A container we're going to convert.
    container_stack.setMetaDataEntry("type", "machine") #This is now a global stack.
    container_stack.insertContainer(0, definition_container) #Must have a definition.
    container_stack.insertContainer(1, definition_changes_container) #Must have a definition changes.

    mock_super_add_container = unittest.mock.MagicMock() #Takes the role of the Uranium-ContainerRegistry where the resulting containers get registered.
    with unittest.mock.patch("UM.Settings.ContainerRegistry.ContainerRegistry.addContainer", mock_super_add_container):
        container_registry.addContainer(container_stack)

    assert len(mock_super_add_container.call_args_list) == 1 #Called only once.
    assert len(mock_super_add_container.call_args_list[0][0]) == 1 #Called with one parameter.
    assert type(mock_super_add_container.call_args_list[0][0][0]) == GlobalStack


def test_addContainerGoodSettingVersion(container_registry, definition_container):
    from cura.CuraApplication import CuraApplication
    definition_container.getMetaData()["setting_version"] = CuraApplication.SettingVersion
    container_registry.addContainer(definition_container)

    instance = UM.Settings.InstanceContainer.InstanceContainer(container_id = "Test Instance Right Version")
    instance.setMetaDataEntry("setting_version", CuraApplication.SettingVersion)
    instance.setDefinition(definition_container.getId())

    mock_super_add_container = unittest.mock.MagicMock() #Take the role of the Uranium-ContainerRegistry where the resulting containers get registered.
    with unittest.mock.patch("UM.Settings.ContainerRegistry.ContainerRegistry.addContainer", mock_super_add_container):
        container_registry.addContainer(instance)

    mock_super_add_container.assert_called_once_with(instance) #The instance must have been registered now.


def test_addContainerNoSettingVersion(container_registry, definition_container):
    from cura.CuraApplication import CuraApplication
    definition_container.getMetaData()["setting_version"] = CuraApplication.SettingVersion
    container_registry.addContainer(definition_container)

    instance = UM.Settings.InstanceContainer.InstanceContainer(container_id = "Test Instance No Version")
    #Don't add setting_version metadata.
    instance.setDefinition(definition_container.getId())

    mock_super_add_container = unittest.mock.MagicMock() #Take the role of the Uranium-ContainerRegistry where the resulting container should not get registered.
    with unittest.mock.patch("UM.Settings.ContainerRegistry.ContainerRegistry.addContainer", mock_super_add_container):
        container_registry.addContainer(instance)

    mock_super_add_container.assert_not_called() #Should not get passed on to UM.Settings.ContainerRegistry.addContainer, because the setting_version is interpreted as 0!


def test_addContainerBadSettingVersion(container_registry, definition_container):
    from cura.CuraApplication import CuraApplication
    definition_container.getMetaData()["setting_version"] = CuraApplication.SettingVersion
    container_registry.addContainer(definition_container)

    instance = UM.Settings.InstanceContainer.InstanceContainer(container_id = "Test Instance Wrong Version")
    instance.setMetaDataEntry("setting_version", 9001) #Wrong version!
    instance.setDefinition(definition_container.getId())

    mock_super_add_container = unittest.mock.MagicMock() #Take the role of the Uranium-ContainerRegistry where the resulting container should not get registered.
    with unittest.mock.patch("UM.Settings.ContainerRegistry.ContainerRegistry.addContainer", mock_super_add_container):
        container_registry.addContainer(instance)

    mock_super_add_container.assert_not_called() #Should not get passed on to UM.Settings.ContainerRegistry.addContainer, because the setting_version doesn't match its definition!
