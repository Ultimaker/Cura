import functools
from unittest.mock import MagicMock, patch, PropertyMock
import pytest

from cura.Settings.MachineManager import MachineManager


def createMockedStack(stack_id: str, name: str):
    stack = MagicMock(name=name)
    stack.getId = MagicMock(return_value=stack_id)
    return stack


def getPropertyMocked(setting_key, setting_property, settings_dict):
    """
    Mocks the getProperty function of containers so that it returns the setting values needed for a test.

    Use this function as follows:
    container.getProperty = functools.partial(getPropertyMocked, settings_dict = {"print_sequence": "one_at_a_time"})

    :param setting_key: The key of the setting to be returned (e.g. "print_sequence", "infill_sparse_density" etc)
    :param setting_property: The setting property (usually "value")
    :param settings_dict: All the settings and their values expected to be returned by this mocked function
    :return: The mocked setting value specified by the settings_dict
    """
    if setting_property == "value":
        return settings_dict.get(setting_key)
    return None


@pytest.fixture()
def global_stack():
    return createMockedStack("GlobalStack", "Global Stack")


@pytest.fixture()
def machine_manager(application, extruder_manager, container_registry, global_stack) -> MachineManager:
    application.getExtruderManager = MagicMock(return_value = extruder_manager)
    application.getGlobalContainerStack = MagicMock(return_value = global_stack)
    with patch("cura.Settings.CuraContainerRegistry.CuraContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
        manager = MachineManager(application)
        with patch.object(MachineManager, "updateNumberExtrudersEnabled", return_value = None):
            manager._onGlobalContainerChanged()

    return manager


def test_getMachine():
    registry = MagicMock()
    mocked_global_stack = MagicMock()
    mocked_global_stack.getId = MagicMock(return_value="test_machine")
    mocked_global_stack.definition.getId = MagicMock(return_value = "test")
    registry.findContainerStacks = MagicMock(return_value=[mocked_global_stack])
    with patch("cura.Settings.CuraContainerRegistry.CuraContainerRegistry.getInstance", MagicMock(return_value=registry)):
        assert MachineManager.getMachine("test") == mocked_global_stack
        # Since only test is in the registry, this should be None
        assert MachineManager.getMachine("UnknownMachine") is None


def test_addMachine(machine_manager):
    registry = MagicMock()

    mocked_stack = MagicMock()
    mocked_stack.getId = MagicMock(return_value="newlyCreatedStack")
    mocked_create_machine = MagicMock(name="createMachine", return_value = mocked_stack)
    machine_manager.setActiveMachine = MagicMock()
    with patch("cura.Settings.CuraStackBuilder.CuraStackBuilder.createMachine", mocked_create_machine):
        with patch("cura.Settings.CuraContainerRegistry.CuraContainerRegistry.getInstance", MagicMock(return_value=registry)):
            machine_manager.addMachine("derp")
    machine_manager.setActiveMachine.assert_called_with("newlyCreatedStack")


def test_hasUserSettings(machine_manager, application):
    mocked_stack = application.getGlobalContainerStack()

    mocked_instance_container = MagicMock(name="UserSettingContainer")
    mocked_instance_container.getNumInstances = MagicMock(return_value = 12)
    mocked_stack.getTop = MagicMock(return_value = mocked_instance_container)
    machine_manager._reCalculateNumUserSettings()
    assert machine_manager.numUserSettings == 12
    assert machine_manager.hasUserSettings


def test_hasUserSettingsExtruder(machine_manager, application):
    mocked_stack = application.getGlobalContainerStack()
    extruder = createMockedExtruder("extruder")

    mocked_instance_container_global = MagicMock(name="UserSettingContainerGlobal")
    mocked_instance_container_global.getNumInstances = MagicMock(return_value=0)
    mocked_stack.getTop = MagicMock(return_value=mocked_instance_container_global)
    mocked_stack.extruderList = [extruder]

    mocked_instance_container = MagicMock(name="UserSettingContainer")
    mocked_instance_container.getNumInstances = MagicMock(return_value=200)
    extruder.getTop = MagicMock(return_value = mocked_instance_container)
    machine_manager._reCalculateNumUserSettings()
    assert machine_manager.hasUserSettings
    assert machine_manager.numUserSettings == 200


def test_hasUserSettingsEmptyUserChanges(machine_manager, application):
    mocked_stack = application.getGlobalContainerStack()
    extruder = createMockedExtruder("extruder")

    mocked_instance_container_global = MagicMock(name="UserSettingContainerGlobal")
    mocked_instance_container_global.getNumInstances = MagicMock(return_value=0)
    mocked_stack.getTop = MagicMock(return_value=mocked_instance_container_global)
    mocked_stack.extruderList = [extruder]

    mocked_instance_container = MagicMock(name="UserSettingContainer")
    mocked_instance_container.getNumInstances = MagicMock(return_value=0)
    extruder.getTop = MagicMock(return_value = mocked_instance_container)
    machine_manager._reCalculateNumUserSettings()
    assert not machine_manager.hasUserSettings


def test_totalNumberOfSettings(machine_manager):
    registry = MagicMock()
    mocked_definition = MagicMock()
    mocked_definition.getAllKeys = MagicMock(return_value = ["omg", "zomg", "foo"])
    registry.findDefinitionContainers = MagicMock(return_value = [mocked_definition])
    with patch("cura.Settings.CuraContainerRegistry.CuraContainerRegistry.getInstance", MagicMock(return_value=registry)):
        assert machine_manager.totalNumberOfSettings == 3


def createMockedExtruder(extruder_id):
    extruder = MagicMock()
    extruder.getId = MagicMock(return_value = extruder_id)
    return extruder


def createMockedInstanceContainer(instance_id, name = ""):
    instance = MagicMock()
    instance.getName = MagicMock(return_value = name)
    instance.getId = MagicMock(return_value=instance_id)
    return instance


def test_globalVariantName(machine_manager, application):
    global_stack = application.getGlobalContainerStack()
    global_stack.variant = createMockedInstanceContainer("beep", "zomg")
    assert machine_manager.globalVariantName == "zomg"


def test_resetSettingForAllExtruders(machine_manager):
    global_stack = machine_manager.activeMachine
    extruder_1 = createMockedExtruder("extruder_1")
    extruder_2 = createMockedExtruder("extruder_2")
    extruder_1.userChanges = createMockedInstanceContainer("settings_1")
    extruder_2.userChanges = createMockedInstanceContainer("settings_2")
    global_stack.extruderList = [extruder_1, extruder_2]

    machine_manager.resetSettingForAllExtruders("whatever")

    extruder_1.userChanges.removeInstance.assert_called_once_with("whatever")
    extruder_2.userChanges.removeInstance.assert_called_once_with("whatever")


def test_setUnknownActiveMachine(machine_manager):
    machine_action_manager = MagicMock()
    machine_manager.getMachineActionManager = MagicMock(return_value = machine_action_manager)

    machine_manager.setActiveMachine("UnknownMachine")
    # The machine isn't known to us, so this should not happen!
    machine_action_manager.addDefaultMachineActions.assert_not_called()


def test_clearActiveMachine(machine_manager):
    machine_manager.setActiveMachine(None)

    machine_manager._application.setGlobalContainerStack.assert_called_once_with(None)


def test_setActiveMachine(machine_manager):
    registry = MagicMock()
    machine_action_manager = MagicMock()
    machine_manager._validateVariantsAndMaterials = MagicMock()  # Not testing that function, so whatever.
    machine_manager._application.getMachineActionManager = MagicMock(return_value=machine_action_manager)
    global_stack = createMockedStack("NewMachine", "Newly created Machine")

    # Ensure that the container stack will be found
    registry.findContainerStacks = MagicMock(return_value = [global_stack])
    with patch("cura.Settings.CuraContainerRegistry.CuraContainerRegistry.getInstance", MagicMock(return_value=registry)):
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=registry)):
            with patch("cura.Settings.ExtruderManager.ExtruderManager.getInstance"):  # Prevent the FixSingleExtruder from being called
                machine_manager.setActiveMachine("NewMachine")

    machine_action_manager.addDefaultMachineActions.assert_called_once_with(global_stack)
    # Yeah sure. It's technically an implementation detail. But if this function wasn't called, it exited early somehow
    machine_manager._validateVariantsAndMaterials.assert_called_once_with(global_stack)


