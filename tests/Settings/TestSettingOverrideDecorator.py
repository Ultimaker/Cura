from unittest.mock import patch, MagicMock

import pytest

from cura.Settings.SettingOverrideDecorator import SettingOverrideDecorator


extruder_manager = MagicMock(name= "ExtruderManager")
application = MagicMock(name="application")
container_registry = MagicMock(name="container_registry")

@pytest.fixture()
def setting_override_decorator():
    # Ensure that all the call counts and the like are reset.
    container_registry.reset_mock()
    application.reset_mock()
    extruder_manager.reset_mock()

    # Actually create the decorator.
    with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
        with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
            with patch("cura.Settings.ExtruderManager.ExtruderManager.getInstance", MagicMock(return_value=extruder_manager)):
                return SettingOverrideDecorator()


def test_onSettingValueChanged(setting_override_decorator):
    # On creation the needs slicing should be called once (as it being added should trigger a reslice)
    assert application.getBackend().needsSlicing.call_count == 1
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
        setting_override_decorator._onSettingChanged("blarg", "value")

    # Once we set a setting value, it should trigger again.
    assert application.getBackend().needsSlicing.call_count == 2


def test_onSettingEnableChanged(setting_override_decorator):
    # On creation the needs slicing should be called once (as it being added should trigger a reslice)
    assert application.getBackend().needsSlicing.call_count == 1
    with patch("UM.Application.Application.getInstance", MagicMock(return_value=application)):
        setting_override_decorator._onSettingChanged("blarg", "enabled")

    # Once we set a property that is not a value, no re-slice should happen.
    assert application.getBackend().needsSlicing.call_count == 1


def test_setActiveExtruder(setting_override_decorator):
    setting_override_decorator.activeExtruderChanged.emit = MagicMock()
    with patch("cura.Settings.ExtruderManager.ExtruderManager.getInstance", MagicMock(return_value=extruder_manager)):
        with patch("UM.Settings.ContainerRegistry.ContainerRegistry.getInstance", MagicMock(return_value=container_registry)):
            setting_override_decorator.setActiveExtruder("ZOMG")
    setting_override_decorator.activeExtruderChanged.emit.assert_called_once_with()
    assert setting_override_decorator.getActiveExtruder() == "ZOMG"
