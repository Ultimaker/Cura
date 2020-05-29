# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os #To find the directory with test files and find the test files.
import pytest #To parameterize tests.
import unittest.mock #To mock and monkeypatch stuff.

from cura.ReaderWriters.ProfileReader import NoProfileException
from cura.Settings.ExtruderStack import ExtruderStack #Testing for returning the correct types of stacks.
from cura.Settings.GlobalStack import GlobalStack #Testing for returning the correct types of stacks.
import UM.Settings.InstanceContainer #Creating instance containers to register.
import UM.Settings.ContainerRegistry #Making empty container stacks.
import UM.Settings.ContainerStack #Setting the container registry here properly.
import cura.CuraApplication

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

    # The provided suggestion is already correct, so nothing to do
    assert container_registry.createUniqueName("user", "test", "test2 #2", "nope") == "test2 #2"

    # In case we don't provide a new name, use the fallback
    assert container_registry.createUniqueName("user", "test", "", "nope") == "nope"


def test_addContainerExtruderStack(container_registry, definition_container, definition_changes_container):
    """Tests whether addContainer properly converts to ExtruderStack."""

    container_registry.addContainer(definition_container)
    container_registry.addContainer(definition_changes_container)

    container_stack = ExtruderStack("Test Extruder Stack") #A container we're going to convert.
    container_stack.setMetaDataEntry("type", "extruder_train") #This is now an extruder train.
    container_stack.setDefinition(definition_container) #Add a definition to it so it doesn't complain.
    container_stack.setDefinitionChanges(definition_changes_container)

    mock_super_add_container = unittest.mock.MagicMock() #Takes the role of the Uranium-ContainerRegistry where the resulting containers get registered.
    with unittest.mock.patch("UM.Settings.ContainerRegistry.ContainerRegistry.addContainer", mock_super_add_container):
        container_registry.addContainer(container_stack)

    assert len(mock_super_add_container.call_args_list) == 1 #Called only once.
    assert len(mock_super_add_container.call_args_list[0][0]) == 1 #Called with one parameter.
    assert type(mock_super_add_container.call_args_list[0][0][0]) == ExtruderStack


def test_addContainerGlobalStack(container_registry, definition_container, definition_changes_container):
    """Tests whether addContainer properly converts to GlobalStack."""

    container_registry.addContainer(definition_container)
    container_registry.addContainer(definition_changes_container)

    container_stack = GlobalStack("Test Global Stack") #A container we're going to convert.
    container_stack.setMetaDataEntry("type", "machine") #This is now a global stack.
    container_stack.setDefinition(definition_container) #Must have a definition.
    container_stack.setDefinitionChanges(definition_changes_container) #Must have a definition changes.

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

test_loadMetaDataValidation_data = [
    {
        "id": "valid_container",
        "is_valid": True,
        "metadata": {
            "id": "valid_container",
            "setting_version": None, #The tests sets this to the current version so it's always correct.
            "foo": "bar"
        }
    },
    {
        "id": "wrong_setting_version",
        "is_valid": False,
        "metadata": {
            "id": "wrong_setting_version",
            "setting_version": "5",
            "foo": "bar"
        }
    },
    {
        "id": "missing_setting_version",
        "is_valid": False,
        "metadata": {
            "id": "missing_setting_version",
            "foo": "bar"
        }
    },
    {
        "id": "unparsable_setting_version",
        "is_valid": False,
        "metadata": {
            "id": "unparsable_setting_version",
            "setting_version": "Not an integer!",
            "foo": "bar"
        }
    }
]


@pytest.mark.parametrize("parameters", test_loadMetaDataValidation_data)
def test_loadMetadataValidation(container_registry, definition_container, parameters):
    from cura.CuraApplication import CuraApplication
    definition_container.getMetaData()["setting_version"] = CuraApplication.SettingVersion
    container_registry.addContainer(definition_container)
    if "setting_version" in parameters["metadata"] and parameters["metadata"]["setting_version"] is None: #Signal that the setting_version must be set to the currently correct version.
        parameters["metadata"]["setting_version"] = CuraApplication.SettingVersion

    mock_provider = unittest.mock.MagicMock()
    mock_provider.getAllIds = unittest.mock.MagicMock(return_value = [parameters["id"]])
    mock_provider.loadMetadata = unittest.mock.MagicMock(return_value = parameters["metadata"])
    container_registry._providers = [mock_provider]

    container_registry.loadAllMetadata() #Run the test.

    if parameters["is_valid"]:
        assert parameters["id"] in container_registry.metadata
        assert container_registry.metadata[parameters["id"]] == parameters["metadata"]
    else:
        assert parameters["id"] not in container_registry.metadata