def test_setInvalidActiveMachine(machine_manager):
    registry = MagicMock()
    global_stack = createMockedStack("InvalidMachine", "Newly created Machine")

    # This machine is just plain wrong!
    global_stack.isValid = MagicMock(return_value = False)

    # Ensure that the container stack will be found
    registry.findContainerStacks = MagicMock(return_value=[global_stack])

    configuration_error_message = MagicMock()

    with patch("cura.Settings.CuraContainerRegistry.CuraContainerRegistry.getInstance", MagicMock(return_value=registry)):
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=registry)):
            with patch("cura.Settings.ExtruderManager.ExtruderManager.getInstance"):  # Prevent the FixSingleExtruder from being called
                with patch("UM.ConfigurationErrorMessage.ConfigurationErrorMessage.getInstance", MagicMock(return_value = configuration_error_message)):
                    machine_manager.setActiveMachine("InvalidMachine")

    # Notification stuff should happen now!
    configuration_error_message.addFaultyContainers.assert_called_once_with("InvalidMachine")


def test_clearUserSettingsAllCurrentStacks(machine_manager, application):
    global_stack = application.getGlobalContainerStack()
    extruder_1 = createMockedExtruder("extruder_1")
    instance_container = createMockedInstanceContainer("user", "UserContainer")
    extruder_1.getTop = MagicMock(return_value = instance_container)
    global_stack.extruderList = [extruder_1]

    machine_manager.clearUserSettingAllCurrentStacks("some_setting")

    instance_container.removeInstance.assert_called_once_with("some_setting", postpone_emit=True)


