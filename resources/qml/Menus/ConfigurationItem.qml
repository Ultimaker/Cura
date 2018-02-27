// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.2 as UM
import Cura 1.0 as Cura

ItemDelegate
{
    contentItem: Label
    {
        text: model.name
        renderType: Text.NativeRendering
        color: UM.Theme.getColor("setting_control_text")
        font: UM.Theme.getFont("default")
        elide: Text.ElideRight
        verticalAlignment: Text.AlignVCenter
        rightPadding: swatch.width + UM.Theme.getSize("setting_unit_margin").width

        background: Rectangle
        {
            id: swatch
            height: Math.round(UM.Theme.getSize("setting_control").height / 2)
            width: height

            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.margins: Math.round(UM.Theme.getSize("default_margin").width / 4)

            border.width: UM.Theme.getSize("default_lining").width
            border.color: enabled ? UM.Theme.getColor("setting_control_border") : UM.Theme.getColor("setting_control_disabled_border")
            radius: Math.round(width / 2)

            color: control.model.getItem(index).color
        }
    }

    background: Rectangle
    {
        color: parent.highlighted ? UM.Theme.getColor("setting_control_highlight") : "transparent"
        border.color: parent.highlighted ? UM.Theme.getColor("setting_control_border_highlight") : "transparent"
    }
}