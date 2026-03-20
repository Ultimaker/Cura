# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
import sys
from typing import Any, Dict, List
from unittest.mock import patch, MagicMock

from UM.PluginRegistry import PluginRegistry
from UM.Resources import Resources
from UM.Trust import Trust
from ..PostProcessingPlugin import PostProcessingPlugin

# not sure if needed
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

""" In this file, community refers to regular Cura for makers."""

mock_plugin_registry = MagicMock()
mock_plugin_registry.getPluginPath = MagicMock(return_value = "mocked_plugin_path")


# noinspection PyProtectedMember
@patch("cura.ApplicationMetadata.IsEnterpriseVersion", False)
def test_community_user_script_allowed():
    assert PostProcessingPlugin._isScriptAllowed("blaat.py")


# noinspection PyProtectedMember
@patch("cura.ApplicationMetadata.IsEnterpriseVersion", False)
def test_community_bundled_script_allowed():
    assert PostProcessingPlugin._isScriptAllowed(_bundled_file_path())


# noinspection PyProtectedMember
@patch("cura.ApplicationMetadata.IsEnterpriseVersion", True)
@patch.object(PluginRegistry, "getInstance", return_value=mock_plugin_registry)
def test_enterprise_unsigned_user_script_not_allowed(plugin_registry):
    assert not PostProcessingPlugin._isScriptAllowed("blaat.py")

# noinspection PyProtectedMember
@patch("cura.ApplicationMetadata.IsEnterpriseVersion", True)
@patch.object(PluginRegistry, "getInstance", return_value=mock_plugin_registry)
def test_enterprise_signed_user_script_allowed(plugin_registry):
    mocked_trust = MagicMock()
    mocked_trust.signedFileCheck = MagicMock(return_value=True)

    plugin_registry.getPluginPath = MagicMock(return_value="mocked_plugin_path")

    with patch.object(Trust, "signatureFileExistsFor", return_value = True):
        with patch("UM.Trust.Trust.getInstanceOrNone", return_value=mocked_trust):
            assert PostProcessingPlugin._isScriptAllowed("mocked_plugin_path/scripts/blaat.py")


# noinspection PyProtectedMember
@patch("cura.ApplicationMetadata.IsEnterpriseVersion", False)
def test_enterprise_bundled_script_allowed():
    assert PostProcessingPlugin._isScriptAllowed(_bundled_file_path())


def _create_plugin_with_scripts(scripts: List[Any]) -> MagicMock:
    plugin = MagicMock(spec=PostProcessingPlugin)
    plugin._script_list = scripts
    plugin._loaded_scripts = {}
    plugin._selected_script_index = len(scripts) - 1 if scripts else -1
    plugin.setSelectedScriptIndex = lambda index: setattr(plugin, "_selected_script_index", index)
    plugin.duplicateScriptByIndex = lambda index: PostProcessingPlugin.duplicateScriptByIndex(plugin, index)
    return plugin


def _create_mock_script(key: str, settings: Dict[str, Any], values: Dict[str, Any]) -> MagicMock:
    script = MagicMock()
    script.getSettingData = MagicMock(return_value={"key": key, "settings": settings})
    script.getSettingValueByKey = MagicMock(side_effect=lambda k: values.get(k))
    script._instance = MagicMock()
    return script


def test_duplicate_script_appends_copy() -> None:
    original_script = _create_mock_script("PauseAtHeight", {"pause_height": None}, {"pause_height": 10})

    new_script = MagicMock()
    new_script._instance = MagicMock()
    new_script_class = MagicMock(return_value=new_script)

    plugin = _create_plugin_with_scripts([original_script])
    plugin._loaded_scripts = {"PauseAtHeight": new_script_class}

    plugin.duplicateScriptByIndex(0)

    assert len(plugin._script_list) == 2
    new_script.initialize.assert_called_once()
    new_script._instance.setProperty.assert_called_once_with("pause_height", "value", 10)
    assert plugin._selected_script_index == 1


def test_duplicate_script_invalid_index_below_range() -> None:
    original_script = _create_mock_script("PauseAtHeight", {}, {})
    plugin = _create_plugin_with_scripts([original_script])

    plugin.duplicateScriptByIndex(-1)

    assert len(plugin._script_list) == 1


def test_duplicate_script_invalid_index_above_range() -> None:
    original_script = _create_mock_script("PauseAtHeight", {}, {})
    plugin = _create_plugin_with_scripts([original_script])

    plugin.duplicateScriptByIndex(5)

    assert len(plugin._script_list) == 1


def test_duplicate_script_empty_list() -> None:
    plugin = _create_plugin_with_scripts([])

    plugin.duplicateScriptByIndex(0)

    assert len(plugin._script_list) == 0


def test_duplicate_script_copies_all_settings() -> None:
    settings = {"layer": None, "speed": None, "temp": None}
    values = {"layer": 5, "speed": 50, "temp": 210}
    original_script = _create_mock_script("PauseAtHeight", settings, values)

    new_script = MagicMock()
    new_script._instance = MagicMock()
    new_script_class = MagicMock(return_value=new_script)

    plugin = _create_plugin_with_scripts([original_script])
    plugin._loaded_scripts = {"PauseAtHeight": new_script_class}

    plugin.duplicateScriptByIndex(0)

    calls = new_script._instance.setProperty.call_args_list
    called_keys = {call.args[0]: call.args[2] for call in calls}
    assert called_keys == {"layer": 5, "speed": 50, "temp": 210}


def _bundled_file_path():
    return os.path.join(
        Resources.getStoragePath(Resources.Resources) + "scripts/blaat.py"
    )
