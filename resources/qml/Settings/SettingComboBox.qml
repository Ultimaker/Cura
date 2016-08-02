// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.1 as UM

SettingItem
{
    id: base

    contents: ComboBox
    {
        id: control

        model: definition.options
        textRole: "value";

        anchors.fill: parent

        MouseArea
        {
            anchors.fill: parent;
            acceptedButtons: Qt.NoButton;
            onWheel: wheel.accepted = true;
        }

        style: ComboBoxStyle
        {
            background: Rectangle
            {
                color:
                {
                    if (!enabled)
                    {
                        return UM.Theme.getColor("setting_control_disabled")
                    }
                    if(control.hovered || base.activeFocus)
                    {
                        return UM.Theme.getColor("setting_control_highlight")
                    }
                    else
                    {
                        return UM.Theme.getColor("setting_control")
                    }
                }
                border.width: UM.Theme.getSize("default_lining").width;
                border.color: !enabled ? UM.Theme.getColor("setting_control_disabled_border") : control.hovered ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_border");
            }
            label: Item
            {
                Label
                {
                    anchors.left: parent.left;
                    anchors.leftMargin: UM.Theme.getSize("default_lining").width
                    anchors.right: downArrow.left;
                    anchors.rightMargin: UM.Theme.getSize("default_lining").width;
                    anchors.verticalCenter: parent.verticalCenter;

                    text: control.currentText;
                    font: UM.Theme.getFont("default");
                    color: !enabled ? UM.Theme.getColor("setting_control_disabled_text") : UM.Theme.getColor("setting_control_text");

                    elide: Text.ElideRight;
                    verticalAlignment: Text.AlignVCenter;
                }

                UM.RecolorImage
                {
                    id: downArrow
                    anchors.right: parent.right;
                    anchors.rightMargin: UM.Theme.getSize("default_lining").width * 2;
                    anchors.verticalCenter: parent.verticalCenter;

                    source: UM.Theme.getIcon("arrow_bottom")
                    width: UM.Theme.getSize("standard_arrow").width
                    height: UM.Theme.getSize("standard_arrow").height
                    sourceSize.width: width + 5
                    sourceSize.height: width + 5

                    color: UM.Theme.getColor("setting_control_text");

                }
            }
        }

        onActivated: { forceActiveFocus(); propertyProvider.setPropertyValue("value", definition.options[index].key) }
        onModelChanged: updateCurrentIndex();

        Connections
        {
            target: propertyProvider
            onPropertiesChanged: control.updateCurrentIndex()
        }

        function updateCurrentIndex() {
            for(var i = 0; i < definition.options.length; ++i) {
                if(definition.options[i].key == propertyProvider.properties.value) {
                    currentIndex = i;
                    return;
                }
            }

            currentIndex = -1;
        }
    }
}
