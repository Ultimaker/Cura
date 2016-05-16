// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.2 as UM

SettingItem
{
    id: base

    contents: MouseArea
    {
        id: control
        anchors.fill: parent

        property bool checked:
        {
            switch(propertyProvider.properties.value)
            {
                case "True":
                    return true
                case "False":
                    return false
                default:
                    return propertyProvider.properties.value
            }
        }

        onClicked: propertyProvider.setPropertyValue("value", !checked)

        Rectangle
        {
            anchors
            {
                top: parent.top
                bottom: parent.bottom
                left: parent.left
            }
            width: height

            color:
            {
                if (!enabled)
                {
                    return UM.Theme.getColor("setting_control_disabled")
                }
                if(control.containsMouse || control.activeFocus)
                {
                    return UM.Theme.getColor("setting_control_highlight")
                }
                else
                {
                    return UM.Theme.getColor("setting_control")
                }
            }

            border.width: UM.Theme.getSize("default_lining").width
            border.color: !enabled ? UM.Theme.getColor("setting_control_disabled_border") : control.containsMouse ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_border")

            UM.RecolorImage {
                anchors.verticalCenter: parent.verticalCenter
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width/2.5
                height: parent.height/2.5
                sourceSize.width: width
                sourceSize.height: width
                color: !enabled ? UM.Theme.getColor("setting_control_disabled_text") : UM.Theme.getColor("setting_control_text");
                source: UM.Theme.getIcon("check")
                opacity: control.checked ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: 100; } }
            }
        }
    }
}
