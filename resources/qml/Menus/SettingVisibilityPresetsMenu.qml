// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: menu
    title: catalog.i18nc("@action:inmenu", "Visible Settings")

    property bool showingSearchResults
    property bool showingAllSettings

    signal showAllSettings()
    signal showSettingVisibilityProfile()

    MenuItem
    {
        text: catalog.i18nc("@action:inmenu", "Custom selection")
        checkable: true
        checked: !showingSearchResults && !showingAllSettings && Cura.SettingVisibilityPresetsModel.activePreset == "custom"
        exclusiveGroup: group
        onTriggered:
        {
            Cura.SettingVisibilityPresetsModel.setActivePreset("custom");
            // Restore custom set from preference
            UM.Preferences.setValue("general/visible_settings", UM.Preferences.getValue("cura/custom_visible_settings"));
            showSettingVisibilityProfile();
        }
    }
    MenuSeparator { }

    Instantiator
    {
        model: Cura.SettingVisibilityPresetsModel

        MenuItem
        {
            text: model.name
            checkable: true
            checked: model.id == Cura.SettingVisibilityPresetsModel.activePreset
            exclusiveGroup: group
            onTriggered:
            {
                Cura.SettingVisibilityPresetsModel.setActivePreset(model.id);

                UM.Preferences.setValue("general/visible_settings", model.settings.join(";"));

                showSettingVisibilityProfile();
            }
        }

        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }

    MenuSeparator {}
    MenuItem
    {
        text: catalog.i18nc("@action:inmenu", "All Settings")
        checkable: true
        checked: showingAllSettings
        exclusiveGroup: group
        onTriggered:
        {
            showAllSettings();
        }
    }
    MenuSeparator {}
    MenuItem
    {
        text: catalog.i18nc("@action:inmenu", "Manage Setting Visibility...")
        iconName: "configure"
        onTriggered: Cura.Actions.configureSettingVisibility.trigger()
    }

    ExclusiveGroup { id: group }
}
