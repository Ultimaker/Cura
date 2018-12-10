// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.0 as UM

ToolTip
{
    // This property indicates when the tooltip has to show, for instance when a button is hovered
    property bool show: false

    property alias tooltipText: tooltip.text
    property var targetPoint: Qt.point(0, 0)

    id: tooltip
    text: ""
    delay: 500
    visible: text != "" && show
    font: UM.Theme.getFont("default")

    background: UM.PointingRectangle
    {
        id: backgroundRect
        color: UM.Theme.getColor("tooltip")

        target: Qt.point(targetPoint.x - tooltip.x, targetPoint.y - tooltip.y)

        arrowSize: UM.Theme.getSize("default_arrow").width
    }

    contentItem: Label
    {
        id: label
        text: tooltip.text
        font: tooltip.font
        wrapMode: Text.Wrap
        textFormat: Text.RichText
        color: UM.Theme.getColor("tooltip_text")
        renderType: Text.NativeRendering
    }
}