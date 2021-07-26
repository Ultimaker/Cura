// Copyright (c) 2020 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// Checkbox with Cura styling.
//
CheckBox
{
    id: control

    hoverEnabled: true

    indicator: Rectangle
    {
        width: control.height
        height: control.height

        color:
        {
            if (!control.enabled)
            {
                return UM.Theme.getColor("setting_control_disabled")
            }
            if (control.hovered || control.activeFocus)
            {
                return UM.Theme.getColor("setting_control_highlight")
            }
            return UM.Theme.getColor("setting_control")
        }

        radius: UM.Theme.getSize("setting_control_radius").width
        border.width: UM.Theme.getSize("default_lining").width
        border.color:
        {
            if (!enabled)
            {
                return UM.Theme.getColor("setting_control_disabled_border")
            }
            if (control.hovered || control.activeFocus)
            {
                return UM.Theme.getColor("setting_control_border_highlight")
            }
            return UM.Theme.getColor("setting_control_border")
        }

        UM.RecolorImage
        {
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter
            width: Math.round(parent.width / 2.5)
            height: Math.round(parent.height / 2.5)
            sourceSize.height: width
            color: !enabled ? UM.Theme.getColor("setting_control_disabled_text") : UM.Theme.getColor("setting_control_text")
            source: UM.Theme.getIcon("Check")
            opacity: control.checked ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: 100; } }
        }
    }

    contentItem: Label
    {
        id: textLabel
        leftPadding: control.indicator.width + control.spacing
        text: control.text
        font: control.font
        color: UM.Theme.getColor("text")
        renderType: Text.NativeRendering
        verticalAlignment: Text.AlignVCenter
    }
}
