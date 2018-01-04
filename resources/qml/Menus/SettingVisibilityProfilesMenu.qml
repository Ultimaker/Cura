// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: menu
    title: "Visible Settings"

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
        text: catalog.i18nc("@action:inmenu", "Normal Set")
        checkable: true
        checked: !showingSearchResults && !showingAllSettings
        exclusiveGroup: group
        onTriggered: showSettingVisibilityProfile()
    }
    MenuSeparator {}
    MenuItem
    {
        text: catalog.i18nc("@action:inmenu", "Changed settings")
        enabled: false
        checkable: true
        checked: showingAllSettings
        exclusiveGroup: group
        onTriggered: showAllSettings()
    }
    MenuItem
    {
        text: catalog.i18nc("@action:inmenu", "Settings in profile")
        enabled: false
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
        text: catalog.i18nc("@action:inmenu", "Manage Visibility Profiles...")
        iconName: "configure"
        onTriggered: Cura.Actions.configureSettingVisibility.trigger()
    }

    ExclusiveGroup { id: group }
}