def test_clearUserSettingsAllCurrentStacksLinkedSetting(machine_manager, application):
    global_stack = application.getGlobalContainerStack()
    extruder_1 = createMockedExtruder("extruder_1")
    instance_container = createMockedInstanceContainer("user", "UserContainer")
    instance_container_global = createMockedInstanceContainer("global_user", "GlobalUserContainer")
    global_stack.getTop = MagicMock(return_value = instance_container_global)
    extruder_1.getTop = MagicMock(return_value=instance_container)
    global_stack.extruderList = [extruder_1]

    global_stack.getProperty = MagicMock(side_effect = lambda key, prop: True if prop == "settable_per_extruder" else "-1" )

    machine_manager.clearUserSettingAllCurrentStacks("some_setting")

    instance_container.removeInstance.assert_not_called()
    instance_container_global.removeInstance.assert_called_once_with("some_setting", postpone_emit = True)


def test_isActiveQualityExperimental(machine_manager):
    quality_group = MagicMock(is_experimental = True)
    machine_manager.activeQualityGroup = MagicMock(return_value = quality_group)
    assert machine_manager.isActiveQualityExperimental
    
    
def test_isActiveQualityNotExperimental(machine_manager):
    quality_group = MagicMock(is_experimental = False)
    machine_manager.activeQualityGroup = MagicMock(return_value = quality_group)
    assert not machine_manager.isActiveQualityExperimental


def test_isActiveQualityNotExperimental_noQualityGroup(machine_manager):
    machine_manager.activeQualityGroup = MagicMock(return_value=None)
    assert not machine_manager.isActiveQualityExperimental


def test_isActiveQualitySupported(machine_manager):
    quality_group = MagicMock(is_available=True)
    machine_manager.activeQualityGroup = MagicMock(return_value=quality_group)
    assert machine_manager.isActiveQualitySupported


def test_isActiveQualityNotSupported(machine_manager):
    quality_group = MagicMock(is_available=False)
    machine_manager.activeQualityGroup = MagicMock(return_value=quality_group)
    assert not machine_manager.isActiveQualitySupported


def test_isActiveQualityNotSupported_noQualityGroup(machine_manager):
    machine_manager.activeQualityGroup = MagicMock(return_value=None)
    assert not machine_manager.isActiveQualitySupported


def test_correctPrintSequence_globalStackHasAllAtOnce(machine_manager, application):

    # Global container stack already has all_at_once
    mocked_stack = application.getGlobalContainerStack()
    mocked_global_settings = {"print_sequence": "all_at_once"}
    mocked_stack.getProperty = functools.partial(getPropertyMocked, settings_dict=mocked_global_settings)

    mocked_user_changes_container = MagicMock(name="UserChangesContainer")
    mocked_stack.userChanges = mocked_user_changes_container

    machine_manager.correctPrintSequence()

    # After the function is called, the user changes container should not have tried to change any properties
    assert not mocked_user_changes_container.setProperty.called, "The Print Sequence should not be attempted to be changed when it is already 'all-at-once'"


def test_correctPrintSequence_OneEnabledExtruder(machine_manager, application):
    # Global container stack reports print sequence as one_at_a_time
    mocked_stack = application.getGlobalContainerStack()
    mocked_global_settings = {"print_sequence": "one_at_a_time"}
    mocked_stack.getProperty = functools.partial(getPropertyMocked, settings_dict=mocked_global_settings)

    # The definition changes container reports 1 enabled extruders, so the correctPrintSequence should not attempt to
    # change the print sequence
    mocked_definition_changes_container = MagicMock(name = "DefinitionChangesContainer")
    mocked_definition_changes_settings = {"extruders_enabled_count": 1}
    mocked_definition_changes_container.getProperty = functools.partial(getPropertyMocked, settings_dict=mocked_definition_changes_settings)
    mocked_stack.definitionChanges = mocked_definition_changes_container

    mocked_user_changes_container = MagicMock(name = "UserChangesContainer")
    mocked_stack.userChanges = mocked_user_changes_container

    machine_manager.correctPrintSequence()

    # After the function is called, the user changes container should not have tried to change any properties
    assert not mocked_user_changes_container.setProperty.called, "The Print Sequence should not be attempted to be changed when there is only one enabled extruder."


