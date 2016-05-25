// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Window 2.2

import UM 1.2 as UM
import Cura 1.0 as Cura
import ".."


Item {
    id: base;
    property int currentIndex: UM.ActiveTool.properties.getValue("SelectedIndex")

    UM.I18nCatalog { id: catalog; name: "cura"; }

    width: childrenRect.width;
    height: childrenRect.height;

    Column {
        id: items
        anchors.top: parent.top;
        anchors.left: parent.left;

        spacing: UM.Theme.getSize("default_margin").height;

        Column {
            id: customisedSettings
            spacing: UM.Theme.getSize("default_lining").height;
            width: UM.Theme.getSize("setting").width + UM.Theme.getSize("setting").height/2;

            Repeater {
                id: settings;

                model: UM.ActiveTool.properties.getValue("Model").getItem(base.currentIndex).settings

                UM.SettingItem {
                    width: UM.Theme.getSize("setting").width;
                    height: UM.Theme.getSize("setting").height;

                    name: model.label;
                    type: model.type;
                    value: model.value;
                    description: model.description;
                    unit: model.unit;
                    valid: model.valid;
                    visible: !model.global_only
                    options: model.options
                    indent: false

                    style: UM.Theme.styles.setting_item;

                    onItemValueChanged: {
                        settings.model.setSettingValue(model.key, value)
                    }

                    Button
                    {
                        anchors.left: parent.right;

                        width: UM.Theme.getSize("setting").height;
                        height: UM.Theme.getSize("setting").height;

                        onClicked: UM.ActiveTool.properties.getValue("Model").removeSettingOverride(UM.ActiveTool.properties.getValue("Model").getItem(base.currentIndex).id, model.key)

                        style: ButtonStyle
                        {
                            background: Rectangle
                            {
                                color: control.hovered ? control.parent.style.controlHighlightColor : control.parent.style.controlColor;
                                UM.RecolorImage
                                {
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    width: parent.width/2
                                    height: parent.height/2
                                    sourceSize.width: width
                                    sourceSize.height: width
                                    color: control.hovered ? UM.Theme.getColor("setting_control_button_hover") : UM.Theme.getColor("setting_control_button")
                                    source: UM.Theme.getIcon("cross1")
                                }
                            }
                        }
                    }
                }
            }
        }

        Button
        {
            id: customise_settings_button;
            height: UM.Theme.getSize("setting").height;
            visible: parseInt(UM.Preferences.getValue("cura/active_mode")) == 1

            text: catalog.i18nc("@action:button", "Add Setting");

            style: ButtonStyle
            {
                background: Rectangle
                {
                    width: control.width;
                    height: control.height;
                    border.width: UM.Theme.getSize("default_lining").width;
                    border.color: control.pressed ? UM.Theme.getColor("action_button_active_border") :
                                  control.hovered ? UM.Theme.getColor("action_button_hovered_border") : UM.Theme.getColor("action_button_border")
                    color: control.pressed ? UM.Theme.getColor("action_button_active") :
                           control.hovered ? UM.Theme.getColor("action_button_hovered") : UM.Theme.getColor("action_button")
                }
                label: Label
                {
                    text: control.text;
                    color: UM.Theme.getColor("setting_control_text");
                    anchors.centerIn: parent
                }
            }

            onClicked: settingPickDialog.visible = true;

            Connections
            {
                target: UM.Preferences;

                onPreferenceChanged:
                {
                    customise_settings_button.visible = parseInt(UM.Preferences.getValue("cura/active_mode"))
                }
            }
        }
    }


    UM.Dialog {
        id: settingPickDialog

        title: catalog.i18nc("@title:window", "Pick a Setting to Customize")
        property string labelFilter: ""

        TextField {
            id: filter;

            anchors {
                top: parent.top;
                left: parent.left;
                right: parent.right;
            }

            placeholderText: catalog.i18nc("@label:textbox", "Filter...");

            onTextChanged:
            {
                if(text != "")
                {
                    listview.model.filter = {"global_only": false, "label": "*" + text}
                }
                else
                {
                    listview.model.filter = {"global_only": false}
                }
            }
        }

        ScrollView
        {
            id: scrollView

            anchors
            {
                top: filter.bottom;
                left: parent.left;
                right: parent.right;
                bottom: parent.bottom;
            }
            ListView
            {
                id:listview
                model: UM.SettingDefinitionsModel
                {
                    id: definitionsModel;
                    containerId: Cura.MachineManager.activeDefinitionId
                    filter:
                    {
                        "global_only": false
                    }
                }
                delegate:Loader
                {
                    id: loader

                    width: parent.width
                    height: model.type != undefined ? UM.Theme.getSize("section").height : 0;

                    property var definition: model
                    property var settingDefinitionsModel: definitionsModel

                    asynchronous: true
                    source:
                    {
                        switch(model.type)
                        {
                            case "category":
                                return "PerObjectCategory.qml"
                            default:
                                return "PerObjectItem.qml"
                        }
                    }
                }
            }
        }

        rightButtons: [
            Button {
                text: catalog.i18nc("@action:button", "Cancel");
                onClicked: {
                    settingPickDialog.visible = false;
                }
            }
        ]
    }

    SystemPalette { id: palette; }
}
