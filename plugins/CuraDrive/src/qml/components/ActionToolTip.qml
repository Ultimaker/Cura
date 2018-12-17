// Copyright (c) 2018 Ultimaker B.V.
import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

import UM 1.1 as UM

ToolTip
{
    id: tooltip
    visible: parent.hovered
    opacity: 0.9
    delay: 500

    background: Rectangle
    {
        color: UM.Theme.getColor("main_background")
        border.color: UM.Theme.getColor("primary")
        border.width: 1 * screenScaleFactor
    }

    contentItem: Label
    {
        text: tooltip.text
        color: UM.Theme.getColor("text")
        font: UM.Theme.getFont("default")
        renderType: Text.NativeRendering
    }
}