def test_correctPrintSequence_TwoExtrudersEnabled_printSequenceIsOneAtATimeInUserSettings(machine_manager, application):
    # Global container stack reports print sequence as one_at_a_time
    mocked_stack = application.getGlobalContainerStack()
    mocked_global_settings = {"print_sequence": "one_at_a_time"}
    mocked_stack.getProperty = functools.partial(getPropertyMocked, settings_dict=mocked_global_settings)

    # The definition changes container reports 2 enabled extruders. Also the print sequence change is not saved in the
    # quality changes container.
    mocked_definition_changes_container = MagicMock(name = "DefinitionChangesContainer")
    mocked_definition_changes_settings = {"extruders_enabled_count": 2, "print_sequence": None}
    mocked_definition_changes_container.getProperty = functools.partial(getPropertyMocked, settings_dict=mocked_definition_changes_settings)
    mocked_stack.definitionChanges = mocked_definition_changes_container

    # The user changes container reports print sequence as "one-at-a-time"
    mocked_user_changes_container = MagicMock(name = "UserChangesContainer")
    mocked_user_changes_settings = {"print_sequence": "one_at_a_time"}
    mocked_user_changes_container.getProperty = functools.partial(getPropertyMocked, settings_dict=mocked_user_changes_settings)
    mocked_stack.userChanges = mocked_user_changes_container

    machine_manager.correctPrintSequence()

    # After the function is called, the user changes container should have tried to remove the print sequence from the
    # user changes container
    mocked_user_changes_container.removeInstance.assert_called_once_with("print_sequence")


def test_correctPrintSequence_TwoExtrudersEnabled_printSequenceIsOneAtATimeInDefinitionChangesSettings(machine_manager, application):
    # Global container stack reports print sequence as one_at_a_time
    mocked_stack = application.getGlobalContainerStack()
    mocked_global_settings = {"print_sequence": "one_at_a_time"}
    mocked_stack.getProperty = functools.partial(getPropertyMocked, settings_dict=mocked_global_settings)

    # The definition changes container reports 2 enabled extruders and contains the print_sequence change to "one-at-a-time"
    mocked_definition_changes_container = MagicMock(name = "DefinitionChangesContainer")
    mocked_definition_changes_settings = {"extruders_enabled_count": 2, "print_sequence": "one_at_a_time"}
    mocked_definition_changes_container.getProperty = functools.partial(getPropertyMocked, settings_dict=mocked_definition_changes_settings)
    mocked_stack.definitionChanges = mocked_definition_changes_container

    # The user changes container doesn't contain print_sequence
    mocked_user_changes_container = MagicMock(name = "UserChangesContainer")
    mocked_user_changes_settings = {"print_sequence": None}
    mocked_user_changes_container.getProperty = functools.partial(getPropertyMocked, settings_dict=mocked_user_changes_settings)
    mocked_stack.userChanges = mocked_user_changes_container

    machine_manager.correctPrintSequence()

    # After the function is called, the print sequence should be set to "all-at-once" in the user changes container
    mocked_user_changes_container.setProperty.assert_called_once_with("print_sequence", "value", "all_at_once")


def test_correctPrintSequence_TwoExtrudersEnabled_printSequenceInUserAndDefinitionChangesSettingsIsNone(machine_manager, application):
    # Global container stack reports print sequence as one_at_a_time
    mocked_stack = application.getGlobalContainerStack()
    mocked_global_settings = {"print_sequence": "one_at_a_time"}
    mocked_stack.getProperty = functools.partial(getPropertyMocked, settings_dict=mocked_global_settings)

    # The definition changes container reports 2 enabled extruders but doesn't contain the print_sequence changes
    mocked_definition_changes_container = MagicMock(name = "DefinitionChangesContainer")
    mocked_definition_changes_settings = {"extruders_enabled_count": 2, "print_sequence": None}
    mocked_definition_changes_container.getProperty = functools.partial(getPropertyMocked, settings_dict=mocked_definition_changes_settings)
    mocked_stack.definitionChanges = mocked_definition_changes_container

    # The user changes container doesn't contain the print_sequence changes
    mocked_user_changes_container = MagicMock(name = "UserChangesContainer")
    mocked_user_changes_settings = {"print_sequence": None}
    mocked_user_changes_container.getProperty = functools.partial(getPropertyMocked, settings_dict=mocked_user_changes_settings)
    mocked_stack.userChanges = mocked_user_changes_container

    machine_manager.correctPrintSequence()

    # After the function is called, the print sequence should be set to "all-at-once" in the user changes container
    mocked_user_changes_container.setProperty.assert_called_once_with("print_sequence", "value", "all_at_once")