class TestExportQualityProfile:
    # This class is just there to provide some grouping for the tests.
    def test_exportQualityProfileInvalidFileType(self, container_registry):
        # With an invalid file_type, we should get a false for success.
        assert not container_registry.exportQualityProfile([], "zomg", "invalid")

    def test_exportQualityProfileFailedWriter(self, container_registry):
        # Create a writer that always fails.
        mocked_writer = unittest.mock.MagicMock(name = "mocked_writer")
        mocked_writer.write = unittest.mock.MagicMock(return_value = False)
        container_registry._findProfileWriter = unittest.mock.MagicMock("findProfileWriter", return_value = mocked_writer)

        # Ensure that it actually fails if the writer did.
        with unittest.mock.patch("UM.Application.Application.getInstance"):
            assert not container_registry.exportQualityProfile([], "zomg", "test files (*.tst)")

    def test_exportQualityProfileExceptionWriter(self, container_registry):
        # Create a writer that always fails.
        mocked_writer = unittest.mock.MagicMock(name = "mocked_writer")
        mocked_writer.write = unittest.mock.MagicMock(return_value = True, side_effect = Exception("Failed :("))
        container_registry._findProfileWriter = unittest.mock.MagicMock("findProfileWriter", return_value = mocked_writer)

        # Ensure that it actually fails if the writer did.
        with unittest.mock.patch("UM.Application.Application.getInstance"):
            assert not container_registry.exportQualityProfile([], "zomg", "test files (*.tst)")

    def test_exportQualityProfileSuccessWriter(self, container_registry):
        # Create a writer that always fails.
        mocked_writer = unittest.mock.MagicMock(name="mocked_writer")
        mocked_writer.write = unittest.mock.MagicMock(return_value=True)
        container_registry._findProfileWriter = unittest.mock.MagicMock("findProfileWriter", return_value=mocked_writer)

        # Ensure that it actually fails if the writer did.
        with unittest.mock.patch("UM.Application.Application.getInstance"):
            assert container_registry.exportQualityProfile([], "zomg", "test files (*.tst)")


def test__findProfileWriterNoPlugins(container_registry):
    # Mock it so that no IO plugins are found.
    container_registry._getIOPlugins = unittest.mock.MagicMock(return_value = [])

    with unittest.mock.patch("UM.PluginRegistry.PluginRegistry.getInstance"):
        # Since there are no writers, don't return any
        assert container_registry._findProfileWriter(".zomg", "dunno") is None


def test__findProfileWriter(container_registry):
    # Mock it so that no IO plugins are found.
    container_registry._getIOPlugins = unittest.mock.MagicMock(return_value = [("writer_id", {"profile_writer": [{"extension": ".zomg", "description": "dunno"}]})])

    with unittest.mock.patch("UM.PluginRegistry.PluginRegistry.getInstance"):
        # In this case it's getting a mocked object (from the mocked_plugin_registry)
        assert container_registry._findProfileWriter(".zomg", "dunno") is not None


def test_importProfileEmptyFileName(container_registry):
    result = container_registry.importProfile("")
    assert result["status"] == "error"


mocked_application = unittest.mock.MagicMock(name = "application")
mocked_plugin_registry = unittest.mock.MagicMock(name="mocked_plugin_registry")

