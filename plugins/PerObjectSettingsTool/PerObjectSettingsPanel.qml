// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Window 2.2

import UM 1.1 as UM

Item {
    id: base;

    width: 0;
    height: 0;

    property variant position: mapToItem(null, 0, 0)
    property var settingOverrideModel: UM.ActiveTool.properties.Model.getItem(base.currentIndex).settings

    property real viewportWidth: UM.Application.mainWindow.width * UM.Application.mainWindow.viewportRect.width;
    property real viewportHeight: UM.Application.mainWindow.height * UM.Application.mainWindow.viewportRect.height;

    property int currentIndex;

    onSettingOverrideModelChanged:{
        console.log(UM.ActiveTool.properties.Model.getItem(base.currentIndex).settings)
//         UM.ActiveTool.properties.Model.getItem(base.currentIndex).settings.refresh()
//         if (UM.ActiveTool.properties.Model.getItem(base.currentIndex).settings == undefined){
//
//         }
    }

    Rectangle {
        id: settingsPanel;

        z: 3;

        width: UM.Theme.sizes.per_object_settings_panel.width;
        height: items.height + UM.Theme.sizes.default_margin.height * 2;

        opacity: 0;
        Behavior on opacity { NumberAnimation { } }

        border.width: UM.Theme.sizes.per_object_settings_panel_border.width;
        border.color: UM.Theme.colors.per_object_settings_panel_border;

        color: UM.Theme.colors.per_object_settings_panel_background;

        DropArea {
            anchors.fill: parent;
        }
        Button {
            id: closeButton;
            width: UM.Theme.sizes.message_close.width;
            height: UM.Theme.sizes.message_close.height;
            anchors {
                right: parent.right;
                rightMargin: UM.Theme.sizes.default_margin.width / 2;
                top: parent.top;
                topMargin: UM.Theme.sizes.default_margin.width / 2;
            }
            UM.RecolorImage {
                anchors.fill: parent;
                sourceSize.width: width
                sourceSize.height: width
                color: UM.Theme.colors.message_dismiss
                source: UM.Theme.icons.cross2;
            }

            onClicked: settingsPanel.opacity = 0

            style: ButtonStyle {
                background: Rectangle {
                    color: UM.Theme.colors.message_background
                }
            }
        }

        Column {
            id: items
            anchors.top: parent.top;
            anchors.topMargin: UM.Theme.sizes.default_margin.height;

            spacing: UM.Theme.sizes.default_lining.height;

            UM.SettingItem {
                id: profileSelection

                x: UM.Theme.sizes.per_object_settings_panel_border.width + 1

                width: UM.Theme.sizes.setting.width;
                height: UM.Theme.sizes.setting.height;

                name: catalog.i18nc("@label", "Profile")
                type: "enum"

                style: UM.Theme.styles.setting_item;

                options: UM.ProfilesModel { addUseGlobal: true }

                value: UM.ActiveTool.properties.Model.getItem(base.currentIndex).profile

                onItemValueChanged: {
                    var item = UM.ActiveTool.properties.Model.getItem(base.currentIndex);
                    UM.ActiveTool.properties.Model.setObjectProfile(item.id, value)
                }
            }

            Repeater {
                id: settings;

                model: base.settingOverrideModel

                UM.SettingItem {
                    width: UM.Theme.sizes.setting.width;
                    height: UM.Theme.sizes.setting.height;
                    x: UM.Theme.sizes.per_object_settings_panel_border.width + 1
                    name: model.label;
                    visible: !model.global_only;
                    type: model.type;
                    value: model.value;
                    description: model.description;
                    unit: model.unit;
                    valid: model.valid;
                    options: model.options;

                    style: UM.Theme.styles.setting_item;

                    onItemValueChanged: {
                        settings.model.setSettingValue(model.key, value)
                         base.settingOverrideModel = UM.ActiveTool.properties.Model.getItem(base.currentIndex).settings
                    }

                    Button
                    {
                        anchors.left: parent.horizontalCenter;
                        anchors.leftMargin: UM.Theme.sizes.default_margin.width;

                        width: UM.Theme.sizes.setting.height;
                        height: UM.Theme.sizes.setting.height;

                        opacity: parent.hovered || hovered ? 1 : 0;
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

            Item
            {
                height: UM.Theme.sizes.default_margin.height / 2
                width: parent.width
            }

            Button
            {
                id: customise_settings_button;
                anchors.right: profileSelection.right;
                visible: parseInt(UM.Preferences.getValue("cura/active_mode")) == 1

                text: catalog.i18nc("@action:button", "Customize Settings");

                style: ButtonStyle
                {
                    background: Rectangle
                    {
                        width: control.width;
                        height: control.height;
                        color: control.hovered ? UM.Theme.colors.load_save_button_hover : UM.Theme.colors.load_save_button;
                    }
                    label: Label
                    {
                        text: control.text;
                        color: UM.Theme.colors.load_save_button_text;
                    }
                }

                onClicked: {
                    settingPickDialog.settingCategoriesModel.reload()
                    settingPickDialog.visible = true;
                }

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
    }

    Repeater {
        model: UM.ActiveTool.properties.Model;
        delegate: Button {
            x: ((model.x + 1.0) / 2.0) * base.viewportWidth - base.position.x - width / 2
            y: -((model.y + 1.0) / 2.0) * base.viewportHeight + (base.viewportHeight - base.position.y) + height / 2

            width: UM.Theme.sizes.per_object_settings_button.width
            height: UM.Theme.sizes.per_object_settings_button.height

            tooltip: catalog.i18nc("@info:tooltip", "Customise settings for this object");

            checkable: true;
            onClicked: {
                if(settingsPanel.opacity < 0.5) //Per-object panel is not currently displayed.
                {
                    base.currentIndex = index;

                    settingsPanel.anchors.left = right;
                    settingsPanel.anchors.top = top;

                    settingsPanel.opacity = 1;
                }
                else //Per-object panel is already displayed. Deactivate it (same behaviour as the close button).
                {
                    settingsPanel.opacity = 0;
                }
            }

            style: ButtonStyle
            {
                background: Rectangle
                {
                    width: control.width;
                    height: control.height;

                    color: control.hovered ? UM.Theme.colors.button_active : UM.Theme.colors.button_hover;
                }
                label: Image {
                    width: control.width;
                    height: control.height;
                    sourceSize.width: width;
                    sourceSize.height: height;
                    source: UM.Theme.icons.plus;
                }
            }
        }
    }

    PerObjectSettingsDialog{
        id: settingPickDialog
        settingCategoriesModel: UM.SettingCategoriesModel { id: settingCategoriesModel; }

        onVisibilityChanged:{
            if (settingPickDialog.visibility == false){
                base.settingOverrideModel = UM.ActiveTool.properties.Model.getItem(base.currentIndex).settings
            }
        }
    }


    SystemPalette { id: palette; }
}
