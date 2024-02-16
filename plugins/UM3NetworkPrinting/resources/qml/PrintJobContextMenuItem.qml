// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.5 as UM

Button
{
    background: Rectangle
    {
        opacity: parent.down || parent.hovered ? 1 : 0
        color: UM.Theme.getColor("monitor_context_menu_hover")
    }
    contentItem: UM.Label
    {
        color: enabled ? UM.Theme.getColor("text") : UM.Theme.getColor("monitor_text_disabled")
        text: parent.text
        horizontalAlignment: Text.AlignLeft
    }
    height: visible ? 39 * screenScaleFactor : 0 // TODO: Theme!
    hoverEnabled: true
    width: parent.width
}
