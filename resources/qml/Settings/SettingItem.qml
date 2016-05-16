// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.1 as UM

import "."

Item {
    id: base;

    height: UM.Theme.getSize("section").height;

    property alias contents: controlContainer.children;
    property alias hovered: mouse.containsMouse

    signal contextMenuRequested()
    signal showTooltip(string text);
    signal hideTooltip();

    MouseArea 
    {
        id: mouse;

        anchors.fill: parent;

        acceptedButtons: Qt.RightButton;
        hoverEnabled: true;

        onClicked: base.contextMenuRequested();

        onEntered: {
            hoverTimer.start();
        }

        onExited: {
            if(controlContainer.item && controlContainer.item.hovered) {
                return;
            }
            hoverTimer.stop();
            base.hideTooltip();
        }

        Timer {
            id: hoverTimer;
            interval: 500;
            repeat: false;

            onTriggered: base.showTooltip(definition.description);
        }

        Label
        {
            id: label;

            anchors.left: parent.left;
            anchors.leftMargin: (UM.Theme.getSize("section_icon_column").width + 5) + ((definition.depth - 1) * UM.Theme.getSize("setting_control_depth_margin").width)
            anchors.right: settingControls.left;
            anchors.verticalCenter: parent.verticalCenter

            height: UM.Theme.getSize("section").height;
            verticalAlignment: Text.AlignVCenter;

            text: definition.label
            elide: Text.ElideMiddle;

            color: UM.Theme.getColor("setting_control_text");
            font: UM.Theme.getFont("default");
        }

        Row
        {
            id: settingControls

            height: parent.height / 2
            spacing: UM.Theme.getSize("default_margin").width / 2

            anchors {
                right: controlContainer.left
                rightMargin: UM.Theme.getSize("default_margin").width / 2
                verticalCenter: parent.verticalCenter
            }

            UM.SimpleButton
            {
                id: revertButton;

                visible: propertyProvider.properties.state == "InstanceState.User"

                height: parent.height;
                width: height;

                backgroundColor: UM.Theme.getColor("setting_control");
                hoverBackgroundColor: UM.Theme.getColor("setting_control_highlight")
                color: UM.Theme.getColor("setting_control_button")
                hoverColor: UM.Theme.getColor("setting_control_button_hover")

                iconSource: UM.Theme.getIcon("reset")

                onClicked: {
                    base.resetRequested()
                    controlContainer.notifyReset();
                }

                onEntered: base.showTooltip(catalog.i18nc("@label", "This setting has a value that is different from the profile.\n\nClick to restore the value of the profile."))
                onExited: base.showTooltip(definition.description);
            }

            UM.SimpleButton
            {
                // This button shows when the setting has an inherited function, but is overriden by profile.
                id: inheritButton;

                //visible: has_profile_value && base.has_inherit_function && base.is_enabled
                visible: propertyProvider.properties.state == "InstanceState.User"

                height: parent.height;
                width: height;

                onClicked: {
                    base.resetToDefaultRequested();
                    controlContainer.notifyReset();
                }

                backgroundColor: UM.Theme.getColor("setting_control");
                hoverBackgroundColor: UM.Theme.getColor("setting_control_highlight")
                color: UM.Theme.getColor("setting_control_button")
                hoverColor: UM.Theme.getColor("setting_control_button_hover")

                iconSource: UM.Theme.getIcon("notice");

                onEntered: base.showTooltip(catalog.i18nc("@label", "This setting is normally calculated, but it currently has an absolute value set.\n\nClick to restore the calculated value."))
                onExited: base.showTooltip(definition.description);
            }

        }

        Item
        {
            id: controlContainer;

            anchors.right: parent.right;
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: parent.verticalCenter;
            width: UM.Theme.getSize("setting_control").width;
            height: UM.Theme.getSize("setting_control").height
        }
    }

    UM.I18nCatalog { id: catalog; name: "cura" }
}
