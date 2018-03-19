// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: menu
    title: catalog.i18nc("@action:inmenu", "Visible Settings")

    property QtObject settingVisibilityPresetsModel: CuraApplication.getSettingVisibilityPresetsModel()

    signal showAllSettings()

    Instantiator
    {
        model: settingVisibilityPresetsModel

        MenuItem
        {
            text: model.name
            checkable: true
            checked: model.id == settingVisibilityPresetsModel.activePreset
            exclusiveGroup: group
            onTriggered:
            {
                settingVisibilityPresetsModel.setActivePreset(model.id);
                showSettingVisibilityProfile();
            }
        }

        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }

    MenuSeparator {}
    MenuItem
    {
        text: catalog.i18nc("@action:inmenu", "Show All Settings")
        checkable: false
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
