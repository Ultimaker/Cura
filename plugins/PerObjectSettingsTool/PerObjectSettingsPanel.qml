// Copyright (c) 2016 Ultimaker B.V.
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

        spacing: UM.Theme.getSize("default_margin").height

        Row
        {
            spacing: UM.Theme.getSize("default_margin").width
            Label
            {
                text: catalog.i18nc("@label", "Print model with")
                anchors.verticalCenter: extruderSelector.verticalCenter

                color: UM.Theme.getColor("setting_control_text")
                font: UM.Theme.getFont("default")
                visible: extruderSelector.visible
            }
            ComboBox
            {
                id: extruderSelector

                model: Cura.ExtrudersModel
                {
                    id: extruders_model
                    onRowsInserted: extruderSelector.visible = extruders_model.rowCount() > 1
                    onModelReset:   extruderSelector.visible = extruders_model.rowCount() > 1
                    onModelChanged: extruderSelector.color = extruders_model.getItem(extruderSelector.currentIndex).color
                }
                property string color: extruders_model.getItem(extruderSelector.currentIndex).color
                visible: extruders_model.rowCount() > 1
                textRole: "name"
                width: UM.Theme.getSize("setting_control").width
                height: UM.Theme.getSize("section").height
                MouseArea
                {
                    anchors.fill: parent
                    acceptedButtons: Qt.NoButton
                    onWheel: wheel.accepted = true;
                }

                style: ComboBoxStyle
                {
                    background: Rectangle
                    {
                        color:
                        {
                            if(extruderSelector.hovered || base.activeFocus)
                            {
                                return UM.Theme.getColor("setting_control_highlight");
                            }
                            else
                            {
                                return UM.Theme.getColor("setting_control");
                            }
                        }
                        border.width: UM.Theme.getSize("default_lining").width
                        border.color: UM.Theme.getColor("setting_control_border")
                    }
                    label: Item
                    {
                        Rectangle
                        {
                            id: swatch
                            height: UM.Theme.getSize("setting_control").height / 2
                            width: height
                            anchors.left: parent.left
                            anchors.leftMargin: UM.Theme.getSize("default_lining").width
                            anchors.verticalCenter: parent.verticalCenter

                            color: extruderSelector.color
                            border.width: UM.Theme.getSize("default_lining").width
                            border.color: !enabled ? UM.Theme.getColor("setting_control_disabled_border") : UM.Theme.getColor("setting_control_border")
                        }
                        Label
                        {
                            anchors.left: swatch.right
                            anchors.leftMargin: UM.Theme.getSize("default_lining").width
                            anchors.right: downArrow.left
                            anchors.rightMargin: UM.Theme.getSize("default_lining").width
                            anchors.verticalCenter: parent.verticalCenter

                            text: extruderSelector.currentText
                            font: UM.Theme.getFont("default")
                            color: !enabled ? UM.Theme.getColor("setting_control_disabled_text") : UM.Theme.getColor("setting_control_text")

                            elide: Text.ElideRight
                            verticalAlignment: Text.AlignVCenter
                        }

                        UM.RecolorImage
                        {
                            id: downArrow
                            anchors.right: parent.right
                            anchors.rightMargin: UM.Theme.getSize("default_lining").width * 2
                            anchors.verticalCenter: parent.verticalCenter

                            source: UM.Theme.getIcon("arrow_bottom")
                            width: UM.Theme.getSize("standard_arrow").width
                            height: UM.Theme.getSize("standard_arrow").height
                            sourceSize.width: width + 5
                            sourceSize.height: width + 5

                            color: UM.Theme.getColor("setting_control_text")
                        }
                    }
                }

                onActivated:
                {
                    UM.ActiveTool.setProperty("SelectedActiveExtruder", extruders_model.getItem(index).id);
                    extruderSelector.color = extruders_model.getItem(index).color;
                }
                onModelChanged: updateCurrentIndex();

                function updateCurrentIndex()
                {
                    for(var i = 0; i < extruders_model.rowCount(); ++i)
                    {
                        if(extruders_model.getItem(i).id == UM.ActiveTool.properties.getValue("SelectedActiveExtruder"))
                        {
                            extruderSelector.currentIndex = i;
                            extruderSelector.color = extruders_model.getItem(i).color;
                            return;
                        }
                    }
                    extruderSelector.currentIndex = -1;
                }
            }
        }

        Column
        {
            spacing: UM.Theme.getSize("default_lining").height
            // This is to ensure that the panel is first increasing in size up to 200 and then shows a scrollbar.
            // It kinda looks ugly otherwise (big panel, no content on it)
            height: contents.count * UM.Theme.getSize("section").height < 200 ? contents.count * UM.Theme.getSize("section").height : 200
            ScrollView
            {
                height: parent.height
                width: UM.Theme.getSize("setting").width + UM.Theme.getSize("setting").height
                style: UM.Theme.styles.scrollview
                ListView
                {
                    id: contents

                    model: UM.SettingDefinitionsModel
                    {
                        id: addedSettingsModel;
                        containerId: Cura.MachineManager.activeDefinitionId
                        expanded: [ "*" ]

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
                            width: UM.Theme.getSize("setting").width
                            height: UM.Theme.getSize("section").height

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
                                settingLoader.item.showLinkedSettingIcon = false
                                settingLoader.item.doDepthIndentation = false
                                settingLoader.item.doQualityUserSettingEmphasis = false
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
                            width: UM.Theme.getSize("setting").height / 2;
                            height: UM.Theme.getSize("setting").height;

                            onClicked: addedSettingsModel.setVisible(model.key, false);

                            style: ButtonStyle
                            {
                                background: Item
                                {
                                    UM.RecolorImage
                                    {
                                        anchors.verticalCenter: parent.verticalCenter
                                        width: parent.width
                                        height: parent.height / 2
                                        sourceSize.width: width
                                        sourceSize.height: width
                                        color: control.hovered ? UM.Theme.getColor("setting_control_button_hover") : UM.Theme.getColor("setting_control_button")
                                        source: UM.Theme.getIcon("minus")
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
                            removeUnusedValue: false
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

            text: catalog.i18nc("@action:button", "Select settings");

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

        title: catalog.i18nc("@title:window", "Select Settings to Customize for this model")
        width: screenScaleFactor * 360;

        property string labelFilter: ""

        onVisibilityChanged:
        {
            // force updating the model to sync it with addedSettingsModel
            if(visible)
            {
                listview.model.forceUpdate()
            }
        }

        TextField {
            id: filter

            anchors {
                top: parent.top
                left: parent.left
                right: toggleShowAll.left
                rightMargin: UM.Theme.getSize("default_margin").width
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

        CheckBox
        {
            id: toggleShowAll

            anchors {
                top: parent.top
                right: parent.right
            }

            text: catalog.i18nc("@label:checkbox", "Show all")
            checked: listview.model.showAll
            onClicked:
            {
                listview.model.showAll = checked;
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
                    expanded: [ "*" ]
                    exclude: [ "machine_settings" ]
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
                text: catalog.i18nc("@action:button", "Close");
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
