// Copyright (c) 2017 Ultimaker B.V.
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
        text: catalog.i18nc("@action:inmenu", "Search Results")
        checkable: true
        visible: showingSearchResults
        checked: showingSearchResults
        exclusiveGroup: group
    }
    MenuSeparator { visible: showingSearchResults }

    MenuItem
    {
        text: catalog.i18nc("@action:inmenu", "Custom selection")
        checkable: true
        checked: !showingSearchResults && !showingAllSettings
        exclusiveGroup: group
        onTriggered: showSettingVisibilityProfile("Custom")
    }
    MenuSeparator { }

    Instantiator
    {
        model: Cura.SettingVisibilityProfilesModel

        MenuItem
        {
            text: model.name
            checkable: true
            checked: false
            exclusiveGroup: group
            onTriggered:
            {
                UM.Preferences.setValue("general/visible_settings", model.settings.join(";"));
                UM.Preferences.setValue("general/preset_setting_visibility_choice", model.id);

                showSettingVisibilityProfile();
            }
        }

        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }

    MenuSeparator { visible: false }
    MenuItem
    {
        text: catalog.i18nc("@action:inmenu", "Changed settings")
        visible: false
        enabled: true
        checkable: true
        checked: showingAllSettings
        exclusiveGroup: group
        onTriggered: showAllSettings()
    }
    MenuItem
    {
        text: catalog.i18nc("@action:inmenu", "Settings in profile")
        visible: false
        enabled: true
        checkable: true
        checked: showingAllSettings
        exclusiveGroup: group
        onTriggered: showAllSettings()
    }
    MenuSeparator {}
    MenuItem
    {
        text: catalog.i18nc("@action:inmenu", "All Settings")
        checkable: true
        checked: showingAllSettings
        exclusiveGroup: group
        onTriggered: showAllSettings()
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
