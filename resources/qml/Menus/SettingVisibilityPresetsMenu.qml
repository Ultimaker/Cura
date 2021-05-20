// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.11
import QtQml.Models 2.14 as Models

import UM 1.2 as UM
import Cura 1.0 as Cura

Cura.Menu
{
    ActionGroup { id: group }

    id: menu
    title: catalog.i18nc("@action:inmenu", "Visible Settings")

    property QtObject settingVisibilityPresetsModel: CuraApplication.getSettingVisibilityPresetsModel()

    signal collapseAllCategories()

    Models.Instantiator
    {
        model: settingVisibilityPresetsModel.items

        Cura.MenuItem
        {
            text: modelData.name
            checkable: true
            checked: modelData.presetId == settingVisibilityPresetsModel.activePreset
            ActionGroup.group: group
            onTriggered:
            {
                settingVisibilityPresetsModel.setActivePreset(modelData.presetId);
            }
        }

        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }

    Cura.MenuSeparator {}
    Cura.MenuItem
    {
        text: catalog.i18nc("@action:inmenu", "Collapse All Categories")
        onTriggered:
        {
            collapseAllCategories();
        }
    }
    Cura.MenuSeparator {}
    Cura.MenuItem
    {
        text: catalog.i18nc("@action:inmenu", "Manage Setting Visibility...")
        icon.name: "configure"
        onTriggered: Cura.Actions.configureSettingVisibility.trigger()
    }
}
