// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Controls 2.0
import UM 1.3 as UM
import Cura 1.0 as Cura

Button
{
    id: base
    background: Rectangle
    {
        color: enabled ? UM.Theme.getColor("viewport_background") : "transparent"
        height: base.height
        opacity: base.down || base.hovered ? 1 : 0
        radius: Math.round(0.5 * width)
        width: base.width
    }
    contentItem: Label {
        color: enabled ? UM.Theme.getColor("monitor_text_primary") : UM.Theme.getColor("monitor_text_disabled")
        font.pixelSize: 32 * screenScaleFactor
        horizontalAlignment: Text.AlignHCenter
        text: base.text
        verticalAlignment: Text.AlignVCenter
    }
    height: width
    hoverEnabled: enabled
    text: "\u22EE" //Unicode Three stacked points.
    width: 36 * screenScaleFactor // TODO: Theme!
}