// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 2.1

import Cura 1.0 as Cura
import UM 1.5 as UM

Button
{
    id: base

    property alias tooltip: tooltip.text
    property alias iconSource: icon.source;

    Cura.ToolTip
    {
        id: tooltip
        visible: base.hovered
        targetPoint: Qt.point(parent.x, Math.round(parent.y + parent.height / 2))
    }


    background: Item
    {
        implicitWidth: UM.Theme.getSize("button").width
        implicitHeight: UM.Theme.getSize("button").height

        Rectangle
        {
            id: buttonFace

            anchors.fill: parent
            property bool down: base.pressed || (base.checkable && base.checked)

            color:
            {
                if(base.customColor !== undefined && base.customColor !== null)
                {
                    return base.customColor
                }
                else if(base.checkable && base.checked && base.hovered)
                {
                    return UM.Theme.getColor("toolbar_button_active_hover")
                }
                else if(base.pressed || (base.checkable && base.checked))
                {
                    return UM.Theme.getColor("toolbar_button_active")
                }
                else if(base.hovered)
                {
                    return UM.Theme.getColor("toolbar_button_hover")
                }
                return UM.Theme.getColor("toolbar_background")
            }
            Behavior on color { ColorAnimation { duration: 50 } }

            border.width: (base.hasOwnProperty("needBorder") && base.needBorder) ? UM.Theme.getSize("default_lining").width : 0
            border.color: base.checked ? UM.Theme.getColor("icon") : UM.Theme.getColor("lining")
        }
    }

    contentItem: Item
    {
        UM.RecolorImage
        {
            id: icon

            anchors.centerIn: parent
            opacity: base.enabled ? 1.0 : 0.2
            width: UM.Theme.getSize("medium_button_icon").width
            height: UM.Theme.getSize("medium_button_icon").height
            color: UM.Theme.getColor("icon")

            sourceSize: UM.Theme.getSize("medium_button_icon")
        }
    }
}