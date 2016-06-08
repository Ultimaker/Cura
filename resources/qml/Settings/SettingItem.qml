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

    property var showRevertButton: true
    property var showInheritButton: true
    property var doDepthIndentation: true

    // Create properties to put property provider stuff in (bindings break in qt 5.5.1 otherwise)
    property var state: propertyProvider.properties.state
    property var stackLevel: propertyProvider.stackLevels[0]

    signal contextMenuRequested()
    signal showTooltip(string text);
    signal hideTooltip();

    property string tooltipText:
    {
            var affects = settingDefinitionsModel.getRequiredBy(definition.key, "value")
            var affected_by = settingDefinitionsModel.getRequires(definition.key, "value")

            var affected_by_list = ""
            for(var i in affected_by)
            {
                affected_by_list += "<li>%1</li>\n".arg(affected_by[i].label)
            }

            var affects_list = ""
            for(var i in affects)
            {
                affects_list += "<li>%1</li>\n".arg(affects[i].label)
            }

            var tooltip = "<b>%1</b>\n<p>%2</p>".arg(definition.label).arg(definition.description)

            if(affects_list != "")
            {
                tooltip += "<br/><b>%1</b>\n<ul>\n%2</ul>".arg(catalog.i18nc("@label", "Affects")).arg(affects_list)
            }

            if(affected_by_list != "")
            {
                tooltip += "<br/><b>%1</b>\n<ul>\n%2</ul>".arg(catalog.i18nc("@label", "Affected By")).arg(affected_by_list)
            }

            return tooltip
    }

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

            onTriggered:
            {
                base.showTooltip(base.tooltipText);
            }
        }

        Label
        {
            id: label;

            anchors.left: parent.left;
            anchors.leftMargin: doDepthIndentation ? (UM.Theme.getSize("section_icon_column").width + 5) + ((definition.depth - 1) * UM.Theme.getSize("setting_control_depth_margin").width) : 0
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

                visible: base.stackLevel == 0 && base.showRevertButton

                height: parent.height;
                width: height;

                backgroundColor: UM.Theme.getColor("setting_control");
                hoverBackgroundColor: UM.Theme.getColor("setting_control_highlight")
                color: UM.Theme.getColor("setting_control_button")
                hoverColor: UM.Theme.getColor("setting_control_button_hover")

                iconSource: UM.Theme.getIcon("reset")

                onClicked: {
                    revertButton.focus = true
                    propertyProvider.removeFromContainer(0)
                }

                onEntered: { hoverTimer.stop(); base.showTooltip(catalog.i18nc("@label", "This setting has a value that is different from the profile.\n\nClick to restore the value of the profile.")) }
                onExited: base.showTooltip(base.tooltipText);
            }

            UM.SimpleButton
            {
                // This button shows when the setting has an inherited function, but is overriden by profile.
                id: inheritButton;

                //visible: has_profile_value && base.has_inherit_function && base.is_enabled
                visible: base.state == "InstanceState.User" && base.stackLevel > 0 && base.showInheritButton

                height: parent.height;
                width: height;

                onClicked: {
                    focus = true;
                    // Get the deepest entry of this setting that we can find. TODO: This is a bit naive, in some cases
                    // there might be multiple profiles saying something about the same setting. There is no strategy
                    // how to handle this as of yet.
                    var last_entry = propertyProvider.stackLevels.slice(-1)[0]
                    // Put that entry into the "top" instance container.
                    // This ensures that the value in any of the deeper containers need not be removed, which is
                    // needed for the reset button (which deletes the top value) to correctly go back to profile
                    // defaults.
                    propertyProvider.setPropertyValue("value", propertyProvider.getPropertyValue("value", last_entry))
                }

                backgroundColor: UM.Theme.getColor("setting_control");
                hoverBackgroundColor: UM.Theme.getColor("setting_control_highlight")
                color: UM.Theme.getColor("setting_control_button")
                hoverColor: UM.Theme.getColor("setting_control_button_hover")

                iconSource: UM.Theme.getIcon("notice");

                onEntered: { hoverTimer.stop(); base.showTooltip(catalog.i18nc("@label", "This setting is normally calculated, but it currently has an absolute value set.\n\nClick to restore the calculated value.")) }
                onExited: base.showTooltip(base.tooltipText);
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
