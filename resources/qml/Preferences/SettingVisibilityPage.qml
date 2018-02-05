// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.2 as UM

import Cura 1.0 as Cura

UM.PreferencesPage
{
    title: catalog.i18nc("@title:tab", "Setting Visibility");

    property int scrollToIndex: 0

    signal scrollToSection( string key )
    onScrollToSection:
    {
        settingsListView.positionViewAtIndex(definitionsModel.getIndex(key), ListView.Beginning)
    }

    function reset()
    {
        UM.Preferences.resetPreference("general/visible_settings")

        // After calling this function update Setting visibility preset combobox.
        // Reset should set "Basic" setting preset
        visibilityPreset.setBasicPreset()

    }
    resetEnabled: true;

    Item
    {
        id: base;
        anchors.fill: parent;

        CheckBox
        {
            id: toggleVisibleSettings
            anchors
            {
                verticalCenter: filter.verticalCenter;
                left: parent.left;
                leftMargin: UM.Theme.getSize("default_margin").width
            }
            text: catalog.i18nc("@label:textbox", "Check all")
            checkedState:
            {
                if(definitionsModel.visibleCount == definitionsModel.categoryCount)
                {
                    return Qt.Unchecked
                }
                else if(definitionsModel.visibleCount == definitionsModel.rowCount(null))
                {
                    return Qt.Checked
                }
                else
                {
                    return Qt.PartiallyChecked
                }
            }
            partiallyCheckedEnabled: true

            MouseArea
            {
                anchors.fill: parent;
                onClicked:
                {
                    if(parent.checkedState == Qt.Unchecked || parent.checkedState == Qt.PartiallyChecked)
                    {
                        definitionsModel.setAllVisible(true)
                    }
                    else
                    {
                        definitionsModel.setAllVisible(false)
                    }

                    // After change set "Custom" option
                    visibilityPreset.currentIndex = visibilityPreset.model.count - 1
                }
            }
        }

        TextField
        {
            id: filter;

            anchors
            {
                top: parent.top
                left: toggleVisibleSettings.right
                leftMargin: UM.Theme.getSize("default_margin").width
                right: visibilityPreset.left
                rightMargin: UM.Theme.getSize("default_margin").width
            }

            placeholderText: catalog.i18nc("@label:textbox", "Filter...")

            onTextChanged: definitionsModel.filter = {"i18n_label": "*" + text}
        }

        ComboBox
        {
            property int customOptionValue: 100

            function setBasicPreset()
            {
                var index = 0
                for(var i = 0; i < presetNamesList.count; ++i)
                {
                    if(model.get(i).text == "Basic")
                    {
                        index = i;
                        break;
                    }
                }

                visibilityPreset.currentIndex = index
            }

            id: visibilityPreset
            width: 150
            anchors
            {
                top: parent.top
                right: parent.right
            }

            model: ListModel
            {
                id: presetNamesList
                Component.onCompleted:
                {
                    // returned value is Dictionary  (Ex: {1:"Basic"}, The number 1 is the weight and sort by weight)
                    var itemsDict = UM.Preferences.getValue("general/visible_settings_preset")
                    var sorted = [];
                    for(var key in itemsDict) {
                        sorted[sorted.length] = key;
                    }

                    sorted.sort();
                    for(var i = 0; i < sorted.length; i++) {
                        presetNamesList.append({text: itemsDict[sorted[i]], value: i});
                    }

                    // By agreement lets "Custom" option will have value 100
                    presetNamesList.append({text: "Custom", value: visibilityPreset.customOptionValue});
                }
            }

            currentIndex:
            {
                // Load previously selected preset.
                var text = UM.Preferences.getValue("general/preset_setting_visibility_choice");



                var index = 0;
                for(var i = 0; i < presetNamesList.count; ++i)
                {
                    if(model.get(i).text == text)
                    {
                        index = i;
                        break;
                    }
                }
                return index;
            }

            onActivated:
            {
                // TODO What to do if user is selected "Custom from Combobox" ?
                if (model.get(index).text == "Custom")
                    return

                var newVisibleSettings = CuraApplication.getVisibilitySettingPreset(model.get(index).text)
                UM.Preferences.setValue("general/visible_settings", newVisibleSettings)
                UM.Preferences.setValue("general/preset_setting_visibility_choice", model.get(index).text)
            }
        }

        ScrollView
        {
            id: scrollView

            frameVisible: true

            anchors
            {
                top: filter.bottom;
                topMargin: UM.Theme.getSize("default_margin").height
                left: parent.left;
                right: parent.right;
                bottom: parent.bottom;
            }
            ListView
            {
                id: settingsListView

                model: UM.SettingDefinitionsModel
                {
                    id: definitionsModel
                    containerId: Cura.MachineManager.activeDefinitionId
                    showAll: true
                    exclude: ["machine_settings", "command_line_settings"]
                    showAncestors: true
                    expanded: ["*"]
                    visibilityHandler: UM.SettingPreferenceVisibilityHandler { }
                }

                delegate: Loader
                {
                    id: loader

                    width: parent.width
                    height: model.type != undefined ? UM.Theme.getSize("section").height : 0

                    property var definition: model
                    property var settingDefinitionsModel: definitionsModel

                    asynchronous: true
                    active: model.type != undefined
                    sourceComponent:
                    {
                        switch(model.type)
                        {
                            case "category":
                                return settingVisibilityCategory
                            default:
                                return settingVisibilityItem
                        }
                    }
                }
            }
        }

        UM.I18nCatalog { name: "cura"; }
        SystemPalette { id: palette; }

        Component
        {
            id: settingVisibilityCategory;

            UM.SettingVisibilityCategory { }
        }

        Component
        {
            id: settingVisibilityItem;

            UM.SettingVisibilityItem {

                // after changing any visibility of settings, set the preset to the "Custom" option
                visibilityChangeCallback : function()
                {
                    // If already "Custom" then don't do nothing
                    if (visibilityPreset.currentIndex != visibilityPreset.model.count - 1)
                    {
                        visibilityPreset.currentIndex = visibilityPreset.model.count - 1
                    }
                }
            }
        }
    }
}