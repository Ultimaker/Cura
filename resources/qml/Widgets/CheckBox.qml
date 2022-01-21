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
        height: UM.Theme.getSize("checkbox").height
        width: UM.Theme.getSize("checkbox").width

        anchors.verticalCenter: parent.verticalCenter

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

        radius: UM.Theme.getSize("checkbox_radius").width
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

            height:
            {
                switch(control.checkState)
                {
                    case Qt.Checked: return UM.Theme.getSize("checkbox_mark").height
                    case Qt.PartiallyChecked: return UM.Theme.getSize("checkbox_square").height
                    default: UM.Theme.getSize("checkbox_mark").height
                }
            }
            width: height
            sourceSize.height: height

            color:
            {
                switch(control.checkState)
                {
                    case Qt.Checked: return !enabled ? UM.Theme.getColor("setting_control_disabled_text") : UM.Theme.getColor("checkbox_mark")
                    case Qt.PartiallyChecked: return !enabled ? UM.Theme.getColor("setting_control_disabled_text") : UM.Theme.getColor("checkbox_square")
                    default: return !enabled ? UM.Theme.getColor("setting_control_disabled_text") : UM.Theme.getColor("checkbox_mark")
                }
            }
            source:
            {
                switch (control.checkState)
                {
                    case Qt.Checked: return UM.Theme.getIcon("EmptyCheck", "low")
                    case Qt.PartiallyChecked: return UM.Theme.getIcon("CheckBoxFill", "low")
                    default: return UM.Theme.getIcon("EmptyCheck", "low")
                }
            }
            opacity:
            {
                switch (control.checkState)
                {
                    case Qt.Checked: return 1;
                    case Qt.PartiallyChecked: return 1;
                    default: 0;
                }
            }
            Behavior on opacity { NumberAnimation { duration: 100; } }
        }
    }

    contentItem: Label
    {
        id: textLabel
        anchors.left: control.indicator.right
        leftPadding: UM.Theme.getSize("checkbox_label_padding").width
        text: control.text
        font: control.font
        color: UM.Theme.getColor("text")
        renderType: Text.NativeRendering
        verticalAlignment: Text.AlignVCenter
    }
}
