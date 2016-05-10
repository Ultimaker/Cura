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

    MouseArea
    {
        id: control

        property bool checked:
        {
            if(value == "True")
            {
                return true;
            }
            else if(value == "False")
            {
                return false;
            }
            else
            {
                return value;
            }
        }

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
                    return base.style.controlDisabledColor
                }
                if(base.containsMouse || base.activeFocus)
                {
                    return base.style.controlHighlightColor
                }
                else
                {
                    return base.style.controlColor
                }
            }
            border.width: base.style.controlBorderWidth;
            border.color: !enabled ? base.style.controlDisabledBorderColor : control.containsMouse ? base.style.controlBorderHighlightColor : base.style.controlBorderColor;

            UM.RecolorImage {
                anchors.verticalCenter: parent.verticalCenter
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width/2.5
                height: parent.height/2.5
                sourceSize.width: width
                sourceSize.height: width
                color: !enabled ? base.style.controlDisabledTextColor : base.style.controlTextColor;
                source: UM.Theme.getIcon("check")
                opacity: control.checked
                Behavior on opacity { NumberAnimation { duration: 100; } }
            }
        }
    }
}
