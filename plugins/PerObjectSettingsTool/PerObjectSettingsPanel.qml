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

    UM.I18nCatalog { id: catalog; name: "cura"; }

    width: childrenRect.width;
    height: childrenRect.height;

    Column
    {
        id: items
        anchors.top: parent.top;
        anchors.left: parent.left;

        spacing: UM.Theme.getSize("default_margin").height;

        Repeater
        {
            id: contents
            height: childrenRect.height;

            model: UM.SettingDefinitionsModel
            {
                id: addedSettingsModel;
                containerId: Cura.MachineManager.activeDefinitionId
                visibilityHandler: Cura.PerObjectSettingVisibilityHandler
                {
                    selectedObjectId: UM.ActiveTool.properties.getValue("SelectedObjectId")
                }
            }

            delegate: Row
            {
                Loader
                {
                    id: settingLoader
                    width: UM.Theme.getSize("setting").width;
                    height: UM.Theme.getSize("section").height;

                    property var definition: model
                    property var settingDefinitionsModel: addedSettingsModel
                    property var propertyProvider: provider

                    //Qt5.4.2 and earlier has a bug where this causes a crash: https://bugreports.qt.io/browse/QTBUG-35989
                    //In addition, while it works for 5.5 and higher, the ordering of the actual combo box drop down changes,
                    //causing nasty issues when selecting different options. So disable asynchronous loading of enum type completely.
                    asynchronous: model.type != "enum" && model.type != "extruder"

                    onLoaded: {
                        settingLoader.item.showRevertButton = false
                        settingLoader.item.showInheritButton = false
                        settingLoader.item.doDepthIndentation = false
                    }

                    sourceComponent:
                    {
                        switch(model.type)
                        {
                            case "int":
                                return settingTextField
                            case "float":
                                return settingTextField
                            case "enum":
                                return settingComboBox
                            case "extruder":
                                return settingExtruder
                            case "bool":
                                return settingCheckBox
                            case "str":
                                return settingTextField
                            case "category":
                                return settingCategory
                            default:
                                return settingUnknown
                        }
                    }
                }

                Button
                {
                    width: UM.Theme.getSize("setting").height;
                    height: UM.Theme.getSize("setting").height;

                    onClicked: addedSettingsModel.setVisible(model.key, false);

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
                UM.SettingPropertyProvider
                {
                    id: provider

                    containerStackId: UM.ActiveTool.properties.getValue("ContainerID")
                    key: model.key
                    watchedProperties: [ "value", "enabled", "validationState" ]
                    storeIndex: 0
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
                    listview.model.filter = {"settable_per_mesh": true, "label": "*" + text}
                }
                else
                {
                    listview.model.filter = {"settable_per_mesh": true}
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
                        "settable_per_mesh": true
                    }
                    visibilityHandler: UM.SettingPreferenceVisibilityHandler {}
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

    Component
    {
        id: settingTextField;

        Cura.SettingTextField { }
    }

    Component
    {
        id: settingComboBox;

        Cura.SettingComboBox { }
    }

    Component
    {
        id: settingExtruder;

        Cura.SettingExtruder { }
    }

    Component
    {
        id: settingCheckBox;

        Cura.SettingCheckBox { }
    }

    Component
    {
        id: settingCategory;

        Cura.SettingCategory { }
    }

    Component
    {
        id: settingUnknown;

        Cura.SettingUnknown { }
    }
}
