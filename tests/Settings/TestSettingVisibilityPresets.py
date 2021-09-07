from unittest.mock import MagicMock, patch

import os.path

from UM.Preferences import Preferences
from UM.Resources import Resources
from cura.CuraApplication import CuraApplication
from cura.Machines.Models.SettingVisibilityPresetsModel import SettingVisibilityPresetsModel
from cura.Settings.SettingVisibilityPreset import SettingVisibilityPreset

setting_visibility_preset_test_settings = {"test", "zomg", "derp", "yay", "whoo"}

Resources.addSearchPath(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources")))
Resources.addStorageType(CuraApplication.ResourceTypes.SettingVisibilityPreset, "setting_visibility")


def test_createVisibilityPresetFromLocalFile():
    # Simple creation test. This is separated from the visibilityFromPrevious, since we can't check for the contents
    # of the other profiles, since they might change over time.
    visibility_preset = SettingVisibilityPreset()

    visibility_preset.loadFromFile(os.path.join(os.path.dirname(os.path.abspath(__file__)), "setting_visibility_preset_test.cfg"))
    assert setting_visibility_preset_test_settings == set(visibility_preset.settings)

    assert visibility_preset.name == "test"
    assert visibility_preset.weight == 1
    assert visibility_preset.settings.count("yay") == 1  # It's in the file twice but we should load it once.

def test_visibilityFromPrevious():
    # This test checks that all settings in basic are in advanced and all settings in advanced are in expert.
    with patch("cura.CuraApplication.CuraApplication.getInstance"):
        visibility_model = SettingVisibilityPresetsModel(Preferences())

    basic_visibility = visibility_model.getVisibilityPresetById("basic")
    advanced_visibility = visibility_model.getVisibilityPresetById("advanced")
    expert_visibility = visibility_model.getVisibilityPresetById("expert")

    # Check if there are settings that are in basic, but not in advanced.
    settings_not_in_advanced = set(basic_visibility.settings) - set(advanced_visibility.settings)
    assert len(settings_not_in_advanced) == 0  # All settings in basic should be in advanced

    # Check if there are settings that are in advanced, but not in expert.
    settings_not_in_expert = set(advanced_visibility.settings) - set(expert_visibility.settings)
    assert len(settings_not_in_expert) == 0  # All settings in advanced should be in expert.


def test_setActivePreset():
    preferences = Preferences()
    with patch("cura.CuraApplication.CuraApplication.getInstance"):
        visibility_model = SettingVisibilityPresetsModel(preferences)
    visibility_model.activePresetChanged = MagicMock()
    # Ensure that we start off with basic (since we didn't change anything just yet!)
    assert visibility_model.activePreset == "basic"

    # Everything should be the same.
    visibility_model.setActivePreset("basic")
    assert visibility_model.activePreset == "basic"
    assert visibility_model.activePresetChanged.emit.call_count == 0  # No events should be sent.

    # Change it to existing type (should work...)
    visibility_model.setActivePreset("advanced")
    assert visibility_model.activePreset == "advanced"
    assert visibility_model.activePresetChanged.emit.call_count == 1

    # Change to unknown preset. Shouldn't do anything.
    visibility_model.setActivePreset("OMGZOMGNOPE")
    assert visibility_model.activePreset == "advanced"
    assert visibility_model.activePresetChanged.emit.call_count == 1


def test_preferenceChanged():
    preferences = Preferences()
    # Set the visible_settings to something silly
    preferences.addPreference("general/visible_settings", "omgzomg")
    with patch("cura.CuraApplication.CuraApplication.getInstance"):
        visibility_model = SettingVisibilityPresetsModel(preferences)
    visibility_model.activePresetChanged = MagicMock()

    assert visibility_model.activePreset == "custom"  # This should make the model start at "custom
    assert visibility_model.activePresetChanged.emit.call_count == 0

    basic_visibility = visibility_model.getVisibilityPresetById("basic")
    new_visibility_string = ";".join(basic_visibility.settings)
    preferences.setValue("general/visible_settings", new_visibility_string)

    # Fake a signal emit (since we didn't create the application, our own signals are not fired)
    visibility_model._onPreferencesChanged("general/visible_settings")
    # Set the visibility settings to basic
    assert visibility_model.activePreset == "basic"
    assert visibility_model.activePresetChanged.emit.call_count == 1
