// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Window 2.2

import UM 1.1 as UM

Item {
    id: base;
    property int currentIndex: UM.ActiveTool.properties.SelectedIndex;
    property string printSequence: UM.ActiveTool.properties.PrintSequence;

    width: childrenRect.width;
    height: childrenRect.height;

    Column {
        id: items
        anchors.top: parent.top;
        anchors.left: parent.left;

        spacing: UM.Theme.sizes.default_margin.height;

        Label {
            width: UM.Theme.sizes.setting.width;
            wrapMode: Text.Wrap;
            text: catalog.i18nc("@label", "Per Object Settings behavior may be unexpected when 'Print sequence' is set to 'All at Once'.")
            color: UM.Theme.colors.text;
            visible: base.printSequence == "all_at_once"
        }

        UM.SettingItem {
            id: profileSelection

            width: UM.Theme.sizes.setting.width;
            height: UM.Theme.sizes.setting.height;

            name: catalog.i18nc("@label", "Object profile")
            type: "enum"
            indent: false

            style: UM.Theme.styles.setting_item;

            options: UM.ProfilesModel { addUseGlobal: true }

            value: UM.ActiveTool.properties.Model.getItem(base.currentIndex).profile

            onItemValueChanged: {
                var item = UM.ActiveTool.properties.Model.getItem(base.currentIndex);
                UM.ActiveTool.properties.Model.setObjectProfile(item.id, value)
            }
        }

        Column {
            id: customisedSettings
            spacing: UM.Theme.sizes.default_lining.height;
            width: UM.Theme.sizes.setting.width + UM.Theme.sizes.setting.height/2;

            Repeater {
                id: settings;

                model: UM.ActiveTool.properties.Model.getItem(base.currentIndex).settings

                UM.SettingItem {
                    width: UM.Theme.sizes.setting.width;
                    height: UM.Theme.sizes.setting.height;

                    name: model.label;
                    type: model.type;
                    value: model.value;
                    description: model.description;
                    unit: model.unit;
                    valid: model.valid;
                    options: model.options
                    indent: false

                    style: UM.Theme.styles.setting_item;

                    onItemValueChanged: {
                        settings.model.setSettingValue(model.key, value)
                    }

                    Button
                    {
                        anchors.left: parent.right;

                        width: UM.Theme.sizes.setting.height;
                        height: UM.Theme.sizes.setting.height;

                        onClicked: UM.ActiveTool.properties.Model.removeSettingOverride(UM.ActiveTool.properties.Model.getItem(base.currentIndex).id, model.key)

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
                                    color: UM.Theme.colors.setting_control_revert
                                    source: UM.Theme.icons.cross1
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
            anchors.right: profileSelection.right;
            height: UM.Theme.sizes.setting.height;
            visible: parseInt(UM.Preferences.getValue("cura/active_mode")) == 1

            text: catalog.i18nc("@action:button", "Add Setting");

            style: ButtonStyle
            {
                background: Rectangle
                {
                    width: control.width;
                    height: control.height;
                    border.width: UM.Theme.sizes.default_lining.width;
                    border.color: control.pressed ? UM.Theme.colors.action_button_active_border :
                                  control.hovered ? UM.Theme.colors.action_button_hovered_border : UM.Theme.colors.action_button_border
                    color: control.pressed ? UM.Theme.colors.action_button_active :
                           control.hovered ? UM.Theme.colors.action_button_hovered : UM.Theme.colors.action_button
                }
                label: Label
                {
                    text: control.text;
                    color: UM.Theme.colors.setting_control_text;
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

    UM.I18nCatalog { id: catalog; name: "uranium"; }

    UM.Dialog {
        id: settingPickDialog

        title: catalog.i18nc("@title:window", "Pick a Setting to Customize")

        TextField {
            id: filter;

            anchors {
                top: parent.top;
                left: parent.left;
                right: parent.right;
            }

            placeholderText: catalog.i18nc("@label:textbox", "Filter...");

            onTextChanged: settingCategoriesModel.filter(text);
        }

        ScrollView {
            id: view;
            anchors {
                top: filter.bottom;
                left: parent.left;
                right: parent.right;
                bottom: parent.bottom;
            }

            Column {
                width: view.width - UM.Theme.sizes.default_margin.width * 2;
                height: childrenRect.height;

                Repeater {
                    id: settingList;

                    model: UM.SettingCategoriesModel { id: settingCategoriesModel; }

                    delegate: Item {
                        id: delegateItem;

                        width: parent.width;
                        height: childrenRect.height;

                        ToolButton {
                            id: categoryHeader;
                            text: model.name;
                            checkable: true;
                            width: parent.width;
                            onCheckedChanged: settingsColumn.state != "" ? settingsColumn.state = "" : settingsColumn.state = "collapsed";

                            style: ButtonStyle {
                                background: Rectangle
                                {
                                    width: control.width;
                                    height: control.height;
                                    color: control.hovered ? palette.highlight : "transparent";
                                }
                                label: Row
                                {
                                    spacing: UM.Theme.sizes.default_margin.width;
                                    Image
                                    {
                                        anchors.verticalCenter: parent.verticalCenter;
                                        source: control.checked ? UM.Theme.icons.arrow_right : UM.Theme.icons.arrow_bottom;
                                    }
                                    Label
                                    {
                                        text: control.text;
                                        font.bold: true;
                                        color: control.hovered ? palette.highlightedText : palette.text;
                                    }
                                }
                            }
                        }

                        property variant settingsModel: model.settings;

                        visible: model.visible;

                        Column {
                            id: settingsColumn;

                            anchors.top: categoryHeader.bottom;

                            property real childrenHeight:
                            {
                                var h = 0.0;
                                for(var i in children)
                                {
                                    var item = children[i];
                                    h += children[i].height;
                                    if(item.settingVisible)
                                    {
                                        if(i > 0)
                                        {
                                            h += spacing;
                                        }
                                    }
                                }
                                return h;
                            }

                            width: childrenRect.width;
                            height: childrenHeight;
                            Repeater {
                                model: delegateItem.settingsModel;

                                delegate: ToolButton {
                                    id: button;
                                    x: model.depth * UM.Theme.sizes.default_margin.width;
                                    text: model.name;
                                    tooltip: model.description;

                                    onClicked: {
                                        var object_id = UM.ActiveTool.properties.Model.getItem(base.currentIndex).id;
                                        UM.ActiveTool.properties.Model.addSettingOverride(object_id, model.key);
                                        settingPickDialog.visible = false;
                                    }

                                    states: State {
                                        name: "filtered"
                                        when: model.filtered || !model.visible || !model.enabled
                                        PropertyChanges { target: button; height: 0; opacity: 0; }
                                    }
                                }
                            }

                            states: State {
                                name: "collapsed";

                                PropertyChanges { target: settingsColumn; opacity: 0; height: 0; }
                            }
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
