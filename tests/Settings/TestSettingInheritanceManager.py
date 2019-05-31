from unittest.mock import patch, MagicMock

import pytest

from UM.Settings.SettingFunction import SettingFunction
from UM.Settings.SettingInstance import InstanceState
from cura.Settings.SettingInheritanceManager import SettingInheritanceManager

setting_function = SettingFunction("")
setting_function.getUsedSettingKeys = MagicMock(return_value = ["omg", "zomg"])

setting_property_dict = {"setting_1": {},
                         "setting_2": {"state": InstanceState.User, "enabled": False},
                         "setting_3": {"state": InstanceState.User, "enabled": True},
                         "setting_4": {"state": InstanceState.User, "enabled": True, "value": 12},
                         "setting_5": {"state": InstanceState.User, "enabled": True, "value": setting_function}}


def getPropertySideEffect(*args, **kwargs):
    properties = setting_property_dict.get(args[0])
    if properties:
        return properties.get(args[1])


@pytest.fixture
def setting_inheritance_manager():
    with patch("UM.Application.Application.getInstance"):
        with patch("cura.Settings.ExtruderManager.ExtruderManager.getInstance"):
            return SettingInheritanceManager()

@pytest.fixture
def mocked_stack():
    mocked_stack = MagicMock()
    mocked_stack.getProperty = MagicMock(side_effect=getPropertySideEffect)
    mocked_stack.getNextStack = MagicMock(return_value = None)
    mocked_stack.getAllKeys = MagicMock(return_value = ["omg", "zomg", "blarg"])
    return mocked_stack

def test_getChildrenKeysWithOverrideNoGlobalStack(setting_inheritance_manager):
    setting_inheritance_manager._global_container_stack = None
    assert setting_inheritance_manager.getChildrenKeysWithOverride("derp") == []


def test_getChildrenKeysWithOverrideEmptyDefinitions(setting_inheritance_manager):
    mocked_global_container = MagicMock()
    mocked_global_container.definition.findDefinitions = MagicMock(return_value = [])
    setting_inheritance_manager._global_container_stack = mocked_global_container
    assert setting_inheritance_manager.getChildrenKeysWithOverride("derp") == []


def test_getChildrenKeysWithOverride(setting_inheritance_manager):
    mocked_global_container = MagicMock()
    mocked_definition = MagicMock()
    mocked_definition.getAllKeys = MagicMock(return_value = ["omg", "zomg", "blarg"])
    mocked_global_container.definition.findDefinitions = MagicMock(return_value=[mocked_definition])
    setting_inheritance_manager._global_container_stack = mocked_global_container

    setting_inheritance_manager._settings_with_inheritance_warning = ["omg", "zomg"]

    assert setting_inheritance_manager.getChildrenKeysWithOverride("derp") == ["omg", "zomg"]


def test_manualRemoveOverrideWrongSetting(setting_inheritance_manager):
    setting_inheritance_manager._settings_with_inheritance_warning = ["omg", "zomg"]
    assert setting_inheritance_manager.settingsWithInheritanceWarning == ["omg", "zomg"]

    # Shouldn't do anything
    setting_inheritance_manager.manualRemoveOverride("BLARG")
    assert setting_inheritance_manager.settingsWithInheritanceWarning == ["omg", "zomg"]


def test_manualRemoveOverrideExistingSetting(setting_inheritance_manager):
    setting_inheritance_manager._settings_with_inheritance_warning = ["omg", "zomg"]
    assert setting_inheritance_manager.settingsWithInheritanceWarning == ["omg", "zomg"]

    # Shouldn't do anything
    setting_inheritance_manager.manualRemoveOverride("omg")
    assert setting_inheritance_manager.settingsWithInheritanceWarning == ["zomg"]


def test_getOverridesForExtruderNoGlobalStack(setting_inheritance_manager):
    setting_inheritance_manager._global_container_stack = None
    assert setting_inheritance_manager.getOverridesForExtruder("derp", 0) == []


def test_settingIsOverwritingInheritanceNoUserState(setting_inheritance_manager, mocked_stack):
    # Setting 1 doesn't have a user state, so it cant have an override
    assert not setting_inheritance_manager._settingIsOverwritingInheritance("setting_1", mocked_stack)


def test_settingIsOverwritingInheritanceNotEnabled(setting_inheritance_manager, mocked_stack):
    # Setting 2 doesn't have a enabled, so it cant have an override
    assert not setting_inheritance_manager._settingIsOverwritingInheritance("setting_2", mocked_stack)


def test_settingIsOverwritingInheritanceNoContainers(setting_inheritance_manager, mocked_stack):
    mocked_stack.getContainers = MagicMock(return_value = [])
    # All the properties are correct, but there are no containers :(
    assert not setting_inheritance_manager._settingIsOverwritingInheritance("setting_3", mocked_stack)


def test_settingIsOverwritingInheritanceNoneValue(setting_inheritance_manager, mocked_stack):
    mocked_container = MagicMock()
    mocked_container.getProperty = MagicMock(side_effect=getPropertySideEffect)
    mocked_stack.getContainers = MagicMock(return_value = [mocked_container])

    # Setting 3 doesn't have a value, so even though the container is there, it's value is None
    assert not setting_inheritance_manager._settingIsOverwritingInheritance("setting_3", mocked_stack)


def test_settingIsOverwritingInheritanceNoSettingFunction(setting_inheritance_manager, mocked_stack):
    mocked_container = MagicMock()
    mocked_container.getProperty = MagicMock(side_effect=getPropertySideEffect)
    mocked_stack.getContainers = MagicMock(return_value=[mocked_container])

    # Setting 4 does have a value, but it's not a settingFunction
    assert not setting_inheritance_manager._settingIsOverwritingInheritance("setting_4", mocked_stack)


def test_settingIsOverwritingInheritanceSingleSettingFunction(setting_inheritance_manager, mocked_stack):
    mocked_container = MagicMock()
    mocked_container.getProperty = MagicMock(side_effect=getPropertySideEffect)
    mocked_stack.getContainers = MagicMock(return_value=[mocked_container])
    setting_inheritance_manager._active_container_stack = mocked_stack
    # Setting 5 does have a value, but we only have one container filled
    assert not setting_inheritance_manager._settingIsOverwritingInheritance("setting_5", mocked_stack)


def test_settingIsOverwritingInheritance(setting_inheritance_manager, mocked_stack):
    mocked_container = MagicMock()
    mocked_second_container = MagicMock()
    mocked_second_container.getProperty = MagicMock(return_value = 12)
    mocked_container.getProperty = MagicMock(side_effect=getPropertySideEffect)
    mocked_stack.getContainers = MagicMock(return_value=[mocked_second_container, mocked_container])
    setting_inheritance_manager._active_container_stack = mocked_stack

    assert setting_inheritance_manager._settingIsOverwritingInheritance("setting_5", mocked_stack)