@unittest.mock.patch("UM.Application.Application.getInstance", unittest.mock.MagicMock(return_value = mocked_application))
@unittest.mock.patch("UM.PluginRegistry.PluginRegistry.getInstance", unittest.mock.MagicMock(return_value = mocked_plugin_registry))
class TestImportProfile:
    mocked_global_stack = unittest.mock.MagicMock(name="global stack")
    mocked_global_stack.extruders = {0: unittest.mock.MagicMock(name="extruder stack")}
    mocked_global_stack.getId = unittest.mock.MagicMock(return_value="blarg")
    mocked_profile_reader = unittest.mock.MagicMock()

    mocked_plugin_registry.getPluginObject = unittest.mock.MagicMock(return_value=mocked_profile_reader)

    def test_importProfileWithoutGlobalStack(self, container_registry):
        mocked_application.getGlobalContainerStack = unittest.mock.MagicMock(return_value = None)
        result = container_registry.importProfile("non_empty")
        assert result["status"] == "error"

    def test_importProfileNoProfileException(self, container_registry):
        container_registry._getIOPlugins = unittest.mock.MagicMock(return_value=[("reader_id", {"profile_reader": [{"extension": "zomg", "description": "dunno"}]})])
        mocked_application.getGlobalContainerStack = unittest.mock.MagicMock(return_value=self.mocked_global_stack)
        self.mocked_profile_reader.read = unittest.mock.MagicMock(side_effect = NoProfileException)
        result = container_registry.importProfile("test.zomg")
        # It's not an error, but we also didn't find any profile to read.
        assert result["status"] == "ok"

    def test_importProfileGenericException(self, container_registry):
        container_registry._getIOPlugins = unittest.mock.MagicMock(return_value=[("reader_id", {"profile_reader": [{"extension": "zomg", "description": "dunno"}]})])
        mocked_application.getGlobalContainerStack = unittest.mock.MagicMock(return_value=self.mocked_global_stack)
        self.mocked_profile_reader.read = unittest.mock.MagicMock(side_effect = Exception)
        result = container_registry.importProfile("test.zomg")
        assert result["status"] == "error"

    def test_importProfileNoDefinitionFound(self, container_registry):
        container_registry._getIOPlugins = unittest.mock.MagicMock(return_value=[("reader_id", {"profile_reader": [{"extension": "zomg", "description": "dunno"}]})])
        mocked_application.getGlobalContainerStack = unittest.mock.MagicMock(return_value=self.mocked_global_stack)
        container_registry.findDefinitionContainers = unittest.mock.MagicMock(return_value = [])
        mocked_profile = unittest.mock.MagicMock(name = "Mocked_global_profile")
        self.mocked_profile_reader.read = unittest.mock.MagicMock(return_value = [mocked_profile])

        result = container_registry.importProfile("test.zomg")
        assert result["status"] == "error"

    @pytest.mark.skip
    def test_importProfileSuccess(self, container_registry):
        container_registry._getIOPlugins = unittest.mock.MagicMock(return_value=[("reader_id", {"profile_reader": [{"extension": "zomg", "description": "dunno"}]})])

        mocked_application.getGlobalContainerStack = unittest.mock.MagicMock(return_value=self.mocked_global_stack)

        mocked_definition = unittest.mock.MagicMock(name = "definition")

        container_registry.findContainers = unittest.mock.MagicMock(return_value=[mocked_definition])
        container_registry.findDefinitionContainers = unittest.mock.MagicMock(return_value = [mocked_definition])
        mocked_profile = unittest.mock.MagicMock(name = "Mocked_global_profile")

        self.mocked_profile_reader.read = unittest.mock.MagicMock(return_value = [mocked_profile])
        with unittest.mock.patch.object(container_registry, "createUniqueName", return_value="derp"):
            with unittest.mock.patch.object(container_registry, "_configureProfile", return_value=None):
                result = container_registry.importProfile("test.zomg")

        assert result["status"] == "ok"


@pytest.mark.parametrize("metadata,result", [(None, False),
                                             ({}, False),
                                             ({"setting_version": cura.CuraApplication.CuraApplication.SettingVersion}, True),
                                             ({"setting_version": 0}, False)])
def test_isMetaDataValid(container_registry, metadata, result):
    assert container_registry._isMetadataValid(metadata) == result


def test_getIOPlugins(container_registry):
    plugin_registry = unittest.mock.MagicMock()
    plugin_registry.getActivePlugins = unittest.mock.MagicMock(return_value = ["lizard"])
    plugin_registry.getMetaData = unittest.mock.MagicMock(return_value = {"zomg": {"test": "test"}})
    with unittest.mock.patch("UM.PluginRegistry.PluginRegistry.getInstance", unittest.mock.MagicMock(return_value = plugin_registry)):
        assert container_registry._getIOPlugins("zomg") == [("lizard", {"zomg": {"test": "test"}})]