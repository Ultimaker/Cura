// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1

import UM 1.3 as UM

CheckBox
{
    id: checkbox
    hoverEnabled: true

    property alias tooltip: tooltip.text

    indicator: Rectangle
    {
        implicitWidth: UM.Theme.getSize("checkbox").width
        implicitHeight: UM.Theme.getSize("checkbox").height
        x: 0
        anchors.verticalCenter: parent.verticalCenter
        color: UM.Theme.getColor("main_background")
        radius: UM.Theme.getSize("checkbox_radius").width
        border.width: UM.Theme.getSize("default_lining").width
        border.color: checkbox.hovered ? UM.Theme.getColor("checkbox_border_hover") : UM.Theme.getColor("checkbox_border")

        UM.RecolorImage
        {
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter
            width: Math.round(parent.width / 2.5)
            height: Math.round(parent.height / 2.5)
            sourceSize.height: width
            color: UM.Theme.getColor("checkbox_mark")
            source: UM.Theme.getIcon("Check")
            opacity: checkbox.checked
            Behavior on opacity { NumberAnimation { duration: 100; } }
        }
    }

    contentItem: Label
    {
        anchors
        {
            left: checkbox.indicator.right
            leftMargin: UM.Theme.getSize("narrow_margin").width
        }
        text: checkbox.text
        color: UM.Theme.getColor("checkbox_text")
        font: UM.Theme.getFont("default")
        renderType: Text.NativeRendering
        elide: Text.ElideRight
        verticalAlignment: Text.AlignVCenter
    }

    ToolTip
    {
        id: tooltip
        text: ""
        delay: 500
        visible: text != "" && checkbox.hovered
    }
}
