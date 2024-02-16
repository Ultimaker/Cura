// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 2.15

import UM 1.5 as UM

import Cura 1.0 as Cura

UM.PreferencesPage
{
    title: catalog.i18nc("@title:tab", "Setting Visibility")

    Item { enabled: false; UM.I18nCatalog { id: catalog; name: "cura"} }

    property QtObject settingVisibilityPresetsModel: CuraApplication.getSettingVisibilityPresetsModel()

    property int scrollToIndex: 0

    buttons: [
        Cura.SecondaryButton
        {
            text: catalog.i18nc("@action:button", "Defaults")
            onClicked: reset()
        }
    ]

    signal scrollToSection( string key )
    onScrollToSection:
    {
        settingsListView.positionViewAtIndex(definitionsModel.getIndex(key), ListView.Beginning)
    }

    function reset()
    {
        settingVisibilityPresetsModel.setActivePreset("basic")
    }
    resetEnabled: true;

    Item
    {
        id: base
        anchors.fill: parent

        UM.CheckBox
        {
            id: toggleVisibleSettings
            anchors
            {
                verticalCenter: filter.verticalCenter
                left: parent.left
                leftMargin: UM.Theme.getSize("default_margin").width
            }
            text: catalog.i18nc("@label:textbox", "Check all")
            checkState:
            {
                if(definitionsModel.visibleCount == definitionsModel.categoryCount)
                {
                    return Qt.Unchecked
                }
                else if(definitionsModel.visibleCount == definitionsModel.count)
                {
                    return Qt.Checked
                }
                else
                {
                    return Qt.PartiallyChecked
                }
            }
            tristate: true
            MouseArea
            {
                anchors.fill: parent;
                onClicked:
                {
                    if (parent.checkState == Qt.Unchecked || parent.checkState == Qt.PartiallyChecked)
                    {
                        definitionsModel.setAllExpandedVisible(true)
                    }
                    else
                    {
                        definitionsModel.setAllExpandedVisible(false)
                    }
                }
            }
        }

        Cura.TextField
        {
            id: filter

            anchors
            {
                top: parent.top
                left: toggleVisibleSettings.right
                leftMargin: UM.Theme.getSize("default_margin").width
                right: visibilityPreset.left
                rightMargin: UM.Theme.getSize("default_margin").width
            }

            placeholderText: catalog.i18nc("@label:textbox", "Filter...")

            onTextChanged: definitionsModel.filter = {"i18n_label|i18n_description": "*" + text}
        }

        Cura.ComboBox
        {
            id: visibilityPreset
            width: UM.Theme.getSize("action_button").width
            anchors
            {
                top: parent.top
                right: parent.right
                verticalCenter: filter.verticalCenter
            }

            model: settingVisibilityPresetsModel.items
            textRole: "name"

            currentIndex:
            {
                var idx = -1;
                for(var i = 0; i < settingVisibilityPresetsModel.items.length; ++i)
                {
                    if(settingVisibilityPresetsModel.items[i].presetId === settingVisibilityPresetsModel.activePreset)
                    {
                        idx = i;
                        break;
                    }
                }
                return idx;
            }

            onActivated:
            {
                var preset_id = settingVisibilityPresetsModel.items[index].presetId
                settingVisibilityPresetsModel.setActivePreset(preset_id)
            }
        }

        ListView
        {
            id: settingsListView
            anchors
            {
                top: filter.bottom
                topMargin: UM.Theme.getSize("default_margin").height
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }

            clip: true
            ScrollBar.vertical: UM.ScrollBar { id: scrollBar }

            model: UM.SettingDefinitionsModel
            {
                id: definitionsModel
                containerId: Cura.MachineManager.activeMachine != null ? Cura.MachineManager.activeMachine.definition.id: ""
                showAll: true
                exclude: ["machine_settings", "command_line_settings", "ppr"]
                showAncestors: true
                expanded: ["*"]
                visibilityHandler: UM.SettingPreferenceVisibilityHandler {}
            }

            property Component settingVisibilityCategory: Cura.SettingVisibilityCategory {}
            property Component settingVisibilityItem: Cura.SettingVisibilityItem {}

            delegate: Loader
            {
                id: loader

                width: settingsListView.width - scrollBar.width
                height: model.type !== undefined ? UM.Theme.getSize("section").height : 0

                property var definition: model
                property var settingDefinitionsModel: definitionsModel

                asynchronous: true
                active: model.type !== undefined
                sourceComponent:
                {
                    switch (model.type)
                    {
                        case "category":
                            return settingsListView.settingVisibilityCategory
                        default:
                            return settingsListView.settingVisibilityItem
                    }
                }
            }
        }
    }
}
